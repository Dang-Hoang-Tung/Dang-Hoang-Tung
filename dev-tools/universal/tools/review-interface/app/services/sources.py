"""Config sources: one repo (`repo`), or every repo under an owner (`owner`). The first source covering a repo wins."""
from fnmatch import fnmatch


def covers(src, repo):
    if "repo" in src:
        return src["repo"] == repo
    return repo.split("/")[0] == src["owner"] and not any(fnmatch(repo, pat) for pat in src.get("exclude", []))


def for_repo(cfg, repo):
    """The first source covering `repo`, as a per-repo source (owner sources filled in for that repo), or None."""
    src = next((s for s in cfg["sources"] if covers(s, repo)), None)
    if not src or "repo" in src:
        return src
    out = {k: v for k, v in src.items() if k not in ("owner", "exclude")}
    out["repo"] = repo
    if src.get("clone"):
        out["clone"] = src["clone"].format(owner=src["owner"], name=repo.split("/", 1)[1])
    return out


def validate(sources):
    for src in sources:
        if ("repo" in src) == ("owner" in src):
            raise SystemExit(f"Bad source {src}: it needs exactly one of 'repo' or 'owner'.")
        if "owner" in src and src.get("clone"):
            try:
                src["clone"].format(owner="o", name="n")
            except (KeyError, IndexError, ValueError):
                raise SystemExit(f"Bad source {src}: 'clone' may only use {{owner}} and {{name}}.")
