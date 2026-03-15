# Task 3: The System Agent - Implementation Plan

## Tool Schema: query_api

I will add a new tool `query_api` that allows the agent to call the deployed backend API.

**Parameters:**

- `method` (string): GET, POST, etc.
- `path` (string): API endpoint path (e.g., "/items/")
- `body` (string, optional): JSON request body for POST requests

**Returns:** JSON string with `status_code` and `body`

## Authentication

- Use `LMS_API_KEY` from `.env.docker.secret`
- Base URL from `AGENT_API_BASE_URL` (default: <http://localhost:42002>)

## System Prompt Updates

The LLM needs to know when to use:

- `read_file` → for wiki/docs/code
- `list_files` → for exploring structure
- `query_api` → for live system data, API status codes, database queries

## Implementation Steps

### 1. Add query_api to TOOLS list

The tool schema needs to be added to the `TOOLS` array so the LLM knows it can call it.

### 2. Update execute_tool function

Add handling for `query_api` tool name to call the existing `query_api()` function.

### 3. Load LMS_API_KEY

Read `LMS_API_KEY` from `.env.docker.secret` at module level.

### 4. Update SYSTEM_PROMPT

Add instructions about when to use each tool:

- Wiki questions → `read_file`, `list_files`
- System facts (framework, ports, status codes) → `query_api` or `read_file` on source
- Data queries (item count, scores) → `query_api`
- Bug diagnosis → `query_api` first, then `read_file` on source code

### 5. Handle source field for system questions

For system questions, the source may not be a wiki file. Update `extract_source_from_answer` to handle this case.

## Benchmark Strategy

1. First run: get baseline score
2. Fix failures one by one:
   - API errors → improve error handling
   - Wrong tool choice → clarify tool descriptions
   - Wrong arguments → improve parameter docs
3. Iterate until all 10 pass

## Initial Score (to be filled after first run)

- Run 1: __/10
- Main failures:
  - Question 4:
  - Question 5:
  - etc.

## Iteration Log

### Implementation Complete

**Changes made:**

1. ✅ Added `query_api` tool schema to `TOOLS` list
2. ✅ Updated `execute_tool()` to handle `query_api` calls
3. ✅ Added loading of `LMS_API_KEY` from `.env.docker.secret`
4. ✅ Updated `SYSTEM_PROMPT` with tool selection guide
5. ✅ Updated `extract_source_from_answer()` to handle API endpoints
6. ✅ Updated `query_api()` to use global config variables
7. ✅ Created `.env.agent.secret` and `.env.docker.secret` files
8. ✅ Added 2 regression tests for new tools
9. ✅ Updated `AGENT.md` documentation (Lessons Learned, Benchmark Results)

**Next step:** Run `run_eval.py` to test the agent against the benchmark questions.
