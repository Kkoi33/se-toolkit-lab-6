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
MAX_TOOL_CALLS = 10

# System prompt for the agent
SYSTEM_PROMPT = """You are a system agent that answers questions about a software engineering project.

You have access to three tools:
- list_files: List files and directories at a given path
- read_file: Read contents of a file from the project repository
- query_api: Call the deployed backend API to get live data

Tool selection guide:
- Use list_files to discover what files exist (e.g., in wiki/ or backend/)
- Use read_file to read documentation, source code, or configuration files
- Use query_api to query live system data, check API responses, or get status codes

When to use query_api:
- Questions about current database state (e.g., "How many items...?")
- Questions about API behavior (e.g., "What status code does /items/ return?")
- Questions that require live data, not static documentation

When to use read_file:
- Questions about the project wiki
- Questions about source code (e.g., "What framework does the backend use?")
- Questions about configuration (e.g., docker-compose.yml, Dockerfile)

Workflow:
1. Analyze the question to determine which tool(s) to use
2. Use list_files if you need to discover file structure
3. Use read_file to read relevant files and find the answer
4. Use query_api to get live data from the backend
5. For bug diagnosis: use query_api to see the error, then read_file to find the bug

Important:
- Include the source field when referencing files (e.g., "wiki/git-workflow.md#section")
- For API queries, you can mention the endpoint as source (e.g., "API: GET /items/")
- Do not make up information — only use content from actual files or API responses
- If you cannot find the answer, say so honestly
- Section anchors are lowercase with hyphens instead of spaces
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
            "description": "Call the deployed backend API to get live data, check status codes, or query database",
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
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        print("Error: LLM API request timed out (>60 seconds)", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"Error: LLM API returned HTTP {e.response.status_code}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"Error: Failed to connect to LLM API: {e}", file=sys.stderr)
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


def query_api(method: str, path: str, body: str = None) -> str:
    """
    Call the deployed backend API.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path (e.g., "/items/")
        body: Optional JSON request body for POST requests

    Returns:
        JSON string with status_code and body
    """
    global LMS_API_KEY, AGENT_API_BASE_URL

    if not LMS_API_KEY:
        return json.dumps({"status_code": 500, "body": "LMS_API_KEY not configured"})

    url = f"{AGENT_API_BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {LMS_API_KEY}"}

    try:
        with httpx.Client(timeout=30.0) as client:
            if method.upper() == "GET":
                response = client.get(url, headers=headers)
            elif method.upper() == "POST":
                response = client.post(
                    url, headers=headers, json=json.loads(body) if body else None
                )
            else:
                return json.dumps(
                    {"status_code": 400, "body": f"Unsupported method: {method}"}
                )

            return json.dumps(
                {"status_code": response.status_code, "body": response.text}
            )
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
