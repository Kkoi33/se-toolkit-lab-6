# Advanced Agent Features

Extend your agent with advanced capabilities that improve reliability or expand what it can answer.

## Extension options

Choose **one or more** extensions. Each should measurably improve your agent — higher pass rate, lower latency, or better failure handling.

### Retry logic with backoff

LLM APIs have rate limits. Implement automatic retry with exponential backoff when the API returns 429 (Too Many Requests) or 5xx errors.

### Caching layer

Cache tool results in memory so that if the LLM calls `read_file("backend/app/main.py")` twice in the same run, the second call returns instantly.

### Direct database tool (`query_db`)

Add a `query_db` tool that runs **read-only** SQL queries against PostgreSQL directly. This lets the agent answer data questions without going through the API. Use a read-only connection to prevent accidental writes.

### Multi-step reasoning

Before executing tools, have the agent output a plan (what it needs to find out and which tools to use). Then execute the plan step by step. This improves accuracy on complex questions.

## Deliverables

### 1. Plan (`plans/optional-1.md`)

Document which extension(s) you chose, why, and the expected improvement.

### 2. Implementation (update `agent.py`)

Implement your chosen extension(s).

### 3. Tests

Write tests that demonstrate the extension works correctly.

### 4. Documentation (update `AGENT.md`)

Update `AGENT.md` to describe the extension(s) you implemented.

## Acceptance criteria

- [ ] At least one extension is implemented and working.
- [ ] Tests demonstrate the extension works correctly.
- [ ] `AGENT.md` is updated to describe the extension.
- [ ] [Git workflow](../../../wiki/git-workflow.md): issue `[Task] Advanced Agent Features`, branch, PR with `Closes #...`, partner approval, merge.
