#!/usr/bin/env python3
"""Rebase a PR stack onto its new base, bottom up, with git rebase --onto. Local only, never pushes.
Dry run unless --apply.

Usage: restack.py <new-base> <branch-1> <branch-2> ... [--old-base REF] [--repo PATH] [--apply]
Branches are bottom to top. Default old base for branch-1: its merge-base with <new-base>.
Stops at the first conflict, aborts that rebase, and reports it.
"""
import argparse
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import require_config, APP, apply_flag, code, fail, git, out
require_config()

apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("new_base")
p.add_argument("branches", nargs="+")
p.add_argument("--old-base")
p.add_argument("--repo", default=str(APP))
a = p.parse_args()

if apply and pathlib.Path(a.repo).resolve() == APP.resolve():
    fail("don't restack in the main checkout; pass --repo <your worktree>")
if apply and git("status", "--porcelain", repo=a.repo):
    fail("working tree has uncommitted changes")

# Record each branch's old parent tip before anything moves.
old_tips = {b: git("rev-parse", b, repo=a.repo) for b in a.branches}
first_old = a.old_base or git("merge-base", a.new_base, a.branches[0], repo=a.repo)
plan = []
parent_new, parent_old = a.new_base, first_old
for b in a.branches:
    plan.append({"branch": b, "onto": parent_new, "upstream": parent_old[:10] if len(parent_old) == 40 else parent_old})
    parent_new, parent_old = b, old_tips[b]

if not apply:
    out({"ok": True, "applied": False, "plan": plan, "note": "re-run with --apply; nothing is pushed"})
    sys.exit(0)

done = []
parent_new, parent_old = a.new_base, first_old
for b in a.branches:
    rc, _, err = code(["git", "rebase", "--onto", parent_new, parent_old, b], cwd=a.repo)
    if rc != 0:
        files = git("diff", "--name-only", "--diff-filter=U", repo=a.repo, check=False).splitlines()
        code(["git", "rebase", "--abort"], cwd=a.repo)
        out({"ok": False, "applied": True, "restacked": done, "conflict": {"branch": b, "files": files, "error": err[-300:]}})
        sys.exit(1)
    done.append(b)
    parent_new, parent_old = b, old_tips[b]
out({"ok": True, "applied": True, "restacked": done, "note": "local only; push each branch when ready"})
