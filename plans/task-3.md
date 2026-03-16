# План реализации Task 3: The System Agent

## Обзор

В этом задании мы добавляем инструмент `query_api` к агенту из Task 2, чтобы он мог querying live backend API. Агент сможет отвечать на два новых типа вопросов:

- Статические факты о системе (фреймворк, порты, status codes)
- Запросы данных (количество items, scores, analytics)

## Инструмент: `query_api`

### Schema

```python
{
    "type": "function",
    "function": {
        "name": "query_api",
        "description": "Send HTTP requests to the backend API. Use for database queries, API testing, and debugging.",
        "parameters": {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE"],
                    "description": "HTTP method for the request"
                },
                "path": {
                    "type": "string",
                    "description": "API endpoint path (e.g., '/items/', '/learners/', '/analytics/completion-rate?lab=lab-99')"
                },
                "body": {
                    "type": "string",
                    "description": "Optional JSON request body for POST/PUT requests"
                }
            },
            "required": ["method", "path"]
        }
    }
}
```

### Реализация

```python
def query_api(method: str, path: str, body: Optional[str] = None) -> str:
    """Send HTTP request to backend API with authentication."""
    # Clean up path
    if not path.startswith('/'):
        path = '/' + path
    
    url = f"{AGENT_API_BASE_URL}{path}"
    headers = {
        "X-API-Key": LMS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Make request based on method
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            data = json.loads(body) if body else None
            response = requests.post(url, headers=headers, json=data, timeout=10)
        # ... PUT, DELETE
        
        # Parse response
        try:
            body_content = response.json()
        except:
            body_content = response.text
        
        # Build result with metadata
        result = {
            "status_code": response.status_code,
            "body": body_content
        }
        
        # Add helpful metadata for lists
        if isinstance(body_content, list):
            result["count"] = len(body_content)
            result["_note"] = f"Response contains {len(body_content)} items"
        
        # Add error details if present
        if response.status_code >= 400 and isinstance(body_content, dict):
            if "detail" in body_content:
                result["error_detail"] = body_content["detail"]
        
        return json.dumps(result)
        
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "status_code": 503,
            "body": f"Could not connect to API at {AGENT_API_BASE_URL}"
        })
    except Exception as e:
        return json.dumps({
            "status_code": 500,
            "body": f"Error making request: {str(e)}"
        })
```

## Аутентификация

- **LMS_API_KEY**: Из `.env.docker.secret` (backend API key)
- **Header**: `X-API-Key: {LMS_API_KEY}`
- **Base URL**: Из `AGENT_API_BASE_URL` (default: `http://localhost:42002`)

## Переменные окружения

| Variable | Purpose | Source |
|----------|---------|--------|
| `LLM_API_KEY` | LLM provider API key | `.env.agent.secret` |
| `LLM_API_BASE` | LLM API endpoint URL | `.env.agent.secret` |
| `LLM_MODEL` | Model name | `.env.agent.secret` |
| `LMS_API_KEY` | Backend API key | `.env.docker.secret` |
| `AGENT_API_BASE_URL` | Backend URL | Optional, defaults to localhost:42002 |

**Важно:** Два разных ключа:

- `LMS_API_KEY` — для аутентификации в backend API
- `LLM_API_KEY` — для аутентификации в LLM provider

## Обновление System Prompt

Добавить инструкции, когда использовать каждый инструмент:

### Когда использовать `query_api`

- Информация о базе данных (количество items, данные learners)
- Тестирование поведения API (status codes, error responses)
- Analytics данные (completion rates, learner statistics)

### Когда использовать `read_file`

- Wiki документация
- Исходный код (фреймворк, routers, models)
- Конфигурационные файлы (docker-compose.yml, Dockerfile)
- Поиск багов после получения ошибки от API

### Когда использовать `list_files`

- Исследование структуры проекта
- Поиск доступных routers или модулей

## Специальные типы вопросов

### A. Подсчёт learners (Hidden Question 14)

- Запросить `/learners/` endpoint
- Посчитать уникальные IDs в response
- Использовать `count` metadata из query_api

### B. Сравнение error handling (Hidden Question 18)

- Прочитать `etl.py` для transaction/rollback patterns
- Прочитать router файлы для try/except patterns
- Сравнить стратегии систематически

### C. Баг диагностика (Questions 6-7)

1. Сначала использовать `query_api` чтобы увидеть ошибку
2. Затем использовать `read_file` на соответствующем исходном коде
3. Error message часто указывает на проблемную строку

### D. Framework вопросы (Question 2)

- Смотреть `main.py` или `app.py` для FastAPI imports
- Проверить `requirements.txt` или `pyproject.toml` для dependencies

### E. Request lifecycle (Question 8)

