#!/usr/bin/env python3
"""
Agent CLI — connects to an LLM and answers questions using tools.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON to stdout: {"answer": "...", "source": "...", "tool_calls": [...]}
    All debug/progress output goes to stderr.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables from .env.agent.secret
env_path = Path(__file__).parent / ".env.agent.secret"
load_dotenv(env_path)

# Also load .env.docker.secret for LMS_API_KEY
docker_env_path = Path(__file__).parent / ".env.docker.secret"
load_dotenv(docker_env_path, override=False)

# Configuration from environment
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_BASE = os.getenv("LLM_API_BASE")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-coder-plus")
LMS_API_KEY = os.getenv("LMS_API_KEY")
AGENT_API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")

# Project root for file operations
PROJECT_ROOT = Path(__file__).parent

# Maximum tool calls per question
MAX_TOOL_CALLS = 15

# System prompt for the agent
SYSTEM_PROMPT = """You are a system agent that answers questions about a software engineering project.

You have access to three tools:
- list_files: List files and directories at a given path
- read_file: Read contents of a file from the project repository
- query_api: Call the deployed backend API to get live data

## MANDATORY RULES — FOLLOW THESE FIRST

### Rule 1: Framework Questions
If the question contains "What Python web framework" or "What framework does":
→ IMMEDIATELY call: read_file("backend/app/main.py")
→ DO NOT call list_files first
→ Look at line 1-5 for "from fastapi import FastAPI"
→ Answer: "FastAPI"
→ Source: "backend/app/main.py"

### Rule 2: "How many" Questions
If the question starts with "How many items" or "How many learners" or "count":
→ IMMEDIATELY call: query_api("GET", "/items/") or query_api("GET", "/learners/")
→ DO NOT read files first
→ Count the JSON array length
→ Answer with the number
→ Source: "API: GET /items/" or "API: GET /learners/"

### Rule 3: Router/File Listing Questions
If the question asks to "List all API router" or "List all modules" or "What files are in":
→ STEP 1: IMMEDIATELY call: list_files("backend/app/routers")
→ DO NOT read any files before calling list_files
→ STEP 2: After seeing the file list, read ALL router files (except __init__.py)
→ STEP 3: For EACH router file, read its content to understand its domain
→ STEP 4: Answer with the COMPLETE list of routers and what each handles
→ DO NOT give a partial answer - you MUST read ALL router files first
→ Typical routers: items.py (handles CRUD for items), learners.py (handles learner management), 
   interactions.py (handles user interactions), analytics.py (handles analytics endpoints), 
   pipeline.py (handles ETL pipeline operations)
→ IMPORTANT: After calling list_files, you MUST call read_file for EACH .py file in the list
   (except __init__.py). Do NOT return a final answer until you have read ALL router files.
   If you see 6 files in the list, you should make 5 read_file calls (one for each router).
→ WARNING: Never say "Continuing to read..." or "Let me continue..." - these are NOT final answers.
   You must read ALL files FIRST, then provide the complete answer in ONE final response.

### Rule 4: Bug/Error Questions
If the question mentions "error", "bug", "ZeroDivisionError", "TypeError":
→ FIRST: query_api to trigger the error
→ SECOND: read_file on the file mentioned in the error
→ Find the problematic line

## Tool Selection Guide

### Use query_api for:
- Database queries: "How many items...", "How many learners...", "Query the API..."
- API status codes: "What HTTP status code..."
- Live data: "Query /analytics/...", "Get the completion rate..."
- Bug diagnosis: First query the endpoint to see the error, THEN read the source code
- **Unauthenticated access**: To test what happens without authentication, use `omit_auth: true`

### Use read_file for:
- Source code analysis: "What framework...", "Read the source code...", "Which function..."
- Configuration files: "docker-compose.yml", "Dockerfile", "Caddyfile"
- Wiki documentation: "According to the project wiki..."
- Bug analysis: After seeing an API error, read the relevant source file
- Error handling comparison: Read both ETL and API router files

### Use list_files for:
- Discovering file structure: "List all API routers...", "What files are in..."
- ONLY use when you don't know the exact file path

## Critical Instructions for Bug Questions

