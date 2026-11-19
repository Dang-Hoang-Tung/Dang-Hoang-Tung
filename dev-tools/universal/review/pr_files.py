"""The files a change touches, with lines added and removed, status and review notes.
Input for code_tree.py and treemap.py: a GitHub PR (through `gh`), or a git range in a local repo."""
import json
import re
import subprocess
from pathlib import Path

SEVERITIES = ("block", "should", "nit", "question", "look")
GENERATED = [r"(^|/)generated/", r"[Gg]enerated[A-Z.]", r"\.gen\.", r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|Cargo\.lock|go\.sum)$",
             r"\.snap$", r"\.min\.(js|css)$"]
PR_REF = re.compile(r"(?:https://github\.com/)?([\w.-]+/[\w.-]+)(?:#|/pull/)(\d+)")
GH_STATUS = {"added": "added", "removed": "deleted", "renamed": "renamed", "copied": "added"}
GIT_STATUS = {"A": "added", "D": "deleted", "R": "renamed", "C": "added"}


def worst(kinds):
    kinds = set(kinds)
    return next((k for k in SEVERITIES if k in kinds), None)


def _run(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def _file(path, a, d, status, generated):
    return {"path": path, "a": a, "d": d, "status": status, "notes": [],
            "gen": any(re.search(p, path) for p in generated)}


def from_pr(ref, generated=GENERATED):
    """`ref` is owner/repo#123 or a PR URL."""
    m = PR_REF.fullmatch(ref.strip().rstrip("/"))
    if not m:
        raise ValueError(f"not a PR reference: {ref} (use owner/repo#123 or the PR URL)")
    repo, n = m.groups()
    pr = json.loads(_run("gh", "pr", "view", n, "-R", repo, "--json", "title,url"))
    rows = json.loads(_run("gh", "api", "--paginate", "--slurp", f"repos/{repo}/pulls/{n}/files?per_page=100"))
    files = [_file(f["filename"], f["additions"], f["deletions"], GH_STATUS.get(f["status"], "modified"), generated)
             for page in rows for f in page]
    return {"title": f'#{n} {pr["title"]}', "url": pr["url"], "root": repo.split("/")[1], "files": files}


def parse_numstat(numstat, name_status):
    """Files from `git diff -z --numstat -M` and `git diff -z --name-status -M` output."""
    statuses, parts = {}, name_status.split("\0")
    i = 0
    while i < len(parts) - 1:
        code = parts[i]
        if code[:1] in "RC":
            statuses[parts[i + 2]] = GIT_STATUS[code[0]]
            i += 3
        else:
            statuses[parts[i + 1]] = GIT_STATUS.get(code[:1], "modified")
            i += 2
    out, parts = [], numstat.split("\0")
    i = 0
    while i < len(parts) and parts[i]:
        a, d, path = parts[i].split("\t", 2)
        if path == "":  # a rename: old and new path follow
            path = parts[i + 2]
            i += 3
        else:
            i += 1
        out.append((path, 0 if a == "-" else int(a), 0 if d == "-" else int(d), statuses.get(path, "modified")))
    return out


def from_git(rng, repo_dir=".", generated=GENERATED):
    """`rng` is any git diff range, e.g. main...HEAD."""
    numstat = _run("git", "diff", "-z", "--numstat", "-M", rng, cwd=repo_dir)
    names = _run("git", "diff", "-z", "--name-status", "-M", rng, cwd=repo_dir)
    root = Path(_run("git", "rev-parse", "--show-toplevel", cwd=repo_dir).strip()).name
    files = [_file(p, a, d, s, generated) for p, a, d, s in parse_numstat(numstat, names)]
    return {"title": rng, "url": None, "root": root, "files": files}


def add_notes(change, notes):
    """Attach notes to files. `notes` is a list of {path, severity, title}, or a review-insights file's dict.
    A path may be a full path or a unique file name; notes with no matching file are returned."""
    if isinstance(notes, dict):
        notes = notes.get("recommendations", [])
    files, unmatched = change["files"], []
    for n in notes:
        p = n.get("path") or ""
        hits = [f for f in files if f["path"] == p] or [f for f in files if p and f["path"].endswith("/" + p.lstrip("/"))]
        if len(hits) == 1 and n.get("severity") in SEVERITIES:
            hits[0]["notes"].append({"severity": n["severity"], "title": n.get("title", "")})
        else:
            unmatched.append(n)
    return unmatched


def load(source, repo_dir=".", notes_path=None):
    """A PR reference (owner/repo#123 or URL) or a git range, plus an optional notes JSON file."""
    change = from_pr(source) if PR_REF.fullmatch(source.strip().rstrip("/")) else from_git(source, repo_dir)
    if notes_path:
        add_notes(change, json.loads(Path(notes_path).read_text()))
    return change
