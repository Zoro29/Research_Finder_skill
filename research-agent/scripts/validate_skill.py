#!/usr/bin/env python3
"""Small dependency-light structural validator for this skill directory."""
from __future__ import annotations
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = ("SKILL.md", "references/QUERY_SYNTAX.md",
            "references/RESEARCH_WORKFLOW.md", "references/OUTPUT_FORMATS.md",
            "assets/templates/outreach_template.md", "scripts/research.py")

def main() -> int:
    errors = [f"missing: {path}" for path in REQUIRED if not (ROOT / path).is_file()]
    skill = ROOT / "SKILL.md"
    text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    if not text.startswith("---\n"):
        errors.append("SKILL.md must begin with YAML frontmatter")
    frontmatter = text.split("---\n", 2)[1] if text.startswith("---\n") else ""
    name = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    description = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if not name or name.group(1).strip() != "research-agent":
        errors.append("frontmatter name must be research-agent")
    if not description or not description.group(1).strip():
        errors.append("frontmatter description is required")
    if len(text.splitlines()) >= 500:
        errors.append("SKILL.md must contain fewer than 500 lines")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Skill structure and required frontmatter are valid.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
