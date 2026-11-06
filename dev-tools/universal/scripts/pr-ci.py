#!/usr/bin/env python3
"""Failing CI checks on a PR, with log tails. Skips checks listed in workspace/ignore-checks.txt. Read-only.

Usage: pr-ci.py <pr-number> [-R owner/repo] [--tails N]
"""
import argparse
import fnmatch
import re
from _lib import require_config, APP, WORKSPACE, code, gh_json, fail, out, read_list
require_config()

p = argparse.ArgumentParser()
p.add_argument("pr", type=int)
p.add_argument("-R", "--repo")
p.add_argument("--tails", type=int, default=3, help="max number of log tails to fetch")
a = p.parse_args()

repo_args = ["-R", a.repo] if a.repo else []
ignore = read_list(WORKSPACE / "ignore-checks.txt")
try:
    checks = gh_json("pr", "checks", str(a.pr), *repo_args, "--json", "name,state,bucket,link,workflow", cwd=APP)
except RuntimeError as e:
    # gh exits non-zero when checks fail but still prints JSON; retry without check
    rc, stdout, stderr = code(["gh", "pr", "checks", str(a.pr), *repo_args, "--json", "name,state,bucket,link,workflow"], cwd=APP)
    if not stdout:
        fail(stderr or str(e))
    import json
    checks = json.loads(stdout)

summary = {"pass": 0, "fail": 0, "pending": 0, "skipping": 0, "cancel": 0, "ignored": 0}
failing = []
for c in checks:
    if any(fnmatch.fnmatch(c["name"], pat) for pat in ignore):
        summary["ignored"] += 1
        continue
    summary[c["bucket"]] = summary.get(c["bucket"], 0) + 1
    if c["bucket"] in ("fail", "cancel"):
        failing.append({"name": c["name"], "workflow": c.get("workflow"), "state": c["state"], "link": c["link"]})

for f in failing[: a.tails]:
    m = re.search(r"/actions/runs/(\d+)/job/(\d+)", f["link"] or "")
    if not m:
        continue
    rc, log, _ = code(["gh", "run", "view", m.group(1), "--job", m.group(2), "--log-failed", *repo_args], cwd=APP)
    if rc == 0 and log:
        f["log_tail"] = "\n".join(log.splitlines()[-40:])

out({"ok": True, "pr": a.pr, "summary": summary, "failing": failing, "ignore_list": ignore})
