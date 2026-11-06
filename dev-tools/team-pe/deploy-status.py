#!/usr/bin/env python3
"""Status of the latest deploy run for a branch (workflow and URL pattern from workspace/config.json). Read-only. One call per check-in.

Usage: deploy-status.py <branch> [--stage <environment name>]
"""
import argparse
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import require_config, APP, CONFIG, fail, gh_json, out
require_config()

p = argparse.ArgumentParser()
p.add_argument("branch")
p.add_argument("--stage")
a = p.parse_args()

try:
    runs = gh_json("run", "list", "--workflow", CONFIG["deploy"]["workflow"], "--branch", a.branch, "--limit", "1",
                   "--json", "databaseId,status,conclusion,url,createdAt,updatedAt", cwd=APP)
except RuntimeError as e:
    fail(str(e))
if not runs:
    out({"ok": True, "state": "not_started", "branch": a.branch})
    sys.exit(0)
r = runs[0]
state = r["status"] if r["status"] != "completed" else ("success" if r["conclusion"] == "success" else "failed")
result = {"ok": True, "state": state, "conclusion": r["conclusion"], "run": r["url"], "started": r["createdAt"], "updated": r["updatedAt"]}
if a.stage:
    d = CONFIG["deploy"]
    result["urls"] = {label: d["url"].format(label=label, stage=a.stage) for label in d["labels"]}
out(result)
