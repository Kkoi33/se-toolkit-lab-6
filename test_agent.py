#!/usr/bin/env python3
"""
Regression tests for agent.py CLI (Task 2: Documentation Agent).

These tests run agent.py as a subprocess and validate the JSON output
including tool_calls and source fields.
"""

import json
import subprocess
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent


def run_agent(question: str) -> dict:
    """
    Run agent.py with a question and return parsed JSON output.

    Args:
        question: The question to ask the agent

    Returns:
        Parsed JSON output as a dictionary

    Raises:
        AssertionError: If agent fails or output is invalid
    """
    project_root = get_project_root()
    agent_path = project_root / "agent.py"

    result = subprocess.run(
        ["uv", "run", str(agent_path), question],
        capture_output=True,
        text=True,
        timeout=120,  # Increased timeout for agentic loop
        cwd=project_root,
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


if __name__ == "__main__":
    print("Running agent.py regression tests...\n")

    test_agent_output_format()
    print()

    test_merge_conflict_question()
    print()

    test_wiki_listing_question()
    print()

    print("All tests passed!")