- Прочитать `docker-compose.yml` чтобы увидеть все сервисы
- Прочитать `Dockerfile` чтобы увидеть как app built
- Прочитать `main.py` чтобы увидеть FastAPI app setup
- Trace: browser → Caddy → FastAPI → auth → router → ORM → DB

## Функция determine_source

```python
def determine_source(tool_calls_log: List[Dict]) -> str:
    """Determine the source based on tool calls made."""
    if not tool_calls_log:
        return ""
    
    # Check for read_file calls
    read_calls = [tc for tc in tool_calls_log if tc["tool"] == "read_file"]
    if read_calls:
        last_read = read_calls[-1]
        path = last_read["args"]["path"]
        # Check if it's a wiki file
        if "wiki" in path or path.endswith(".md"):
            return path
        else:
            return f"code: {path}"
    
    # Check for query_api calls
    api_calls = [tc for tc in tool_calls_log if tc["tool"] == "query_api"]
    if api_calls:
        last_api = api_calls[-1]
        return f"API: {last_api['args']['method']} {last_api['args']['path']}"
    
    return ""
```

## Обновление agent loop

В `run_agent` функции, когда возвращаем результат:

```python
return {
    "answer": message.content or "",
    "source": determine_source(tool_calls_log),
    "tool_calls": tool_calls_log
}
```

## Этапы реализации

1. [ ] Проверить, что `agent.py` содержит все необходимые изменения
2. [ ] Убедиться, что `query_api` правильно аутентифицируется
3. [ ] Проверить, что system prompt обновлён
4. [ ] Запустить `run_eval.py` и исправить ошибки
5. [ ] Написать 2 regression теста
6. [ ] Обновить `AGENT.md` документацию
7. [ ] Финальная проверка всех тестов

## Тесты

### Test 1: Framework question

**Вопрос:** "What framework does the backend use?"
**Ожидается:**

- `tool_calls` содержит вызов `read_file`
- `answer` содержит "FastAPI"

### Test 2: Item count question

**Вопрос:** "How many items are in the database?"
**Ожидается:**

- `tool_calls` содержит вызов `query_api`
- `answer` содержит число > 0

## Риски и решения

| Риск | Решение |
|------|---------|
| API недоступен | Проверить, что backend запущен через docker-compose |
| Неправильная аутентификация | Убедиться, что LMS_API_KEY из `.env.docker.secret` |
| LLM не использует query_api | Улучшить description в tool schema |
| Timeout при запросе | Увеличить timeout или уменьшить max_iterations |

## Benchmark Questions

| # | Question | Grading | Expected | Tools required |
|---|----------|---------|----------|----------------|
| 0 | According to the project wiki, what steps are needed to protect a branch on GitHub? | keyword | `branch`, `protect` | `read_file` |
| 1 | What does the project wiki say about connecting to your VM via SSH? Summarize the key steps. | keyword | `ssh` / `key` / `connect` | `read_file` |
| 2 | What Python web framework does this project's backend use? Read the source code to find out. | keyword | `FastAPI` | `read_file` |
| 3 | List all API router modules in the backend. What domain does each one handle? | keyword | `items`, `interactions`, `analytics`, `pipeline` | `list_files` |
| 4 | How many items are currently stored in the database? Query the running API to find out. | keyword | a number > 0 | `query_api` |
| 5 | What HTTP status code does the API return when you request `/items/` without an authentication header? | keyword | `401` / `403` | `query_api` |
| 6 | Query `/analytics/completion-rate` for a lab with no data (e.g., `lab-99`). What error do you get, and what is the bug in the source code? | keyword | `ZeroDivisionError` / `division by zero` | `query_api`, `read_file` |
| 7 | The `/analytics/top-learners` endpoint crashes for some labs. Query it, find the error, and read the source code to explain what went wrong. | keyword | `TypeError` / `None` / `NoneType` / `sorted` | `query_api`, `read_file` |
| 8 | Read `docker-compose.yml` and the backend `Dockerfile`. Explain the full journey of an HTTP request from the browser to the database and back. | **LLM judge** | must trace ≥4 hops: Caddy → FastAPI → auth → router → ORM → PostgreSQL | `read_file` |
| 9 | Read the ETL pipeline code. Explain how it ensures idempotency — what happens if the same data is loaded twice? | **LLM judge** | must identify the `external_id` check and explain that duplicates are skipped | `read_file` |

## Initial Score

Запустить после первого прогона `run_eval.py`:

```
X/10 passed
```

## Iteration Strategy

1. Запустить `run_eval.py`
2. Для каждого failing question:
   - Прочитать feedback
   - Проверить, какой инструмент используется
   - Улучшить system prompt или tool description
   - Перезапустить тест
3. Повторять, пока все 10 вопросов не пройдут
