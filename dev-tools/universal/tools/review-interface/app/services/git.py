from pathlib import Path

from app.services.shell import run


def has_clone(src):
    clone = src.get("clone")
    return bool(clone and Path(clone, ".git").exists())


def fetch_diff(pr):
    clone, n = pr["source"]["clone"], pr["number"]
    head_ref, base_ref = f"refs/review/pr-{n}", f"refs/review/base-{n}"
    run("git", "-C", clone, "fetch", "-q", "--no-tags", "origin", f"+pull/{n}/head:{head_ref}", f"+refs/heads/{pr['baseRefName']}:{base_ref}", timeout=300)
    return run("git", "-C", clone, "diff", "-U12", f"{base_ref}...{head_ref}", timeout=120)
