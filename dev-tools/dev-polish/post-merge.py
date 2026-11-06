#!/usr/bin/env python3
"""Clean up after I merge a PR: remove its worktree and local branch. Dry run unless --apply.

Usage: post-merge.py <branch> [--repo PATH] [--apply]
Refuses if the PR isn't merged, or the worktree has uncommitted changes.
"""
import argparse
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import require_config, APP, apply_flag, code, fail, gh_json, git, out
require_config()

apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("branch")
p.add_argument("--repo", default=str(APP))
a = p.parse_args()

prs = gh_json("pr", "list", "--head", a.branch, "--state", "merged", "--json", "number,url,mergedAt", cwd=a.repo)
if not prs:
    fail(f"no merged PR for {a.branch}")

worktree = None
block = {}
for line in git("worktree", "list", "--porcelain", repo=a.repo).splitlines() + [""]:
    if not line:
        if block.get("branch") == f"refs/heads/{a.branch}":
            worktree = block["worktree"]
        block = {}
        continue
    key, _, value = line.partition(" ")
    block[key] = value

if worktree:
    dirty = git("status", "--porcelain", repo=worktree)
    if dirty:
        fail(f"worktree {worktree} has uncommitted changes", changes=dirty.splitlines()[:20])
if worktree and pathlib.Path(worktree).resolve() == pathlib.Path(a.repo).resolve():
    fail("the branch is checked out in the main checkout; switch it away first")

errors = []
if apply:
    if worktree:
        rc, _, err = code(["git", "worktree", "remove", worktree], cwd=a.repo)
        if rc:
            errors.append(err[-300:])
    rc, _, err = code(["git", "branch", "-D", a.branch], cwd=a.repo)
    if rc and "not found" not in err:
        errors.append(err[-300:])
out({"ok": not errors, "applied": apply, "pr": prs[0]["url"], "remove_worktree": worktree, "delete_branch": a.branch, "errors": errors})
