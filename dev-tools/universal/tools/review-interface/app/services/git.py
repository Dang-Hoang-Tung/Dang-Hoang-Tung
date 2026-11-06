from pathlib import Path

from app.services.shell import FAILURES, run


def has_clone(src):
    clone = src.get("clone")
    return bool(clone and Path(clone, ".git").exists())


def fetch_diff(pr):
    clone, n = pr["source"]["clone"], pr["number"]
    head_ref, base_ref = f"refs/review/pr-{n}", f"refs/review/base-{n}"
    run("git", "-C", clone, "fetch", "-q", "--no-tags", "origin", f"+pull/{n}/head:{head_ref}", f"+refs/heads/{pr['baseRefName']}:{base_ref}", timeout=300)
    return run("git", "-C", clone, "diff", "-U12", f"{base_ref}...{head_ref}", timeout=120)


def merge_base(pr):
    n = pr["number"]
    try:
        return run("git", "-C", pr["source"]["clone"], "merge-base", f"refs/review/base-{n}", f"refs/review/pr-{n}").strip()
    except FAILURES:
        return None


def file_pair(pr, base, path):
    """(old, new) contents of a file at the merge base and at the PR head, or None if either is missing or not text."""
    clone = pr["source"]["clone"]
    try:
        return tuple(run("git", "-C", clone, "show", f"{rev}:{path}", timeout=30) for rev in (base, f"refs/review/pr-{pr['number']}"))
    except FAILURES + (UnicodeDecodeError,):
        return None
