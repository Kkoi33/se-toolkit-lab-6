# Agent Architecture

## Overview

This agent is a CLI tool that connects to an LLM and answers questions about the project. It uses an **agentic loop** with tools to read files, navigate the project wiki, and query the deployed backend API for live data.

## LLM Provider

**Provider:** Qwen Code API
**Model:** `qwen3-coder-plus`
**API Format:** OpenAI-compatible chat completions API with function calling

### Why Qwen Code?

- 1000 free requests per day
- Works from Russia without credit card
- OpenAI-compatible API endpoint
- Strong tool calling support

## Architecture

### Components

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CLI Input     │ ──► │   agent.py   │ ──► │   LLM API       │
│   (question)    │     │  (orchestrator)   │  (qwen3-coder)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │                      │
                               │ ◄──── tool calls ────┘
                               ▼
                        ┌──────────────────┐
                        │   Tools:         │
                        │  read_file       │
                        │  list_files      │
                        │  query_api       │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  JSON Output │
                        │  (stdout)    │
                        └──────────────┘
```

### Agentic Loop

The agent follows an iterative loop:

1. **Send question to LLM** with tool definitions
2. **LLM decides** whether to call tools or give final answer
3. **If tool calls:**
   - Execute each tool
   - Append results as `tool` role messages
   - Go back to step 1
4. **If final answer:**
   - Extract answer and source
   - Output JSON and exit
5. **Maximum 10 tool calls** per question (prevents infinite loops)

```
Question ──▶ LLM ──▶ tool calls? ──yes──▶ execute tools ──▶ back to LLM
                         │
                         no
                         │
                         ▼
                    JSON output
```

### Data Flow

1. **Parse input**: Read question from `sys.argv[1]`
2. **Load config**: Read `.env.agent.secret` for API credentials
3. **Initialize messages**: System prompt + user question
4. **Agentic loop** (max 10 iterations):
   - Call LLM with messages and tool definitions
   - If tool calls returned:
     - Execute each tool (`read_file` or `list_files`)
     - Log tool call with result
     - Add tool result to messages
     - Continue loop
   - If final answer (no tool calls):
     - Extract answer text
     - Extract source reference
     - Break loop
5. **Format output**: JSON with `answer`, `source`, and `tool_calls`
6. **Output**: JSON to stdout, debug info to stderr

### Output Format

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [
    {
      "tool": "list_files",
      "args": {"path": "wiki"},
      "result": "git-workflow.md\nimages\n..."
    },
    {
      "tool": "read_file",
      "args": {"path": "wiki/git-workflow.md"},
      "result": "# Git workflow for tasks\n\n..."
    }
  ]
}
```

**Fields:**

- `answer` (string, required): The LLM's response to the question
- `source` (string, required): Wiki section reference (e.g., `wiki/git-workflow.md#section`)
- `tool_calls` (array, required): All tool calls made during the agentic loop

## Tools

### `read_file`

Read contents of a file from the project repository.

**Parameters:**

- `path` (string, required): Relative path from project root (e.g., `wiki/git-workflow.md`)

**Returns:** File contents as a string, or error message

**Security:**

- Blocks path traversal attempts (`../`)
- Only allows files within project directory

**Example:**

```python
read_file("wiki/git-workflow.md")
# Returns: "# Git workflow for tasks\n\n..."
```

### `list_files`

List files and directories at a given path.

**Parameters:**

- `path` (string, required): Relative directory path from project root (e.g., `wiki`)

**Returns:** Newline-separated listing of entries, or error message

**Security:**

- Blocks path traversal attempts (`../`)
- Only allows directories within project directory

**Example:**

```python
list_files("wiki")
# Returns: "api.md\narchitectural-views.md\n..."
```

### `query_api` (Task 3)

Call the deployed backend API to get live data, check status codes, or query the database.

**Parameters:**

- `method` (string, required): HTTP method (GET, POST, etc.)
- `path` (string, required): API endpoint path (e.g., `/items/`, `/analytics/completion-rate`)
- `body` (string, optional): JSON request body for POST requests

