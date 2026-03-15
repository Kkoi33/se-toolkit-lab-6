# Agent Architecture

## Overview

This agent is a CLI tool that connects to an LLM and answers questions about the project documentation. It uses an **agentic loop** with tools to read files and navigate the project wiki.

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
                        ┌──────────────┐
                        │   Tools:     │
                        │  read_file   │
                        │  list_files  │
                        └──────────────┘
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

## Configuration

### Environment File: `.env.agent.secret`

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_API_KEY` | API key for LLM provider | `your-api-key` |
| `LLM_API_BASE` | Base URL of LLM API | `http://vm-ip:port/v1` |
| `LLM_MODEL` | Model name | `qwen3-coder-plus` |

### Setup Steps

1. Copy example: `cp .env.agent.example .env.agent.secret`
2. Fill in your credentials (see `wiki/qwen.md` for Qwen Code setup)

## System Prompt Strategy

The system prompt instructs the LLM to:

1. Use `list_files` to discover wiki files
2. Use `read_file` to read relevant content
3. Include source references in the final answer
4. Not make up information — only use actual file content

**Key instructions:**

```
You are a documentation agent that answers questions about a software engineering project.

Workflow:
1. Use list_files to discover what files exist in the wiki/ directory
2. Use read_file to read relevant files and find the answer
3. When you find the answer, provide it along with the source reference

Important:
- Always include the source field in your final answer
- Do not make up information — only use content from actual files
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

## Comparison: Task 1 vs Task 2

| Feature | Task 1 | Task 2 |
|---------|--------|--------|
| Tools | None | `read_file`, `list_files` |
| Agentic loop | No | Yes (max 10 iterations) |
| Output fields | `answer`, `tool_calls` | `answer`, `source`, `tool_calls` |
| Can read files | No | Yes |
| System prompt | Basic | Workflow instructions |

## Future Extensions

Potential improvements:

- Add more tools (`search_file`, `grep`)
- Improve source extraction (better section anchor detection)
- Add caching for repeated file reads
- Support for multiple wiki directories
