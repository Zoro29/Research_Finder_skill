#!/usr/bin/env python3
"""Executable skill entry point; delegates to the project's real CLI."""
from __future__ import annotations
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_finder.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
