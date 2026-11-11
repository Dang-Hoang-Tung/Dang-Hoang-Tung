import json
import os
import sys

from app.config import now
from app.services import sources
from app.services.shell import FAILURES, run, why

PR_FIELDS = "number,title,url,author,headRefOid,baseRefName,isDraft,additions,deletions,changedFiles,body,createdAt,labels,statusCheckRollup"
REQUESTS_Q = ("query($o:String!,$n:String!,$p:Int!){repository(owner:$o,name:$n){pullRequest(number:$p){timelineItems("
              "itemTypes:[REVIEW_REQUESTED_EVENT],last:50){nodes{... on ReviewRequestedEvent{createdAt requestedReviewer{"
              "__typename ... on User{login} ... on Team{slug}}}}}}}}")
FAILING = ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED")
PENDING = ("PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED", "WAITING")
_viewer = []
DEFAULT_SEARCH = "review-requested:@me -author:@me"


def _search_owner(src):
    """(repo, number) of the open PRs under an owner (user or org) matching the source's search, newest first.
    One search page, so `limit` is capped at 100."""
    q = f'is:pr is:open user:{src["owner"]} {src.get("search", DEFAULT_SEARCH)}'
    per_page = min(src.get("limit", 50), 100)
    found = json.loads(run("gh", "api", "-X", "GET", "search/issues", "-f", f"q={q}", "-f", "sort=created", "-f", "order=desc",
                           "-f", f"per_page={per_page}",
                           "--jq", "[.items[] | [(.repository_url | split(\"/\")[-2:] | join(\"/\")), .number]]"))
    return [(r, n) for r, n in found if sources.covers(src, r)]


def _view_all(pairs):
    prs = []
    for repo, n in pairs:
        pr = view_pr(repo, n)
        if pr:
            prs.append(dict(pr, repo=repo))
    return prs


def _hits(src, earlier, only, bare):
    """The PRs `src` finds, as dicts with `repo` set. A repo an earlier source covers is left to that source."""
    def mine(repo):
        return sources.covers(src, repo) and not any(sources.covers(s, repo) for s in earlier)

    if only:
        pairs = [(r or src["repo"], n) for r, n in only if (r is None and bare) or (r and mine(r))]
        return _view_all(pairs)
    if "repo" in src:
        if not mine(src["repo"]):
            return []
        listed = json.loads(run("gh", "pr", "list", "-R", src["repo"], "--search", src.get("search", DEFAULT_SEARCH),
                                "--limit", str(src.get("limit", 50)), "--json", PR_FIELDS))
        return [dict(pr, repo=src["repo"]) for pr in listed]
    return _view_all([(r, n) for r, n in _search_owner(src) if mine(r)])


def list_pending(cfg, only=None):
    out, seen = [], set()
    configured = cfg["sources"]
    # A bare PR number belongs to the first single-repo source.
    bare_to = next((i for i, s in enumerate(configured) if "repo" in s), None)
    if only and bare_to is None and any(r is None for r, _ in only):
        print("  a bare PR number needs a 'repo' source; give it as owner/repo#N", file=sys.stderr)
    for i, src in enumerate(configured):
        try:
            prs = _hits(src, configured[:i], only, i == bare_to)
        except FAILURES + (ValueError,) as e:
            print(f"  {src.get('repo') or src['owner']}: could not list PRs: {why(e)}", file=sys.stderr)
            continue
        for pr in prs:
            if (pr["repo"], pr["number"]) in seen:
                continue
            seen.add((pr["repo"], pr["number"]))
            out.append(dict(pr, source=sources.for_repo(cfg, pr["repo"])))
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


def post_reply(repo, pr, root_id, body):
    if os.environ.get("REVIEW_POST_DRY_RUN"):
        return {"url": f"https://example.invalid/{repo}/pull/{pr}#dry-run-reply", "id": 0, "dry_run": True}
    res = json.loads(run("gh", "api", "-X", "POST", f"repos/{repo}/pulls/{pr}/comments/{root_id}/replies", "-f", f"body={body}"))
    return {"url": res["html_url"], "id": res["id"]}


def fetch_review_comments(repo, pr):
    out, dec, text, i = [], json.JSONDecoder(), run("gh", "api", f"repos/{repo}/pulls/{pr}/comments", "--paginate"), 0
    while True:
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            return out
        page, i = dec.raw_decode(text, i)
        out += page
