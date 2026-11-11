import fcntl
import os
import shutil
import sys
from pathlib import Path

from app.services import sources
from app.services.shell import FAILURES, run, why

CLONE_TIMEOUT = 900

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


def _cache_path(cfg, repo):
    return Path(cfg["data_dir"], "clones", *repo.split("/"))


def cached_clone(cfg, src):
    """`src` pointing at its own clone, else at the cache clone if one exists. Never clones."""
    if has_clone(src):
        return src
    path = _cache_path(cfg, src["repo"])
    return dict(src, clone=str(path), cached=True) if Path(path, ".git").exists() else src


def ensure_clone(cfg, src):
    """Like `cached_clone`, but makes the cache clone when there is none and `auto_clone` is on."""
    found = cached_clone(cfg, src)
    if has_clone(found) or not cfg["auto_clone"]:
        return found
    _make_cache_clone(cfg, src["repo"])
    return cached_clone(cfg, src)


def _make_cache_clone(cfg, repo):
    """Blobless, no checkout. Built beside the final path and renamed in, so `.git` only appears when it is complete."""
    path = _cache_path(cfg, repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(Path(cfg["data_dir"], "clones", ".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if Path(path, ".git").exists():
            return
        for stale in path.parent.glob(f"{path.name}.tmp-*"):
            shutil.rmtree(stale, ignore_errors=True)
        tmp = Path(f"{path}.tmp-{os.getpid()}")
        print(f"  cloning {repo} into the cache…", file=sys.stderr)
        try:
            run("gh", "repo", "clone", repo, str(tmp), "--", "--filter=blob:none", "--no-checkout", "--quiet", timeout=CLONE_TIMEOUT)
            os.rename(tmp, path)
        except FAILURES + (OSError,) as e:
            print(f"  {repo}: could not clone: {why(e)}", file=sys.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def clone_for(cfg, repo):
    """The path of the existing clone (its own or the cache) for `repo`, or None."""
    src = sources.for_repo(cfg, repo)
    found = src and cached_clone(cfg, src)
    return found["clone"] if found and has_clone(found) else None


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
    """The paths the clone marks `linguist-generated`, read at the PR head. Without `git check-attr --source` (git before 2.40),
    a cache clone, which has no checkout, is read through its index; any other clone through its working tree."""
    src = pr["source"]
    if not paths or not has_clone(src):
        return set()
    clone, ref = src["clone"], f"refs/review/pr-{pr['number']}"
    stdin = "".join(p + "\0" for p in paths).encode()

    def check_attr(*options):
        return run("git", "-C", clone, "check-attr", *options, "-z", "--stdin", "linguist-generated", input=stdin, timeout=30)

    try:
        try:
            out = check_attr("--source", ref)
        except FAILURES:
            if src.get("cached"):
                run("git", "-C", clone, "read-tree", ref, timeout=30)
                out = check_attr("--cached")
            else:
                out = check_attr()
    except FAILURES + (OSError,):
        return set()
    parts = out.split("\0")
    return {parts[i] for i in range(0, len(parts) - 2, 3) if parts[i + 2] in ("true", "set")}