**Returns:** JSON string with `status_code` and `body` fields

**Authentication:**

- Uses `LMS_API_KEY` from `.env.docker.secret`
- Sends `Authorization: Bearer <LMS_API_KEY>` header

**Example:**

```python
query_api("GET", "/items/")
# Returns: '{"status_code": 200, "body": "[...]"}'

query_api("POST", "/items/", body='{"name": "test"}')
# Returns: '{"status_code": 201, "body": "{...}"}'
```

**When to use:**

- Questions about current database state (e.g., "How many items...?")
- Questions about API behavior (e.g., "What status code does /items/ return?")
- Bug diagnosis (e.g., "Query /analytics/completion-rate and find the error")

## Configuration

### Environment Files

The agent uses two environment files:

**`.env.agent.secret`** — LLM provider credentials

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | API key for LLM provider | `your-api-key` |
| `LLM_API_BASE` | Base URL of LLM API | `http://vm-ip:port/v1` |
| `LLM_MODEL` | Model name | `qwen3-coder-plus` |

**`.env.docker.secret`** — Backend API credentials

| Variable | Description | Example |
|----------|-------------|---------|
| `LMS_API_KEY` | Backend API key for `query_api` authentication | `my-secret-api-key` |
| `AGENT_API_BASE_URL` | Base URL for backend API (optional) | `http://localhost:42002` |

### Setup Steps

1. Copy example: `cp .env.agent.example .env.agent.secret`
2. Fill in your LLM credentials (see `wiki/qwen.md` for Qwen Code setup)
3. Copy backend example: `cp .env.docker.example .env.docker.secret`
4. Fill in `LMS_API_KEY` from your backend configuration

> **Note:** Two distinct keys: `LMS_API_KEY` (in `.env.docker.secret`) protects your backend endpoints. `LLM_API_KEY` (in `.env.agent.secret`) authenticates with your LLM provider. Don't mix them up.

## System Prompt Strategy

The system prompt instructs the LLM to:

1. Analyze the question to determine which tool(s) to use
2. Use `list_files` to discover wiki files
3. Use `read_file` to read relevant content
4. Use `query_api` for live data from the backend
5. Include source references in the final answer
6. Not make up information — only use actual file content or API responses

**Key instructions:**

```
You are a system agent that answers questions about a software engineering project.

You have access to three tools:
- list_files: List files and directories at a given path
- read_file: Read contents of a file from the project repository
- query_api: Call the deployed backend API to get live data

Tool selection guide:
- Use list_files to discover what files exist (e.g., in wiki/ or backend/)
- Use read_file to read documentation, source code, or configuration files
- Use query_api to query live system data, check API responses, or get status codes
```

## Usage

### Basic Usage

```bash
uv run agent.py "How do you resolve a merge conflict?"
```

### Expected Output

```json
{
  "answer": "Edit the conflicting file, choose which changes to keep, then stage and commit.",
  "source": "wiki/git-workflow.md#resolving-merge-conflicts",
  "tool_calls": [...]
}
```

### Error Handling

| Error | Exit Code | Output |
|-------|-----------|--------|
| No question provided | 1 | Error message to stderr |
| Missing API key | 1 | Error message to stderr |
| API timeout (>60s) | 1 | Error message to stderr |
| HTTP error | 1 | Error message + response to stderr |
| Network error | 1 | Error message to stderr |
| Path traversal attempt | N/A | Error in tool result (not exit) |

## Security

### Path Security

Both tools validate paths to prevent directory traversal:

1. **Normalize path**: Remove leading/trailing slashes, check for `..`
2. **Resolve to absolute**: Convert to absolute path
3. **Check prefix**: Ensure path starts with project root
4. **Block access**: Return error message if outside project

```python
def is_safe_path(base_path: Path, requested_path: Path) -> bool:
    base_resolved = base_path.resolve()
    requested_resolved = requested_path.resolve()
    return str(requested_resolved).startswith(str(base_resolved) + os.sep)
```

