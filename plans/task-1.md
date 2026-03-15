# План реализации Task 1: Call an LLM from Code

## LLM Provider и модель

**Provider:** Qwen Code API (OpenAI-compatible endpoint)
**Модель:** `qwen3-coder-plus`

### Почему этот выбор

- Qwen Code предоставляет 1000 бесплатных запросов в день
- Работает из России без кредитной карты
- Поддерживает OpenAI-compatible API
- Модель `qwen3-coder-plus` имеет сильную поддержку tool calling (понадобится в Task 2)

## Архитектура агента

### Входные данные
- Вопрос пользователя передаётся как первый аргумент командной строки
- Пример: `uv run agent.py "What does REST stand for?"`

### Конфигурация
- API ключ, базовый URL и модель читаются из `.env.agent.secret`
- Используем `python-dotenv` для загрузки переменных окружения

### Поток данных

```
1. Parse CLI argument (sys.argv[1]) → question
2. Load config from .env.agent.secret
3. Call LLM API (HTTP POST to /chat/completions)
4. Parse response → extract answer
5. Format output as JSON: {"answer": "...", "tool_calls": []}
6. Output JSON to stdout, debug info to stderr
```

### Структура agent.py

```python
# Псевдокод
import sys, json, os, httpx
from dotenv import load_dotenv

load_dotenv(".env.agent.secret")

def call_lllm(question: str) -> str:
    # POST to LLM_API_BASE/chat/completions
    # Headers: Authorization, Content-Type
    # Body: model, messages
    # Return: response.choices[0].message.content

def main():
    if len(sys.argv) < 2:
        print("Error: No question provided", file=sys.stderr)
        sys.exit(1)
    
    question = sys.argv[1]
    answer = call_lllm(question)
    
    result = {"answer": answer, "tool_calls": []}
    print(json.dumps(result))  # stdout
```

### Обработка ошибок

- Нет аргумента → ошибка в stderr, exit code 1
- Таймаут API (>60 сек) → ошибка в stderr, exit code 1
- Неверный API ключ → ошибка в stderr, exit code 1
- Network error → ошибка в stderr, exit code 1

### Тесты

Один regression test в `backend/tests/`:
- Запускает `agent.py` как subprocess с тестовым вопросом
- Парсит stdout как JSON
- Проверяет наличие полей `answer` (string) и `tool_calls` (array)

## Этапы реализации

1. [x] Создать plans/task-1.md
2. [ ] Скопировать `.env.agent.example` → `.env.agent.secret`, заполнить
3. [ ] Создать `agent.py` с базовой структурой
4. [ ] Реализовать вызов LLM API
5. [ ] Добавить обработку ошибок и таймауты
6. [ ] Создать `AGENT.md` с документацией
7. [ ] Написать 1 regression test
8. [ ] Протестировать вручную
9. [ ] Запустить test
