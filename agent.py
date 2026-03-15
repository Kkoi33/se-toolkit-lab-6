#!/usr/bin/env python3
"""
Agent CLI — connects to an LLM and answers questions.

Usage:
    uv run agent.py "Your question here"

Output:
    JSON to stdout: {"answer": "...", "tool_calls": []}
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

# Configuration from environment
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_API_BASE = os.getenv("LLM_API_BASE")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3-coder-plus")


def validate_config() -> None:
    """Validate that required configuration is present."""
    if not LLM_API_KEY:
        print("Error: LLM_API_KEY not set in .env.agent.secret", file=sys.stderr)
        sys.exit(1)
    if not LLM_API_BASE:
        print("Error: LLM_API_BASE not set in .env.agent.secret", file=sys.stderr)
        sys.exit(1)


def call_llm(question: str) -> str:
    """
    Call the LLM API and return the answer.

    Args:
        question: The user's question.

    Returns:
        The LLM's answer as a string.

    Raises:
        SystemExit: If the API call fails.
    """
    url = f"{LLM_API_BASE}/chat/completions"

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {
                "role": "user",
                "content": question,
            }
        ],
    }

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

    # Parse the response
    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"Error: Unexpected LLM response format: {e}", file=sys.stderr)
        print(f"Response: {data}", file=sys.stderr)
        sys.exit(1)

    print(f"LLM responded successfully.", file=sys.stderr)
    return answer


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

    # Call LLM and get answer
    answer = call_llm(question)

    # Format output as JSON
    result: dict[str, Any] = {
        "answer": answer,
        "tool_calls": [],
    }

    # Output JSON to stdout (single line)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
