# Agent Architecture

## Overview

This agent is a CLI tool that connects to an LLM and answers questions. It forms the foundation for the agentic system that will be extended with tools and a planning loop in Tasks 2–3.

## LLM Provider

**Provider:** Qwen Code API  
**Model:** `qwen3-coder-plus`  
**API Format:** OpenAI-compatible chat completions API

### Why Qwen Code?

- 1000 free requests per day
- Works from Russia without credit card
- OpenAI-compatible API endpoint
- Strong tool calling support (for Task 2+)

## Architecture

### Components

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CLI Input     │ ──► │   agent.py   │ ──► │   LLM API       │
│   (question)    │     │  (orchestrator)   │  (qwen3-coder)    │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  JSON Output │
                        │  (stdout)    │
                        └──────────────┘
```

### Data Flow

1. **Parse input**: Read question from `sys.argv[1]`
2. **Load config**: Read `.env.agent.secret` for API credentials
3. **Call LLM**: HTTP POST to `{LLM_API_BASE}/chat/completions`
4. **Parse response**: Extract `choices[0].message.content`
5. **Format output**: JSON with `answer` and `tool_calls` fields
6. **Output**: JSON to stdout, debug info to stderr

### Output Format

```json
{"answer": "Representational State Transfer.", "tool_calls": []}
```

- `answer` (string): The LLM's response to the question
- `tool_calls` (array): Empty for Task 1, populated in Task 2+

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

## Usage

### Basic Usage

```bash
uv run agent.py "What does REST stand for?"
```

### Expected Output

```json
{"answer": "Representational State Transfer.", "tool_calls": []}
```

### Error Handling

| Error | Exit Code | Output |
|-------|-----------|--------|
| No question provided | 1 | Error message to stderr |
| Missing API key | 1 | Error message to stderr |
| API timeout (>60s) | 1 | Error message to stderr |
| HTTP error | 1 | Error message + response to stderr |
| Network error | 1 | Error message to stderr |

## Testing

### Manual Testing

```bash
uv run agent.py "What is 2+2?"
```

### Automated Testing

Run the regression test:

```bash
uv run pytest backend/tests/agent/test_agent.py
```

The test:
- Runs `agent.py` as a subprocess
- Parses stdout as JSON
- Validates `answer` (string) and `tool_calls` (array) fields exist

## File Structure

```
project-root/
├── agent.py              # Main CLI entry point
├── .env.agent.secret     # LLM credentials (gitignored)
├── .env.agent.example    # Example configuration
├── AGENT.md              # This documentation
└── plans/task-1.md       # Implementation plan
```

## Dependencies

- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable loading

## Future Extensions (Tasks 2–3)

- **Task 2**: Add tool calling capability
  - Define tools (e.g., `query_api`, `read_file`)
  - Parse tool calls from LLM response
  - Execute tools and return results
  - Populate `tool_calls` in output

- **Task 3**: Add agentic loop
  - Multi-turn conversation support
  - Tool result feedback to LLM
  - Planning and reasoning capabilities
