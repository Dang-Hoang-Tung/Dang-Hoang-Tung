import json
import os
import sys

from app.config import now
from app.services.shell import FAILURES, run, why

PR_FIELDS = "number,title,url,author,headRefOid,baseRefName,isDraft,additions,deletions,changedFiles,body,createdAt,labels,statusCheckRollup"
REQUESTS_Q = ("query($o:String!,$n:String!,$p:Int!){repository(owner:$o,name:$n){pullRequest(number:$p){timelineItems("
              "itemTypes:[REVIEW_REQUESTED_EVENT],last:50){nodes{... on ReviewRequestedEvent{createdAt requestedReviewer{"
              "__typename ... on User{login} ... on Team{slug}}}}}}}}")
FAILING = ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED")
PENDING = ("PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED", "WAITING")
_viewer = []


def list_pending(cfg, only=None):
    out = []
    for i, src in enumerate(cfg["sources"]):
        repo = src["repo"]
        try:
            if only:
                nums = [n for r, n in only if r == repo or (r is None and i == 0)]
                items = [pr for pr in (view_pr(repo, n) for n in nums) if pr]
            else:
                items = json.loads(run("gh", "pr", "list", "-R", repo, "--search", src.get("search", "review-requested:@me -author:@me"),
                                       "--limit", str(src.get("limit", 50)), "--json", PR_FIELDS))
        except FAILURES + (ValueError,) as e:
            print(f"  {repo}: could not list PRs: {why(e)}", file=sys.stderr)
            continue
        for it in items:
            it["repo"], it["source"] = repo, src
            out.append(it)
    return out


def view_pr(repo, n):
    try:
        return json.loads(run("gh", "pr", "view", str(n), "-R", repo, "--json", PR_FIELDS))
    except FAILURES + (ValueError,) as e:
        print(f"  {repo}#{n}: could not load: {why(e)}", file=sys.stderr)
        return None


def viewer_login():
    if not _viewer:
        try:
            _viewer.append(run("gh", "api", "user", "-q", ".login").strip())
        except FAILURES:
            _viewer.append("")
    return _viewer[0]


def review_requests(pr):
    owner, name = pr["repo"].split("/")
    try:
        out = json.loads(run("gh", "api", "graphql", "-f", f"query={REQUESTS_Q}", "-f", f"o={owner}", "-f", f"n={name}", "-F", f"p={pr['number']}"))
        return out["data"]["repository"]["pullRequest"]["timelineItems"]["nodes"]
    except FAILURES + (ValueError, KeyError, TypeError):
        return []


def requested_at(cfg, pr):
    nodes = review_requests(pr)
    me = viewer_login()
    mine = [x["createdAt"] for x in nodes if x and x.get("requestedReviewer") and
            (x["requestedReviewer"].get("login") == me or x["requestedReviewer"].get("slug") in cfg["team_slugs"])]
    anyone = [x["createdAt"] for x in nodes if x]
    return max(mine or anyone or [pr.get("createdAt") or now()])


def ci_state(rollup):
    states = [(c.get("conclusion") or c.get("state") or c.get("status") or "").upper() for c in (rollup or [])]
    if any(s in FAILING for s in states):
        return "failing"
    if any(s in PENDING for s in states):
        return "pending"
    return "passing" if states else "none"


def fetch_api_diff(pr):
    return run("gh", "api", f"repos/{pr['repo']}/pulls/{pr['number']}", "-H", "Accept: application/vnd.github.diff")


def submit_approval(repo, pr, commit, body=""):
    if os.environ.get("REVIEW_POST_DRY_RUN"):
        return {"url": f"https://example.invalid/{repo}/pull/{pr}#dry-run-approval", "id": 0, "dry_run": True}
    args = ["gh", "api", "-X", "POST", f"repos/{repo}/pulls/{pr}/reviews", "-f", "event=APPROVE", "-f", f"commit_id={commit}"]
    if body:
        args += ["-f", f"body={body}"]
    res = json.loads(run(*args))
    return {"url": res["html_url"], "id": res["id"]}


def post_comment(repo, pr, commit, thread, body):
    on_lines = bool(thread.get("path") and thread.get("line"))
    if os.environ.get("REVIEW_POST_DRY_RUN"):
        kind = "line" if on_lines else "conversation"
        return {"url": f"https://example.invalid/{repo}/pull/{pr}#dry-run-{kind}", "id": 0, "dry_run": True}
    if on_lines:
        side = "LEFT" if thread.get("side") == "LEFT" else "RIGHT"
        args = ["gh", "api", "-X", "POST", f"repos/{repo}/pulls/{pr}/comments", "-f", f"body={body}", "-f", f"commit_id={commit}",
                "-f", f"path={thread['path']}", "-F", f"line={thread['line']}", "-f", f"side={side}"]
        if thread.get("start_line") and thread["start_line"] != thread["line"]:
            args += ["-F", f"start_line={thread['start_line']}", "-f", f"start_side={side}"]
    else:
        args = ["gh", "api", "-X", "POST", f"repos/{repo}/issues/{pr}/comments", "-f", f"body={body}"]
    res = json.loads(run(*args))
    return {"url": res["html_url"], "id": res["id"]}
