from pathlib import Path

from app.services.shell import FAILURES, run

MOVED_COLORS = [f"color.diff.{k}={v}" for k, v in (
    ("oldMoved", "magenta"), ("newMoved", "cyan"), ("oldMovedAlternative", "magenta"), ("newMovedAlternative", "cyan"),
    ("oldMovedDimmed", "magenta"), ("newMovedDimmed", "cyan"), ("oldMovedAlternativeDimmed", "magenta"),
    ("newMovedAlternativeDimmed", "cyan"), ("old", "red"), ("new", "green"))]
MOVED_ARGS = ["--color=always", "--ws-error-highlight=none", "--histogram", "--color-moved=blocks",
              "--color-moved-ws=allow-indentation-change", "-U12"]


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
        out.moved = run("git", "-C", clone, *cfg, "diff", *MOVED_ARGS, rng, timeout=120)
    except FAILURES:
        out.moved = None
    return out


def fetch_diff(pr):
    clone, n = pr["source"]["clone"], pr["number"]
    head_ref, base_ref = f"refs/review/pr-{n}", f"refs/review/base-{n}"
    run("git", "-C", clone, "fetch", "-q", "--no-tags", "origin", f"+pull/{n}/head:{head_ref}", f"+refs/heads/{pr['baseRefName']}:{base_ref}", timeout=300)
    return diff(clone, f"{base_ref}...{head_ref}")


def generated_paths(pr, paths):
    """The paths the clone marks `linguist-generated`, read at the PR head when git supports --source, else from the working tree."""
    if not paths or not has_clone(pr["source"]):
        return set()
    stdin = "".join(p + "\0" for p in paths).encode()
    for source in (["--source", f"refs/review/pr-{pr['number']}"], []):
        try:
            out = run("git", "-C", pr["source"]["clone"], "check-attr", *source, "-z", "--stdin", "linguist-generated", input=stdin, timeout=30)
            break
        except FAILURES + (OSError,):
            continue
    else:
        return set()
    parts = out.split("\0")
    return {parts[i] for i in range(0, len(parts) - 2, 3) if parts[i + 2] in ("true", "set")}
