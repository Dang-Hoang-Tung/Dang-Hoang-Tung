from pathlib import Path

from app.services.shell import FAILURES, run

MOVED_COLORS = [f"color.diff.{k}={v}" for k, v in (
    ("oldMoved", "magenta"), ("newMoved", "cyan"), ("oldMovedAlternative", "magenta"), ("newMovedAlternative", "cyan"),
    ("oldMovedDimmed", "magenta"), ("newMovedDimmed", "cyan"), ("oldMovedAlternativeDimmed", "magenta"),
    ("newMovedAlternativeDimmed", "cyan"), ("old", "red"), ("new", "green"))]


class Diff(str):
    """The plain diff text; `moved` holds the same diff coloured by `--color-moved`, or None."""
    moved = None


def has_clone(src):
    clone = src.get("clone")
    return bool(clone and Path(clone, ".git").exists())


def diff(clone, rng):
    out = Diff(run("git", "-C", clone, "diff", "--histogram", "-U12", rng, timeout=120))
    cfg = [a for c in MOVED_COLORS for a in ("-c", c)]
    try:
        out.moved = run("git", "-C", clone, *cfg, "diff", "--color=always", "--ws-error-highlight=none", "--histogram",
                        "--color-moved=blocks", "--color-moved-ws=allow-indentation-change", "-U12", rng, timeout=120)
    except FAILURES:
        out.moved = None
    return out


def fetch_diff(pr):
    clone, n = pr["source"]["clone"], pr["number"]
    head_ref, base_ref = f"refs/review/pr-{n}", f"refs/review/base-{n}"
    run("git", "-C", clone, "fetch", "-q", "--no-tags", "origin", f"+pull/{n}/head:{head_ref}", f"+refs/heads/{pr['baseRefName']}:{base_ref}", timeout=300)
    return diff(clone, f"{base_ref}...{head_ref}")


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
