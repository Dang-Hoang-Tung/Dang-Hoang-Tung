#!/usr/bin/env python3
"""Start buddy's day: today's log (with open items carried over) and the list of projects.
Read-only unless --apply, which creates today's log if it's missing.

Usage: buddy-start.py [--apply]
"""
import datetime
import pathlib
import re
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import AGENT_FILES, apply_flag, out

apply = apply_flag()
logs = AGENT_FILES / "shared" / "buddy"
today = datetime.date.today().isoformat()
today_log = logs / f"{today}.md"


def section(text, title):
    m = re.search(rf"^## {title}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return [l for l in (m.group(1).splitlines() if m else []) if l.strip().startswith("-")]


previous = sorted(p for p in logs.glob("????-??-??.md") if p.name != today_log.name) if logs.exists() else []
latest = previous[-1] if previous else None
carried = section(latest.read_text(), "Open items") if latest else []

projects = []
for readme in sorted((AGENT_FILES / "projects").glob("*/README.md")):
    fields = dict(re.findall(r"^(Goal|Size|Lead|Status): (.*)$", readme.read_text(), re.M))
    projects.append({"slug": readme.parent.name, **{k.lower(): v for k, v in fields.items()}})
active = [p for p in projects if p.get("status", "").lower() not in ("done", "closed")]

ideas_file = logs / "ideas.md"
ideas = len([l for l in ideas_file.read_text().splitlines() if l.strip().startswith("-")]) if ideas_file.exists() else 0

created = False
if apply and not today_log.exists():
    logs.mkdir(parents=True, exist_ok=True)
    project_lines = [f"- {p['slug']} ({p.get('lead', '?')}): {p.get('status', '?')}" for p in active]
    today_log.write_text(f"# {today}\n## Open items\n" + "\n".join(carried) + "\n## Projects\n" + "\n".join(project_lines) + "\n## Log\n")
    created = True

out({"ok": True, "applied": apply, "today_log": str(today_log), "exists": today_log.exists(), "created": created,
     "previous_log": str(latest) if latest else None, "open_items": carried, "active_projects": active, "ideas": ideas})
