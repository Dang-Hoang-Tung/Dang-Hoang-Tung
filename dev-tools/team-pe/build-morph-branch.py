#!/usr/bin/env python3
"""Build a fresh morph branch: origin/main plus the given branches, in order. Dry run unless --apply.

Usage: build-morph-branch.py <branch> [<branch> ...] [--name <tag>/morph/<YYYY-MM-DD>-<n>] [--apply]
Morph branches live under PREFIX, my own namespace, so we never touch other people's branches.
Dry run: predicts conflicts without touching any branch or worktree.
--apply: builds it in team-pe's worktree (<worktrees>/team-pe) and pushes it.
Stops at the first conflict and reports the files.
"""
import argparse
import datetime
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import require_config, APP, MORPH_PREFIX, WORKTREES, apply_flag, code, fail, git, out
require_config()

WORKTREE = WORKTREES / "team-pe"
PREFIX = MORPH_PREFIX

apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("branches", nargs="+")
p.add_argument("--name")
a = p.parse_args()

git("fetch", "--quiet", "--prune", "origin")
if a.name:
    name = a.name
else:
    today = datetime.date.today().isoformat()
    taken = git("branch", "-r", "--list", f"origin/{PREFIX}{today}-*").split()
    n = 1 + max([int(t.rsplit("-", 1)[1]) for t in taken if t.rsplit("-", 1)[1].isdigit()] or [0])
    name = f"{PREFIX}{today}-{n}"

# Predict: chain merges in memory with merge-tree + commit-tree (no refs change).
head = git("rev-parse", "origin/main")
merged = []
for b in a.branches:
    rc, stdout, _ = code(["git", "merge-tree", "--write-tree", "--name-only", "--no-messages", head, f"origin/{b}"], cwd=APP)
    if rc != 0:
        out({"ok": False, "applied": False, "name": name, "merged": merged, "conflict": {"branch": b, "files": stdout.splitlines()[1:]}})
        sys.exit(1)
    tree = stdout.splitlines()[0]
    head = git("commit-tree", tree, "-p", head, "-p", f"origin/{b}", "-m", f"predict {b}")
    merged.append(b)

if not apply:
    out({"ok": True, "applied": False, "name": name, "merged": merged, "note": "clean; re-run with --apply to build and push"})
    sys.exit(0)

if not WORKTREE.exists():
    WORKTREE.parent.mkdir(parents=True, exist_ok=True)
    git("worktree", "add", "--detach", str(WORKTREE), "origin/main")
git("checkout", "--quiet", "-B", name, "origin/main", repo=WORKTREE)
for b in a.branches:
    rc, _, err = code(["git", "merge", "--no-ff", "--no-edit", f"origin/{b}"], cwd=WORKTREE)
    if rc != 0:
        files = git("diff", "--name-only", "--diff-filter=U", repo=WORKTREE).splitlines()
        code(["git", "merge", "--abort"], cwd=WORKTREE)
        out({"ok": False, "applied": True, "name": name, "conflict": {"branch": b, "files": files, "error": err[-300:]}})
        sys.exit(1)
git("push", "--quiet", "-u", "origin", name, repo=WORKTREE)
out({"ok": True, "applied": True, "name": name, "sha": git("rev-parse", "--short", "HEAD", repo=WORKTREE),
     "merged": a.branches, "worktree": str(WORKTREE)})
