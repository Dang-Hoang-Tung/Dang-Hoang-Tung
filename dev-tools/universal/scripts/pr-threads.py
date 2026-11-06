#!/usr/bin/env python3
"""Unresolved review threads on a PR. Read-only.

Usage: pr-threads.py <pr-number> [-R owner/repo]   (default repo: the main repo in workspace/config.json)
"""
import argparse
from _lib import require_config, APP, fail, gh_json, out, run
require_config()

p = argparse.ArgumentParser()
p.add_argument("pr", type=int)
p.add_argument("-R", "--repo")
a = p.parse_args()

try:
    repo = a.repo or run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], cwd=APP)
except RuntimeError as e:
    fail(f"can't resolve repo: {e}")
owner, name = repo.split("/")

QUERY = """query($owner:String!,$name:String!,$pr:Int!){repository(owner:$owner,name:$name){pullRequest(number:$pr){
 url reviewThreads(first:100){nodes{id isResolved isOutdated path line
  comments(first:20){nodes{author{login __typename} body url createdAt}}}}}}}"""
try:
    data = gh_json("api", "graphql", "-f", f"query={QUERY}", "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"pr={a.pr}")
except RuntimeError as e:
    fail(str(e))

pr = data["data"]["repository"]["pullRequest"]
threads = []
for t in pr["reviewThreads"]["nodes"]:
    if t["isResolved"]:
        continue
    comments = t["comments"]["nodes"]
    first = comments[0] if comments else {}
    author = (first.get("author") or {})
    login = author.get("login", "?")
    threads.append({
        "thread_id": t["id"],
        "path": t["path"],
        "line": t["line"],
        "outdated": t["isOutdated"],
        "author": login,
        "bot": author.get("__typename") == "Bot" or login.endswith("[bot]"),
        "comment": (first.get("body") or "")[:600],
        "replies": len(comments) - 1,
        "url": first.get("url"),
    })
out({"ok": True, "pr": pr["url"], "unresolved": len(threads), "threads": threads})
