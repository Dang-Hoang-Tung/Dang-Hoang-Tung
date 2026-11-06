#!/usr/bin/env python3
"""Collect the PR review queue as compact JSON. Read-only: runs `gh` and reads the briefs folder.

Usage: review-queue.py [team ...]   (default: the teams in ~/.claude/skills/workspace/review-teams.txt)
Output: {"queue": [...], "failed": [...], "warnings": [...]}
"""
import fnmatch
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
BRIEFS = pathlib.Path.home() / ".claude" / "agent-files" / "shared" / "team-reviewer" / "briefs"
SEARCH_FIELDS = "number,title,repository,author,url,isDraft,createdAt,labels"
VIEW_FIELDS = "additions,deletions,changedFiles,files,headRefOid,statusCheckRollup,body"
LIMIT = 50
RETRIES = 2
FAILING = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE"}
PENDING = {"", "PENDING", "QUEUED", "IN_PROGRESS", "EXPECTED", "WAITING", "REQUESTED"}


def read_list(name):
    path = name if isinstance(name, pathlib.Path) else HERE / name
    if not path.exists():
        return []
    lines = (line.strip() for line in path.read_text().splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def gh(*args):
    out = subprocess.run(["gh", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"gh exited {out.returncode}")
    return json.loads(out.stdout or "null")


def gh_retry(*args):
    error = None
    for _ in range(RETRIES + 1):
        try:
            return gh(*args)
        except (RuntimeError, json.JSONDecodeError) as e:
            error = e
    raise RuntimeError(str(error))


def ci_status(checks):
    states = [(c.get("conclusion") or c.get("state") or c.get("status") or "").upper() for c in checks]
    if any(s in FAILING for s in states):
        return "failing"
    if any(s in PENDING for s in states):
        return "pending"
    return "passing" if states else "none"


def brief_status(repo, number, sha7):
    current = BRIEFS / f"{repo}-{number}-{sha7}.md"
    if current.exists():
        return "current", str(current)
    older = sorted(BRIEFS.glob(f"{repo}-{number}-*.md"), key=lambda p: p.stat().st_mtime)
    return ("stale", str(older[-1])) if older else ("none", None)


def is_generated(path, patterns):
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(pathlib.PurePath(path).name, p) for p in patterns)


teams = sys.argv[1:] or read_list(pathlib.Path.home() / ".claude/skills/workspace/review-teams.txt")
generated = read_list("generated.txt")
warnings, failed = [], []
me = subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True).stdout.strip()

prs = {}
for who, reviewer in [("me", "@me")] + [(t, t) for t in teams]:
    try:
        results = gh_retry("search", "prs", f"--review-requested={reviewer}", "--state=open",
                           f"--limit={LIMIT}", f"--json={SEARCH_FIELDS}")
    except RuntimeError as e:
        warnings.append(f"search for {reviewer} failed: {e}")
        continue
    if len(results) >= LIMIT:
        warnings.append(f"search for {reviewer} hit the {LIMIT} limit; some PRs may be missing")
    for pr in results:
        if pr["author"]["login"] == me:
            continue
        prs.setdefault(pr["url"], {**pr, "requested": []})["requested"].append(who)

queue = []
for pr in prs.values():
    owner_repo = pr["repository"]["nameWithOwner"]
    repo = owner_repo.split("/")[1]
    label = f"{repo}#{pr['number']}"
    try:
        view = gh_retry("pr", "view", str(pr["number"]), "-R", owner_repo, f"--json={VIEW_FIELDS}")
    except RuntimeError as e:
        failed.append({"pr": label, "url": pr["url"], "error": str(e)})
        continue
    files = view.get("files") or []
    gen_files = [f for f in files if is_generated(f["path"], generated)]
    added_gen = sum(f["additions"] for f in gen_files)
    sha7 = view["headRefOid"][:7]
    brief, brief_path = brief_status(repo, pr["number"], sha7)
    queue.append({
        "pr": label,
        "title": pr["title"],
        "url": pr["url"],
        "author": pr["author"]["login"],
        "requested": pr["requested"],
        "draft": pr["isDraft"],
        "created": pr["createdAt"][:10],
        "labels": [label_["name"] for label_ in pr["labels"]],
        "size": f"+{view['additions']}/-{view['deletions']} in {view['changedFiles']} files",
        "added": view["additions"],
        "added_excl_generated": view["additions"] - added_gen,
        "generated_files": [f["path"] for f in gen_files],
        "ci": ci_status(view["statusCheckRollup"] or []),
        "has_description": bool((view["body"] or "").strip()),
        "sha7": sha7,
        "brief": brief,
        "brief_path": brief_path,
    })

print(json.dumps({"queue": sorted(queue, key=lambda p: p["created"]), "failed": failed, "warnings": warnings},
                 separators=(",", ":")))