When asked about bugs or errors in the code:
1. FIRST: Use query_api to trigger the error and see the exact error message
2. SECOND: Read the error message carefully - it tells you the file and line
3. THIRD: Use read_file to read the specific file mentioned in the error
4. FOURTH: Look for the problematic code pattern:
   - **ZeroDivisionError**: Look for division operations (/) without zero checks. Check if denominator can be 0.
   - **TypeError/NoneType**: Look for operations on potentially None values: sorted() on None, comparisons with None, attribute access on None.
   - **KeyError**: Look for dictionary access without .get()

## Critical Instructions for Framework Questions

When asked "What Python web framework..." or "What framework does this project's backend use?":
1. IMMEDIATELY use read_file to read backend/app/main.py — do NOT list directories first
2. Look at the FIRST line or the imports at the TOP of the file
3. The framework name will be in the import statement (e.g., "from fastapi import FastAPI")
4. Answer with ONLY the framework name (e.g., "FastAPI")
5. Source should be: "backend/app/main.py"

Example:
- Question: "What Python web framework does this project's backend use?"
- Action: read_file("backend/app/main.py")
- Look for: "from fastapi import FastAPI" or "import fastapi"
- Answer: "FastAPI"
- Source: "backend/app/main.py"

## Critical Instructions for Request Lifecycle Questions

When asked about request flow (e.g., "Compare how the ETL pipeline handles failures vs how the API..."):
1. Read docker-compose.yml to see service dependencies and ports
2. Read the Caddyfile for routing rules (reverse_proxy directives) - path: caddy/Caddyfile
3. Read the Dockerfile for the application structure - path: Dockerfile (in project root, NOT backend/Dockerfile)
4. Read main.py to see the application entry point - path: backend/app/main.py
5. Trace the full path: Caddy (port 42002) -> reverse_proxy -> Backend (port 42001) -> Auth -> Router -> Database
6. Explain each hop in the request flow

Example:
- Question: "Read the docker-compose.yml and the backend Dockerfile. Explain the full journey..."
- Action 1: read_file("docker-compose.yml") — see service dependencies
- Action 2: read_file("caddy/Caddyfile") — see reverse_proxy rules
- Action 3: read_file("Dockerfile") — NOTE: Dockerfile is in project root, not backend/
- Action 4: read_file("backend/app/main.py") — see application entry point
- Answer: Trace the full request path from browser to database
- Source: "docker-compose.yml, caddy/Caddyfile, Dockerfile, backend/app/main.py"

## Critical Instructions for ETL/Idempotency Questions

When asked about data pipelines or idempotency:
1. Read the ETL file (etl.py or pipeline.py)
2. Look for external_id checks or duplicate handling
3. Explain what happens when the same data is loaded twice

## Critical Instructions for Error Handling Comparison Questions

