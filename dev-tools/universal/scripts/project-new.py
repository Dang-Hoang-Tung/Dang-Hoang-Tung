#!/usr/bin/env python3
"""Create a project bank. Dry run unless --apply.

Usage: project-new.py <slug> --lead <session> --size Small|Medium|Large [--goal "<one line>"] [--apply]
"""
import argparse
import sys
from _lib import AGENT_FILES, apply_flag, fail, out

apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("slug")
p.add_argument("--lead", required=True)
p.add_argument("--size", required=True, choices=["Small", "Medium", "Large"])
p.add_argument("--goal", default="<one line>")
a = p.parse_args()

bank = AGENT_FILES / "projects" / a.slug
if bank.exists():
    fail(f"{bank} already exists")

files = {
    "README.md": f"""# {a.slug}

Goal: {a.goal}
Size: {a.size}
Lead: {a.lead}
Status: planning

## Helpers
| Helper | Agent ID | State |
|--------|----------|-------|

## Branches

## Links
- Tracker:
- Docs:
- Design:
""",
    "project-doc.md": f"# {a.slug}\n\n## Project brief\n\n## Design review\n\n## Technical design\n\n## PR plan\n",
    "decisions.md": f"# Decisions: {a.slug}\n\n<!-- - YYYY-MM-DD <decision> — <why> (<who>) -->\n",
    "followups.md": f"# Follow-ups: {a.slug}\n",
}
dirs = ["handoffs", "notes"]

if apply:
    bank.mkdir(parents=True)
    for d in dirs:
        (bank / d).mkdir()
    for name, text in files.items():
        (bank / name).write_text(text)
out({"ok": True, "applied": apply, "bank": str(bank), "files": list(files) + [d + "/" for d in dirs]})
