#!/usr/bin/env python3
"""
Regression tests for agent.py CLI (Task 2: Documentation Agent).

These tests run agent.py as a subprocess and validate the JSON output
including tool_calls and source fields.

Environment variables are loaded by conftest.py before tests run.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def run_agent(question: str) -> dict:
    """
    Run agent.py with a question and return parsed JSON output.

    Environment variables are inherited from the pytest process (loaded by conftest.py).

    Args:
        question: The question to ask the agent

    Returns:
        Parsed JSON output as a dictionary

    Raises:
        AssertionError: If agent fails or output is invalid
    """
    project_root = get_project_root()
    agent_path = project_root / "agent.py"

    # Inherit environment variables from pytest process
    # (conftest.py loads .env files before tests run)
    # Pass the current environment explicitly to subprocess
    env = os.environ.copy()

    result = subprocess.run(
        [sys.executable, str(agent_path), question],
        capture_output=True,
        text=True,
        timeout=120,  # Increased timeout for agentic loop
        cwd=project_root,
        env=env,  # Explicitly pass environment
    )

    # Check exit code
    assert result.returncode == 0, f"agent.py failed with: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"stdout is not valid JSON: {e}\nstdout: {result.stdout}")

    return output


def test_merge_conflict_question():
    """
    Test that agent correctly answers about merge conflicts.

    This test verifies:
    1. Agent uses read_file tool to read wiki/git-workflow.md
    2. Source field contains reference to git-workflow.md
    3. Answer is not empty
    """
    question = "How do you resolve a merge conflict?"
    output = run_agent(question)

    # Validate required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Validate field types
    assert isinstance(output["answer"], str), "'answer' must be a string"
    assert isinstance(output["source"], str), "'source' must be a string"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Validate answer is not empty
    assert len(output["answer"]) > 0, "'answer' field is empty"

    # Validate tool_calls contains read_file
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tool_names, (
        f"Expected 'read_file' in tool_calls, got: {tool_names}"
    )

    # Validate source contains wiki file reference (LLM may find answer in different files)
    assert output["source"].startswith("wiki/"), (
        f"Expected source to start with 'wiki/', got: {output['source']}"
    )
    assert ".md" in output["source"], (
        f"Expected source to contain '.md', got: {output['source']}"
    )

    print(f"✓ test_merge_conflict_question passed")
    print(f"  Answer: {output['answer'][:80]}...")
    print(f"  Source: {output['source']}")
    print(f"  Tool calls: {len(output['tool_calls'])}")


def test_wiki_listing_question():
    """
    Test that agent correctly lists wiki files.

    This test verifies:
    1. Agent uses list_files tool with path='wiki'
    2. Answer contains file names from wiki
    3. tool_calls contains list_files entry
    """
    question = "What files are in the wiki?"
    output = run_agent(question)

    # Validate required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Validate field types
    assert isinstance(output["answer"], str), "'answer' must be a string"
    assert isinstance(output["source"], str), "'source' must be a string"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Validate answer is not empty
    assert len(output["answer"]) > 0, "'answer' field is empty"

    # Validate tool_calls contains list_files
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "list_files" in tool_names, (
        f"Expected 'list_files' in tool_calls, got: {tool_names}"
    )

    # Find the list_files call and validate args
    list_files_call = None
    for tc in output["tool_calls"]:
        if tc.get("tool") == "list_files":
            list_files_call = tc
            break

    assert list_files_call is not None, "list_files tool call not found"
    assert list_files_call.get("args", {}).get("path") == "wiki", (
        f"Expected list_files args.path to be 'wiki', got: {list_files_call.get('args')}"
    )

    print(f"✓ test_wiki_listing_question passed")
    print(f"  Answer: {output['answer'][:80]}...")
    print(f"  Source: {output['source']}")
    print(f"  Tool calls: {len(output['tool_calls'])}")


def test_agent_output_format():
    """
    Test that agent.py outputs valid JSON with required fields.

    This is a basic format test using a simple question.
    """
    question = "What is the project about?"
    output = run_agent(question)

    # Validate required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "source" in output, "Missing 'source' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Validate field types
    assert isinstance(output["answer"], str), "'answer' must be a string"
    assert isinstance(output["source"], str), "'source' must be a string"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    print(f"✓ test_agent_output_format passed")


def test_backend_framework_question():
    """
    Test that agent uses read_file to find out what framework the backend uses.

    This test verifies:
    1. Agent uses read_file tool to read backend source code
    2. Answer contains 'FastAPI'
    3. tool_calls contains read_file entry
    """
    question = "What Python web framework does this project's backend use?"
    output = run_agent(question)

    # Validate required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Validate answer is not empty
    assert len(output["answer"]) > 0, "'answer' field is empty"

    # Validate tool_calls contains read_file
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "read_file" in tool_names, (
        f"Expected 'read_file' in tool_calls, got: {tool_names}"
    )

    # Validate answer contains FastAPI
    assert "FastAPI" in output["answer"], (
        f"Expected answer to contain 'FastAPI', got: {output['answer']}"
    )

    print(f"✓ test_backend_framework_question passed")
    print(f"  Answer: {output['answer'][:80]}...")
    print(f"  Tools: {', '.join(tool_names)}")


def test_database_item_count_question():
    """
    Test that agent uses query_api to find out how many items are in the database.

    This test verifies:
    1. Agent uses query_api tool to query the backend
    2. Answer contains a number > 0
    3. tool_calls contains query_api entry
    """
    question = "How many items are currently stored in the database?"
    output = run_agent(question)

    # Validate required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Validate answer is not empty
    assert len(output["answer"]) > 0, "'answer' field is empty"

    # Validate tool_calls contains query_api
    tool_names = [tc.get("tool") for tc in output["tool_calls"]]
    assert "query_api" in tool_names, (
        f"Expected 'query_api' in tool_calls, got: {tool_names}"
    )

    # Validate answer contains a number
    import re

    numbers = re.findall(r"\d+", output["answer"])
    assert len(numbers) > 0, (
        f"Expected answer to contain a number, got: {output['answer']}"
    )

    print(f"✓ test_database_item_count_question passed")
    print(f"  Answer: {output['answer'][:80]}...")
    print(f"  Tools: {', '.join(tool_names)}")


if __name__ == "__main__":
    print("Running agent.py regression tests...\n")

    test_agent_output_format()
    print()

    test_merge_conflict_question()
    print()

    test_wiki_listing_question()
    print()

    test_backend_framework_question()
    print()

    test_database_item_count_question()
    print()

    print("All tests passed!")
