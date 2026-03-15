#!/usr/bin/env python3
"""
Regression test for agent.py CLI.

This test runs agent.py as a subprocess and validates the JSON output.
"""

import json
import subprocess
from pathlib import Path


def test_agent_output_format():
    """
    Test that agent.py outputs valid JSON with required fields.

    This test:
    1. Runs agent.py as a subprocess with a simple question
    2. Parses stdout as JSON
    3. Validates that 'answer' and 'tool_calls' fields exist
    """
    # Path to agent.py in project root
    project_root = Path(__file__).parent
    agent_path = project_root / "agent.py"

    # Run agent.py with a simple question
    result = subprocess.run(
        ["uv", "run", str(agent_path), "What is 2+2?"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=project_root,
    )

    # Check exit code
    assert result.returncode == 0, f"agent.py failed with: {result.stderr}"

    # Parse stdout as JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise AssertionError(f"stdout is not valid JSON: {e}\nstdout: {result.stdout}")

    # Validate required fields exist
    assert "answer" in output, "Missing 'answer' field in output"
    assert "tool_calls" in output, "Missing 'tool_calls' field in output"

    # Validate field types
    assert isinstance(output["answer"], str), "'answer' must be a string"
    assert isinstance(output["tool_calls"], list), "'tool_calls' must be an array"

    # Validate answer is not empty
    assert len(output["answer"]) > 0, "'answer' field is empty"


if __name__ == "__main__":
    test_agent_output_format()
    print("All tests passed!")
