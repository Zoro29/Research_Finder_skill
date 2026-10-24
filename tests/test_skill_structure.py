import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).parents[1]
SKILL = ROOT / "research-agent"

class SkillStructureTests(unittest.TestCase):
    def test_required_skill_files_and_frontmatter(self):
        required = [
            "SKILL.md",
            "scripts/research.py",
            "scripts/validate_skill.py",
            "references/QUERY_SYNTAX.md",
            "references/RESEARCH_WORKFLOW.md",
            "references/OUTPUT_FORMATS.md",
            "assets/templates/outreach_template.md",
        ]
        for relative in required:
            self.assertTrue((SKILL / relative).is_file(), relative)
        text = (SKILL / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---\n", 2)[1]
        self.assertIsNotNone(re.search(r"^name:\s*research-agent$", frontmatter, re.MULTILINE))
        self.assertLess(len(text.splitlines()), 500)

    def test_custom_validator(self):
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts/validate_skill.py")],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_direct_script_help(self):
        result = subprocess.run(
            [sys.executable, str(SKILL / "scripts/research.py"), "--help"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("search", result.stdout)

if __name__ == "__main__":
    unittest.main()
