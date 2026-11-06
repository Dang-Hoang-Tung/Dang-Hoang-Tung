#!/usr/bin/env python3
"""Check branches before integrating them. Read-only (runs git fetch).

Usage: integrate-check.py <branch> [<branch> ...] [--repo PATH]
Per branch: commits behind main, conflicts with main, changed files, new migrations (and whether
they're already on main). Across branches: shared files and migration clashes.
"""
import argparse
import itertools
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import require_config, APP, CONFIG, code, fail, git, out
require_config()

MIGRATIONS = CONFIG["migrations_dir"]
SUM_FILE = CONFIG.get("migrations_sum_file")

p = argparse.ArgumentParser()
p.add_argument("branches", nargs="+")
p.add_argument("--repo", default=str(APP))
a = p.parse_args()
repo = pathlib.Path(a.repo)

try:
    git("fetch", "--quiet", "origin", repo=repo)
except RuntimeError as e:
    fail(f"git fetch failed: {e}")

report, files_by_branch, new_migrations = [], {}, {}
for b in a.branches:
    ref = f"origin/{b}"
    rc, _, _ = code(["git", "rev-parse", "--verify", "--quiet", ref], cwd=repo)
    if rc != 0:
        report.append({"branch": b, "error": "not found on origin"})
        continue
    behind = int(git("rev-list", "--count", f"{ref}..origin/main", repo=repo))
    ahead = int(git("rev-list", "--count", f"origin/main..{ref}", repo=repo))
    rc, stdout, _ = code(["git", "merge-tree", "--write-tree", "--name-only", "--no-messages", "origin/main", ref], cwd=repo)
    conflicts = stdout.splitlines()[1:] if rc == 1 else []
    changed = git("diff", "--name-only", f"origin/main...{ref}", repo=repo).splitlines()
    added = git("diff", "--name-only", "--diff-filter=A", f"origin/main...{ref}", "--", MIGRATIONS, repo=repo).splitlines()
    migrations = []
    for m in added:
        if not m.endswith(".sql"):
            continue
        on_main, _, _ = code(["git", "cat-file", "-e", f"origin/main:{m}"], cwd=repo)
        migrations.append({"file": m, "already_on_main": on_main == 0})
    files_by_branch[b] = set(changed)
    new_migrations[b] = [m["file"] for m in migrations if not m["already_on_main"]]
    report.append({"branch": b, "behind_main": behind, "ahead_of_main": ahead,
                   "conflicts_with_main": conflicts, "changed_files": len(changed),
                   "migrations": migrations, "touches_migrations_sum": bool(SUM_FILE) and SUM_FILE in changed})

shared = [{"branches": [x, y], "files": sorted(files_by_branch[x] & files_by_branch[y])}
          for x, y in itertools.combinations(files_by_branch, 2) if files_by_branch[x] & files_by_branch[y]]
with_new = [b for b, ms in new_migrations.items() if ms]
out({"ok": True, "branches": report, "shared_files": shared,
     "migration_clash": len(with_new) > 1, "branches_with_new_migrations": with_new,
     "needs_update": [r["branch"] for r in report if r.get("conflicts_with_main")]})
