#!/usr/bin/env python3
"""Delete our old morph branches (<tag>/morph/*, remote and local), keeping the ones given. Dry run unless --apply.
Only ever touches PREFIX: other people's branches are never listed or deleted.

Usage: cleanup-morph-branches.py [--keep <tag>/morph/<...> ...] [--apply]
"""
import argparse
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path.home() / ".claude/skills/universal/scripts"))
from _lib import require_config, APP, MORPH_PREFIX, apply_flag, code, git, out
require_config()

PREFIX = MORPH_PREFIX
apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("--keep", nargs="*", default=[])
a = p.parse_args()

git("fetch", "--quiet", "--prune", "origin")
remote = [b.removeprefix("origin/") for b in git("branch", "-r", "--list", f"origin/{PREFIX}*").split()]
local = git("branch", "--list", f"{PREFIX}*", "--format=%(refname:short)").split()
assert all(b.startswith(PREFIX) for b in remote + local)
drop_remote = [b for b in remote if b not in a.keep]
drop_local = [b for b in local if b not in a.keep]
errors = []
if apply:
    for b in drop_remote:
        rc, _, err = code(["git", "push", "--quiet", "origin", "--delete", b], cwd=str(APP))
        if rc:
            errors.append(f"{b}: {err[-200:]}")
    for b in drop_local:
        rc, _, err = code(["git", "branch", "-D", b], cwd=str(APP))
        if rc:
            errors.append(f"{b}: {err[-200:]}")
out({"ok": not errors, "applied": apply, "delete_remote": drop_remote, "delete_local": drop_local, "kept": a.keep, "errors": errors})
