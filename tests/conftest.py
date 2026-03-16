#!/usr/bin/env python3
"""
Pytest configuration and fixtures for agent tests.
Loads environment variables before running tests.
"""

import os
import sys
from pathlib import Path


def load_env_file(filepath: str) -> None:
    """Load environment variables from a .env file."""
    path = Path(filepath)
    if not path.exists():
        print(f"conftest.py: {filepath} does not exist", file=sys.stderr)
        return
    print(f"conftest.py: Loading {filepath}", file=sys.stderr)
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            print(f"conftest.py: Loaded {key}", file=sys.stderr)


# Get project root (parent of tests directory)
project_root = Path(__file__).parent.parent

# Load environment variables before any tests run
load_env_file(str(project_root / ".env.agent.secret"))
load_env_file(str(project_root / ".env.docker.secret"))

# Verify that required variables are loaded
print(
    f"conftest.py: LLM_API_KEY loaded: {'LLM_API_KEY' in os.environ}", file=sys.stderr
)
print(
    f"conftest.py: LLM_API_BASE loaded: {'LLM_API_BASE' in os.environ}", file=sys.stderr
)
print(f"conftest.py: LLM_MODEL loaded: {'LLM_MODEL' in os.environ}", file=sys.stderr)
