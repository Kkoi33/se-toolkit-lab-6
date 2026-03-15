# План реализации Task 2: The Documentation Agent

## Обзор

В этом задании мы превращаем простой CLI-чатбот в агента с инструментами и агентовым циклом. Агент сможет читать файлы проекта и навигировать по wiki для поиска ответов.

## Инструменты

### 1. `read_file`

**Назначение:** Чтение содержимого файла из репозитория.

**Параметры:**
- `path` (string) — относительный путь от корня проекта

**Возвращает:** Содержимое файла как строку

**Безопасность:**
- Запретить чтение файлов вне проекта (блокировка `../` в пути)
- Разрешить только абсолютные пути внутри project root

**Реализация:**
```python
def read_file(path: str) -> str:
    # Нормализовать путь
    # Проверить, что путь не выходит за пределы проекта
    # Прочитать файл
    # Вернуть содержимое или сообщение об ошибке
```

### 2. `list_files`

**Назначение:** Список файлов и директорий по указанному пути.

**Параметры:**
- `path` (string) — относительный путь директории от корня проекта

**Возвращает:** Список файлов/директорий, разделённых newline

**Безопасность:**
- Запретить доступ к директориям вне проекта
- Проверять, что путь — директория, а не файл

**Реализация:**
```python
def list_files(path: str) -> str:
    # Нормализовать путь
    # Проверить, что путь внутри проекта
    # Получить список файлов
    # Вернуть как строку с newline
```

## Tool Schemas для LLM

Определим схемы инструментов для function calling API:

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read contents of a file from the project repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories at a given path",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative directory path from project root (e.g., 'wiki')"
                    }
                },
                "required": ["path"]
            }
        }
    }
]
```

## Агентовый цикл

### Алгоритм

```
1. Инициализировать messages = [system_prompt, user_question]
2. Инициализировать tool_calls_log = []
3. Пока len(tool_calls_log) < 10:
   a. Отправить messages к LLM с tool definitions
   b. Если LLM вернул tool_calls:
      - Для каждого tool_call:
        * Выполнить инструмент
        * Добавить результат в tool_calls_log
        * Добавить сообщение с результатом в messages (role: "tool")
      - Продолжить цикл (шаг 3a)
   c. Если LLM вернул текстовый ответ (без tool_calls):
      - Извлечь answer из сообщения
      - Извлечь source (путь к файлу + якорь раздела)
      - Вернуть JSON и выйти
4. Если достигнуто 10 tool calls:
   - Использовать имеющийся ответ
   - Вернуть JSON
```

### Структура данных

```python
messages: list[dict] = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": question}
]

tool_calls_log: list[dict] = []
# Каждый элемент: {"tool": "...", "args": {...}, "result": "..."}
```

### Обработка tool_calls от LLM

Формат ответа LLM (OpenAI-compatible API):

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": null,
      "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "read_file",
            "arguments": "{\"path\": \"wiki/git-workflow.md\"}"
          }
        }
      ]
    }
  }]
}
```

После выполнения инструмента добавляем сообщение:

```json
{
  "role": "tool",
  "tool_call_id": "call_abc123",
  "content": "<результат выполнения>"
}
```

## System Prompt

System prompt должен инструктировать LLM:

1. Использовать `list_files` для навигации по wiki
2. Использовать `read_file` для чтения содержимого файлов
3. Включать source reference (путь файла + якорь раздела) в ответ
4. Не выдумывать информацию — использовать только данные из файлов

**Пример system prompt:**

```
You are a documentation agent that answers questions about a software engineering project.

You have access to two tools:
- list_files: List files in a directory
- read_file: Read contents of a file

Workflow:
1. Use list_files to discover what files exist in the wiki/ directory
2. Use read_file to read relevant files and find the answer
3. When you find the answer, provide it along with the source reference

Important:
- Always include the source field in your final answer (e.g., "wiki/git-workflow.md#resolving-merge-conflicts")
- Do not make up information — only use content from actual files
- If you cannot find the answer, say so honestly

Format your final answer clearly and include the source reference.
```

## Безопасность путей

### Проверка путей

```python
def is_safe_path(base_path: Path, requested_path: Path) -> bool:
    """Check if requested_path is within base_path."""
    try:
        # Resolve to absolute paths
        base_resolved = base_path.resolve()
        requested_resolved = requested_path.resolve()
        
        # Check if requested is under base
        return str(requested_resolved).startswith(str(base_resolved))
    except (OSError, ValueError):
        return False
```

### Нормализация путей

```python
def normalize_path(project_root: Path, relative_path: str) -> Path:
    """Normalize and validate relative path."""
    # Remove leading/trailing slashes
    relative_path = relative_path.strip("/")
    
    # Build absolute path
    absolute_path = project_root / relative_path
    
    # Check for path traversal attempts
    if ".." in relative_path.split("/") or ".." in relative_path.split("\\"):
        raise ValueError("Path traversal not allowed")
    
    return absolute_path
```

## Формат вывода JSON

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "..."
    }
  ]
}
```

### Поля

- `answer` (string, required) — ответ на вопрос
- `source` (string, required) — ссылка на раздел wiki (файл + якорь)
- `tool_calls` (array, required) — все вызовы инструментов с результатами

## Тесты

### Test 1: Merge conflict question

**Вопрос:** "How do you resolve a merge conflict?"

**Ожидается:**
- `tool_calls` содержит вызовы `read_file`
- `source` содержит `wiki/git-workflow.md`

### Test 2: Wiki listing question

**Вопрос:** "What files are in the wiki?"

**Ожидается:**
- `tool_calls` содержит вызов `list_files`
- `args.path` равен `"wiki"`

## Этапы реализации

1. [ ] Создать `plans/task-2.md` с этим планом
2. [ ] Определить tool schemas
3. [ ] Реализовать функцию `read_file` с проверкой безопасности
4. [ ] Реализовать функцию `list_files` с проверкой безопасности
5. [ ] Реализовать `call_llm` с поддержкой tool calling
6. [ ] Реализовать агентовый цикл в `main()`
7. [ ] Добавить извлечение `source` из ответа
8. [ ] Обновить `AGENT.md` с документацией
9. [ ] Написать 2 regression теста
10. [ ] Запустить тесты, проверить acceptance criteria

## Зависимости

- `httpx` — уже установлен
- `python-dotenv` — уже установлен
- Никаких новых зависимостей не требуется

## Риски и решения

| Риск | Решение |
|------|---------|
| LLM не использует инструменты | Улучшить system prompt, добавить примеры |
| Path traversal атаки | Строгая проверка путей с `resolve()` и `startswith()` |
| Бесконечный цикл tool calls | Лимит 10 итераций |
| LLM не включает source в ответ | Явная инструкция в system prompt, парсинг ответа |