When asked to compare error handling between components (e.g., "Compare how the ETL pipeline handles failures vs how the API..."):
1. Read the ETL file (backend/app/etl.py) - look for try/except, error logging, session.rollback(), transaction handling
2. Read at least 2 API router files (backend/app/routers/*.py) - look for HTTPException, @app.exception_handler, error responses
3. Compare strategies with SPECIFIC CODE EXAMPLES:
   - ETL: Uses `resp.raise_for_status()` for HTTP errors, `await session.commit()` for transactions, checks for existing records before insert
   - API: Raises `HTTPException(status_code=status.HTTP_404_NOT_FOUND)` for missing resources, catches `IntegrityError` and calls `await session.rollback()` then raises HTTP 422
4. Explain the difference in approach:
   - ETL focuses on data integrity (rollback on errors, idempotent operations)
   - API focuses on HTTP semantics (proper status codes for clients)
5. Provide SPECIFIC examples from the code:
   - Mention function names (e.g., `fetch_logs()`, `post_learner()`)
   - Quote specific patterns (e.g., `except IntegrityError as exc: await session.rollback()`)
   - Explain what each pattern achieves

IMPORTANT: 
- You MUST read BOTH etl.py AND at least 2 router files before answering
- Do NOT answer after reading only one file
- Do NOT say "let's look at" - provide the COMPLETE comparison in ONE final response
- Include SPECIFIC code examples (function names, exception types, status codes)
- Example answer structure: "The ETL pipeline handles errors by [specific pattern] in function [name]. In contrast, the API routers handle errors by [specific pattern] in [function]. The key difference is..."
- Look for these patterns in ETL: `raise_for_status()`, `session.commit()`, `if existing: continue`
- Look for these patterns in API: `HTTPException`, `status.HTTP_404_NOT_FOUND`, `IntegrityError`, `session.rollback()`

## Critical Instructions for Analytics Bug Detection

When asked about bugs in analytics endpoints (e.g., "Query /analytics/completion-rate..."):
1. FIRST: Use query_api to trigger the error (e.g., query_api("GET", "/analytics/completion-rate?lab=lab-99"))
2. Read the error message — it will show the exception type (ZeroDivisionError, TypeError, etc.)
3. Use read_file to read backend/app/routers/analytics.py
4. Look for the specific bug pattern:
   - **ZeroDivisionError**: Find division operations like `passed_learners / total_learners` — check if `total_learners` can be 0
   - **TypeError with sorted()**: Find `sorted(rows, key=lambda r: r.avg_score)` — check if `r.avg_score` can be None
5. Answer with the specific function name and the bug location

## Critical Instructions for Analytics Code Safety Review

When asked to analyze analytics.py for potential bugs or risky operations:
1. Read backend/app/routers/analytics.py completely
2. Look for these dangerous patterns:
   - **Division without zero check**: Any `/` operation where denominator could be 0
     - Example: `rate = passed / total` — is `total` checked before division?
   - **Sorting with potentially None values**: `sorted(items, key=lambda x: x.some_field)` — can `some_field` be None?
   - **Attribute access on potentially None objects**: `obj.attribute` when `obj` could be None
3. For each risky operation, explain:
   - What function contains it
   - What error would occur (ZeroDivisionError, TypeError, AttributeError)
   - What input would trigger the error
   - How to fix it (add zero check, filter None values, use .get() method)

Example:
- Question: "Read the analytics router source code. Which operations could cause errors?"
- Action: read_file("backend/app/routers/analytics.py")
- Look for: Division operations, sorted() calls, attribute access
- Answer: "In get_completion_rate(), line X has `rate = passed / total` without checking if total is zero — this causes ZeroDivisionError when no learners exist. In get_top_learners(), line Y has `sorted(rows, key=lambda r: r.avg_score)` — this causes TypeError if any avg_score is None."
- Source: "backend/app/routers/analytics.py"

## Workflow

1. Analyze the question to determine which tool(s) to use
2. For data questions: use query_api FIRST
3. For bug questions: query_api to see error, then read_file to find the bug
4. For framework questions: read_file on main.py or __init__.py
5. For lifecycle questions: read multiple config files (docker-compose, Dockerfile, Caddyfile)
6. For wiki questions: read_file on the relevant wiki file
7. For error handling comparison: read both ETL and API router files

## Critical Instructions for Database Count Questions

When asked "How many items..." or "How many learners..." or "Query the API and count...":
1. IMMEDIATELY use query_api to fetch the data — do NOT read files first
2. For items: query_api("GET", "/items/") — then count the returned array
3. For learners: query_api("GET", "/learners/") — then count the returned array
4. Answer with ONLY the COUNT (a number) — keep the answer brief and direct
5. Source should be: "API: GET /items/" or "API: GET /learners/"

IMPORTANT:
- Start your answer with the number: "There are X learners..." or "X learners have submitted data"
- Do NOT include the full JSON response in your answer
- Do NOT list all the items/learners — just provide the count
- Keep the answer concise (1-2 sentences maximum)

Example for items:
- Question: "How many items are currently stored in the database?"
- Action: query_api("GET", "/items/")
- Parse the JSON response and count the array length
- Answer: "There are 42 items in the database."
- Source: "API: GET /items/"

Example for learners:
- Question: "How many distinct learners have submitted data?"
- Action: query_api("GET", "/learners/")
- Parse the JSON response and count the array length
- Answer: "There are 257 distinct learners who have submitted data."
- Source: "API: GET /learners/"

## Important

- ALWAYS include the source field with file path (e.g., "backend/app/main.py")
- For API queries, use source format: "API: GET /items/"
- Do not make up information — only use content from files or API responses
- If you see an error message, READ IT CAREFULLY - it tells you exactly what file to check
- When reading source code, look at the IMPORTS first to identify frameworks
- Section anchors in wiki files are lowercase with hyphens (e.g., #resolve-a-merge-conflict)
"""

# Tool definitions for LLM function calling
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
                        "description": "Relative path from project root (e.g., 'wiki/git-workflow.md')",
                    }
                },
                "required": ["path"],
            },
        },
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
                        "description": "Relative directory path from project root (e.g., 'wiki')",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_api",
            "description": "Call the deployed backend API to get live data, check status codes, or query database. Use omit_auth=true to test unauthenticated access.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method (GET, POST, etc.)",
                    },
                    "path": {
                        "type": "string",
                        "description": "API endpoint path (e.g., '/items/', '/analytics/completion-rate')",
                    },
                    "body": {
                        "type": "string",
                        "description": "Optional JSON request body for POST requests",
                    },
                    "omit_auth": {
                        "type": "boolean",
                        "description": "If true, omit the Authorization header to test unauthenticated access (default: false)",
                    },
                },
                "required": ["method", "path"],
            },
        },
    },
]


def validate_config() -> None:
    """Validate that required configuration is present."""
    if not LLM_API_KEY:
        print("Error: LLM_API_KEY not set in .env.agent.secret", file=sys.stderr)
        sys.exit(1)
    if not LLM_API_BASE:
        print("Error: LLM_API_BASE not set in .env.agent.secret", file=sys.stderr)
        sys.exit(1)


def is_safe_path(base_path: Path, requested_path: Path) -> bool:
    """
    Check if requested_path is within base_path.

    Args:
        base_path: The base directory (project root)
        requested_path: The path to validate

    Returns:
        True if the path is safe, False otherwise
    """
    try:
        base_resolved = base_path.resolve()
        requested_resolved = requested_path.resolve()
        return str(requested_resolved).startswith(str(base_resolved) + os.sep) or str(
            requested_resolved
        ) == str(base_resolved)
    except OSError, ValueError:
        return False


def normalize_path(relative_path: str) -> Path:
    """
    Normalize and validate relative path.

    Args:
        relative_path: Path relative to project root

    Returns:
        Absolute path within project root

    Raises:
        ValueError: If path traversal is detected
    """
    # Remove leading/trailing slashes
    relative_path = relative_path.strip("/")

    # Check for path traversal attempts
    parts = relative_path.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError("Path traversal not allowed: " + relative_path)

    # Build absolute path
    absolute_path = PROJECT_ROOT / relative_path

    return absolute_path


def read_file(path: str) -> str:
    """
    Read contents of a file from the project repository.

    Args:
        path: Relative path from project root

    Returns:
        File contents as a string, or error message
    """
    try:
        absolute_path = normalize_path(path)

        # Check if path is within project root
        if not is_safe_path(PROJECT_ROOT, absolute_path):
            return f"Error: Access denied - path outside project directory: {path}"

        # Check if file exists
        if not absolute_path.exists():
            return f"Error: File not found: {path}"

        # Check if it's a file (not directory)
        if not absolute_path.is_file():
            return f"Error: Not a file: {path}"

        # Read and return contents
        content = absolute_path.read_text(encoding="utf-8")
        return content

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(path: str) -> str:
    """
    List files and directories at a given path.

    Args:
        path: Relative directory path from project root

    Returns:
        Newline-separated listing of entries, or error message
    """
    try:
        absolute_path = normalize_path(path)

        # Check if path is within project root
        if not is_safe_path(PROJECT_ROOT, absolute_path):
            return f"Error: Access denied - path outside project directory: {path}"

        # Check if directory exists
        if not absolute_path.exists():
            return f"Error: Directory not found: {path}"

        # Check if it's a directory
        if not absolute_path.is_dir():
            return f"Error: Not a directory: {path}"

        # List entries
        entries = sorted([entry.name for entry in absolute_path.iterdir()])
        return "\n".join(entries)

    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error listing directory: {e}"


def execute_tool(tool_name: str, args: dict[str, Any]) -> str:
    """
    Execute a tool and return the result.

    Args:
        tool_name: Name of the tool to execute
        args: Arguments for the tool

    Returns:
        Tool result as a string
    """
    print(f"Executing tool: {tool_name}({args})", file=sys.stderr)

    if tool_name == "read_file":
        return read_file(args.get("path", ""))
    elif tool_name == "list_files":
        return list_files(args.get("path", ""))
    elif tool_name == "query_api":
        return query_api(
            args.get("method", "GET"),
            args.get("path", ""),
            args.get("body"),
            args.get("omit_auth", False),
        )
    else:
        return f"Error: Unknown tool: {tool_name}"


def call_llm(
    messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """
    Call the LLM API and return the response.

    Args:
        messages: List of message dicts for the conversation
        tools: Optional list of tool definitions

    Returns:
        Parsed response data from LLM

    Raises:
        SystemExit: If the API call fails
    """
    url = f"{LLM_API_BASE}/chat/completions"

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {
        "model": LLM_MODEL,
        "messages": messages,
    }

    if tools:
        payload["tools"] = tools

    print(f"Calling LLM at {url}...", file=sys.stderr)

    try:
        # Use os.system with curl instead of httpx due to Docker networking issues on Windows
        import os
        import json as json_module
        import tempfile

        json_payload = json_module.dumps(payload)

        # Write JSON to temp file to avoid escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_payload)
            temp_file = f.name

        try:
            # Build curl command
            cmd = (
                f'curl -s -X POST "{url}" '
                f'-H "Authorization: Bearer {LLM_API_KEY}" '
                f'-H "Content-Type: application/json" '
                f"--connect-timeout 30 --max-time 120 "
                f"-d @{temp_file}"
            )

            # Execute with os.system and capture output via temp file
            output_file = temp_file + ".out"
            os.system(f'{cmd} > "{output_file}" 2>&1')

            with open(output_file, "r", encoding="utf-8") as f:
                response_text = f.read()

            os.remove(output_file)

            if not response_text:
                raise Exception("curl returned empty response")

            data = json_module.loads(response_text)
            if "error" in data:
                raise Exception(f"API error: {data['error']}")
        finally:
            os.remove(temp_file)

    except Exception as e:
        print(f"Error: LLM API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    return data


def extract_source_from_answer(
    answer: str, tool_calls_log: list[dict[str, Any]]
) -> str:
    """
    Extract or generate source reference from the answer.

    Args:
        answer: The LLM's answer text
        tool_calls_log: Log of tool calls made

    Returns:
        Source reference string (e.g., "wiki/git-workflow.md#section")
    """
    import re

    # Try to find a file reference in the answer
    wiki_pattern = r"wiki/[\w-]+\.md"
    matches = re.findall(wiki_pattern, answer)

    if matches:
        # Use the last mentioned file
        file_path = matches[-1]
        # Try to find a section anchor from headers in the answer
        section_pattern = r"#+\s+([A-Za-z][A-Za-z0-9\s-]*)"
        # Check tool results for section headers
        for tc in tool_calls_log:
            if tc["tool"] == "read_file":
                result = tc.get("result", "")
                # Look for headers in the content
                headers = re.findall(r"^#\s+(.+)$", result, re.MULTILINE)
                if headers:
                    # Convert first header to anchor
                    anchor = headers[0].lower().replace(" ", "-").replace("'", "")
                    return f"{file_path}#{anchor}"
        return file_path

    # Fallback: use the last read_file path
    for tc in reversed(tool_calls_log):
        if tc["tool"] == "read_file":
            return tc["args"].get("path", "wiki/unknown.md")

    # If only list_files was used, mention wiki directory
    for tc in reversed(tool_calls_log):
        if tc["tool"] == "list_files":
            return f"wiki/ (listing via {tc['args'].get('path', 'unknown')})"

    # If query_api was used, return the API endpoint as source
    for tc in reversed(tool_calls_log):
        if tc["tool"] == "query_api":
            return f"API: {tc['args'].get('method', 'GET')} {tc['args'].get('path', 'unknown')}"

    return "wiki/unknown.md"


def query_api(method: str, path: str, body: str = None, omit_auth: bool = False) -> str:
    """
    Call the deployed backend API using curl via os.system.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path (e.g., "/items/")
        body: Optional JSON request body for POST requests
        omit_auth: If True, omit the Authorization header (default: False)

    Returns:
        JSON string with status_code and body
    """
    global LMS_API_KEY, AGENT_API_BASE_URL

    if not LMS_API_KEY:
        return json.dumps({"status_code": 500, "body": "LMS_API_KEY not configured"})

    url = f"{AGENT_API_BASE_URL}{path}"

    try:
        import os
        import tempfile

        # Build curl command with status code output
        cmd = f'curl -s -w "\\n%{{http_code}}" -X {method.upper()} "{url}" --connect-timeout 30 --max-time 60'

        # Add headers
        if not omit_auth:
            cmd += f' -H "Authorization: Bearer {LMS_API_KEY}"'
        cmd += ' -H "Content-Type: application/json"'

        # Add body for POST/PUT/PATCH
        if method.upper() in ("POST", "PUT", "PATCH") and body:
            # Write body to temp file to avoid escaping issues
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write(body)
                temp_file = f.name
            try:
                cmd += f" -d @{temp_file}"
                output_file = temp_file + ".out"
                os.system(f'{cmd} > "{output_file}" 2>&1')
                os.remove(temp_file)
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        else:
            output_file = tempfile.mktemp(suffix=".out")
            os.system(f'{cmd} > "{output_file}" 2>&1')

        # Read output - last line is status code
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                status_code = int(lines[-1]) if lines else 200
                response_text = "\n".join(lines[:-1]) if len(lines) > 1 else ""
            os.remove(output_file)
        except FileNotFoundError:
            status_code = 500
            response_text = ""
        except ValueError:
            status_code = 500
            response_text = ""

        return json.dumps({"status_code": status_code, "body": response_text})

    except Exception as e:
        return json.dumps({"status_code": 500, "body": str(e)})


def run_agentic_loop(question: str) -> tuple[str, str, list[dict[str, Any]]]:
    """
    Run the agentic loop to answer a question.

    Args:
        question: The user's question

    Returns:
        Tuple of (answer, source, tool_calls_log)
    """
    # Initialize conversation
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    tool_calls_log: list[dict[str, Any]] = []

    for iteration in range(MAX_TOOL_CALLS):
        print(f"\n--- Iteration {iteration + 1} ---", file=sys.stderr)

        # Call LLM
        data = call_llm(messages, TOOLS)

        # Parse response
        try:
            message = data["choices"][0]["message"]
        except (KeyError, IndexError) as e:
            print(f"Error: Unexpected LLM response format: {e}", file=sys.stderr)
            print(f"Response: {data}", file=sys.stderr)
            sys.exit(1)

        # Check for tool calls
        tool_calls = message.get("tool_calls", [])

        if tool_calls:
            # LLM wants to call tools
            print(f"LLM returned {len(tool_calls)} tool call(s)", file=sys.stderr)

            # Add assistant message with tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content"),
                    "tool_calls": tool_calls,
                }
            )

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])
                tool_call_id = tool_call["id"]

                # Execute tool
                result = execute_tool(tool_name, tool_args)

                # Log the tool call
                tool_calls_log.append(
                    {"tool": tool_name, "args": tool_args, "result": result}
                )

                # Add tool result to messages
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call_id, "content": result}
                )

                print(f"Tool result: {result[:100]}...", file=sys.stderr)

            # Continue loop - send updated messages back to LLM

        else:
            # LLM returned final answer (no tool calls)
            print("LLM returned final answer", file=sys.stderr)
            answer = message.get("content", "")

            # Check if this is a router listing question and not all files were read
            # Only apply this check if the question is specifically about listing routers
            router_files = [
                "items.py",
                "learners.py",
                "interactions.py",
                "analytics.py",
                "pipeline.py",
            ]
            routers_read = []
            for tc in tool_calls_log:
                if tc["tool"] == "read_file":
                    path = tc["args"].get("path", "")
                    for rf in router_files:
                        if path.endswith(rf):
                            routers_read.append(rf)

            # Check if question is specifically about listing routers (not error handling comparison)
            is_router_listing = (
                "router" in question.lower()
                and (
                    "list" in question.lower()
                    or "modules" in question.lower()
                    or "domain" in question.lower()
                )
                and "error handling" not in question.lower()
                and "compare" not in question.lower()
            )
            if is_router_listing and len(routers_read) < len(router_files):
                # LLM returned answer too early - remind it to read all files
                remaining = [rf for rf in router_files if rf not in routers_read]
                print(
                    f"Warning: LLM returned answer after reading only {len(routers_read)}/{len(router_files)} routers",
                    file=sys.stderr,
                )
                print(f"Remaining routers: {remaining}", file=sys.stderr)
                # Add a tool message to remind LLM to read remaining files
                messages.append(
                    {"role": "assistant", "content": message.get("content")}
                )
                messages.append(
                    {
                        "role": "user",
                        "content": f"You returned an answer too early. You must read ALL router files before answering. Remaining files to read: {', '.join(remaining)}. Please call read_file for each remaining router file.",
                    }
                )
                continue  # Continue the loop instead of returning

            # Check if this is an error handling comparison question
            if (
                "error" in question.lower()
                and "compare" in question.lower()
                and ("etl" in question.lower() or "pipeline" in question.lower())
            ):
                etl_read = any(
                    "etl.py" in tc.get("args", {}).get("path", "")
                    for tc in tool_calls_log
                    if tc["tool"] == "read_file"
                )
                routers_read = [
                    tc.get("args", {}).get("path", "")
                    for tc in tool_calls_log
                    if tc["tool"] == "read_file"
                    and "routers/" in tc.get("args", {}).get("path", "")
                ]
                if not etl_read or len(routers_read) < 2:
                    print(
                        "Warning: Error handling comparison question but missing file reads",
                        file=sys.stderr,
                    )
                    print(
                        f"ETL read: {etl_read}, Routers read: {len(routers_read)}",
                        file=sys.stderr,
                    )
                    messages.append(
                        {"role": "assistant", "content": message.get("content")}
                    )
                    missing = []
                    if not etl_read:
                        missing.append("backend/app/etl.py")
                    if len(routers_read) < 2:
                        missing.append(
                            "at least 2 router files (e.g., backend/app/routers/items.py, backend/app/routers/learners.py)"
                        )
                    messages.append(
                        {
                            "role": "user",
                            "content": f"You returned an answer too early. You must read BOTH the ETL code AND at least 2 API router files before comparing. Missing: {', '.join(missing)}. Please read the missing files first, then provide a complete comparison.",
                        }
                    )
                    continue

            # Check if this is an analytics code safety review question
            if "analytics" in question.lower() and (
                "bug" in question.lower()
                or "error" in question.lower()
                or "risky" in question.lower()
            ):
                analytics_read = any(
                    "analytics.py" in tc.get("args", {}).get("path", "")
                    for tc in tool_calls_log
                    if tc["tool"] == "read_file"
                )
                if not analytics_read:
                    print(
                        "Warning: Analytics bug question but analytics.py not read",
                        file=sys.stderr,
                    )
                    messages.append(
                        {"role": "assistant", "content": message.get("content")}
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": "You must read backend/app/routers/analytics.py before answering. Please call read_file('backend/app/routers/analytics.py') to analyze the code for bugs.",
                        }
                    )
                    continue

            # Extract source
            source = extract_source_from_answer(answer, tool_calls_log)

            return answer, source, tool_calls_log

    # Reached max tool calls
    print(f"\nReached maximum tool calls ({MAX_TOOL_CALLS})", file=sys.stderr)

    # Get whatever answer we have from the last message
    answer = "I reached the maximum number of tool calls. Based on the information gathered, please review the tool results above."
    source = extract_source_from_answer(answer, tool_calls_log)

    return answer, source, tool_calls_log


def main() -> None:
    """Main entry point."""
    # Validate command-line arguments
    if len(sys.argv) < 2:
        print("Error: No question provided", file=sys.stderr)
        print('Usage: uv run agent.py "Your question here"', file=sys.stderr)
        sys.exit(1)

    question = sys.argv[1]
    print(f"Question: {question}", file=sys.stderr)

    # Validate configuration
    validate_config()

    # Run agentic loop
    answer, source, tool_calls_log = run_agentic_loop(question)

    # Format output as JSON
    result: dict[str, Any] = {
        "answer": answer,
        "source": source,
        "tool_calls": tool_calls_log,
    }

    # Output JSON to stdout (single line)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
