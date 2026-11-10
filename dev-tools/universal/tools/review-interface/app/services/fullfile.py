"""A changed file shown whole: the PR's diff for one path with unlimited context."""
from app.services import git, tokdiff
from app.services.diff import parse_file_rows
from app.services.shell import run
from app.ui.components import file_section

CONTEXT = "-U1000000"


class NoClone(Exception):
    pass


def rows(cfg, meta, path):
    src = next((s for s in cfg["sources"] if s.get("repo") == meta["repo"] and git.has_clone(s)), None)
    if not src:
        raise NoClone("Showing a whole file needs a local clone of " + meta["repo"])
    rng = f"refs/review/base-{meta['pr']}...{meta['head_sha']}"
    text = run("git", "--literal-pathspecs", "-C", src["clone"], "diff", "--histogram", CONTEXT, rng, "--", path, timeout=60)
    found, _, _ = parse_file_rows(text.splitlines())
    return [r for r in found if r[0] != "hunk"]


def render(cfg, meta, path, idx):
    found = rows(cfg, meta, path)
    spans, quiet = tokdiff.strong_spans([{"path": path, "rows": found}])[0]
    return {"html": file_section.full_table(idx, found, spans, quiet) if found else "", "lines": len(found)}