## Testing

### Manual Testing

```bash
# Test list_files
uv run agent.py "What files are in the wiki?"

# Test read_file
uv run agent.py "How do you resolve a merge conflict?"
```

### Automated Testing

Run regression tests:

```bash
uv run pytest backend/tests/agent/test_agent.py
uv run pytest test_agent.py
```

Tests verify:

- JSON output format with `answer`, `source`, `tool_calls` fields
- Correct tool usage for specific questions
- Source field contains wiki file reference

## File Structure

```
project-root/
├── agent.py              # Main CLI entry point with agentic loop
├── .env.agent.secret     # LLM credentials (gitignored)
├── .env.agent.example    # Example configuration
├── AGENT.md              # This documentation
├── plans/task-2.md       # Implementation plan
├── test_agent.py         # Regression tests
└── wiki/                 # Documentation files
    ├── git-workflow.md
    └── ...
```

## Dependencies

- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable loading

## Comparison: Task 1 vs Task 2 vs Task 3

| Feature | Task 1 | Task 2 | Task 3 |
|---------|--------|--------|--------|
| Tools | None | `read_file`, `list_files` | + `query_api` |
| Agentic loop | No | Yes (max 10 iterations) | Yes |
| Output fields | `answer`, `tool_calls` | `answer`, `source`, `tool_calls` | Same (source can be API endpoint) |
| Can read files | No | Yes | Yes |
| Can query API | No | No | Yes |
| System prompt | Basic | Workflow instructions | Tool selection guide |

## Lessons Learned (Task 3)

### Environment Variable Management

One key challenge was managing two separate API keys:

- `LLM_API_KEY` for the LLM provider (in `.env.agent.secret`)
- `LMS_API_KEY` for the backend API (in `.env.docker.secret`)

Initially, I was tempted to hardcode the backend URL, but the autochecker injects different values. The solution was to read all configuration from environment variables, with `AGENT_API_BASE_URL` defaulting to `http://localhost:42002`.

### Tool Description Design

The LLM needs clear guidance on when to use each tool. The initial system prompt was too vague, causing the agent to use `read_file` for questions that required live API data. Adding explicit "When to use" sections for each tool significantly improved tool selection accuracy.

### Source Field for API Queries

The `source` field was originally designed for wiki references. For API queries, I extended it to accept endpoint references like `API: GET /items/`. This maintains consistency in the output format while supporting the new tool.

### Error Handling

The `query_api` tool needed robust error handling for:

- Missing `LMS_API_KEY` (returns 500 with clear message)
- Network errors (caught and returned as JSON)
- Unsupported HTTP methods (returns 400)

### Benchmark Iteration Strategy

Running `run_eval.py` revealed several issues:

1. Agent wasn't calling `query_api` for database questions → improved system prompt
2. API calls failed due to missing authentication → ensured `LMS_API_KEY` is loaded
3. Source field was empty for API queries → updated `extract_source_from_answer`

## Benchmark Results

**Final Score:** (to be filled after running `run_eval.py`)

| Question | Topic | Tool Required | Status |
|----------|-------|---------------|--------|
| 0 | Branch protection (wiki) | `read_file` | - |
| 1 | SSH connection (wiki) | `read_file` | - |
| 2 | Backend framework (source) | `read_file` | - |
| 3 | API router modules | `list_files` | - |
| 4 | Item count (database) | `query_api` | - |
| 5 | Status code without auth | `query_api` | - |
| 6 | ZeroDivisionError bug | `query_api`, `read_file` | - |
| 7 | TypeError in top-learners | `query_api`, `read_file` | - |
| 8 | Request lifecycle | `read_file` | LLM judge |
| 9 | ETL idempotency | `read_file` | LLM judge |

## Future Extensions

Potential improvements:

- Add more tools (`search_file`, `grep`)
- Improve source extraction (better section anchor detection)
- Add caching for repeated file reads
- Support for multiple wiki directories
- Query parameter support in `query_api` (e.g., `?lab=lab-99`)
