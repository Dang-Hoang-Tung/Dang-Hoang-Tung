"""Pull GitHub line-comment threads into the review state. Adds only; never changes what the reviewer wrote."""
import re

from app.services import github
from app.services.state import load_state, locked, save_state


def posted_ids(t):
    return {v.get("id") for v in (t.get("posted_messages") or {}).values() if isinstance(v, dict)}


def group(comments):
    """{root id: [comments by time]}; replies follow in_reply_to_id up to the root."""
    parent = {c["id"]: c.get("in_reply_to_id") for c in comments}

    def root(i):
        while parent.get(i):
            i = parent[i]
        return i
    out = {}
    for c in comments:
        out.setdefault(root(c["id"]), []).append(c)
    for cs in out.values():
        cs.sort(key=lambda c: (c.get("created_at") or "", c["id"]))
    return out


def clean(body):
    """Drop HTML comments and collapsed <details> blocks (bot boilerplate) from a GitHub comment."""
    return re.sub(r"<!--.*?-->|<details>.*?</details>", "", body, flags=re.S | re.I).strip()


def to_message(c, me):
    mine = bool(me) and (c.get("user") or {}).get("login") == me
    return {"id": f"gh-{c['id']}", "who": "me" if mine else "github", "author": (c.get("user") or {}).get("login") or "",
            "text": clean(c.get("body") or ""), "at": c.get("created_at") or "", "gh_id": c["id"], "url": c.get("html_url")}


def find_thread(threads, root_id):
    return next((t for t in threads if t.get("gh_root") == root_id or root_id in posted_ids(t)), None)


def new_thread(root_id, root):
    line = root.get("line") or root.get("original_line")
    start = (root.get("start_line") if root.get("line") else root.get("original_start_line")) or line
    t = {"id": f"gh-{root_id}", "synced": True, "gh_root": root_id, "path": root.get("path"), "line": line, "start_line": start,
         "created": root.get("created_at"), "resolved": False,
         "side": "LEFT" if root.get("side") == "LEFT" else "RIGHT", "commit": root.get("commit_id"), "messages": []}
    if root.get("line") is None:
        t["outdated"] = True
    return t


def merge(data, comments, me):
    threads = data.setdefault("threads", [])
    added = 0
    for root_id, cs in group(comments).items():
        t = find_thread(threads, root_id)
        if t is None:
            t = new_thread(root_id, next((c for c in cs if c["id"] == root_id), cs[0]))
            threads.append(t)
        else:
            t.setdefault("synced", True)
            t.setdefault("gh_root", root_id)
        known = {m.get("gh_id") for m in t["messages"]} | {m.get("id") for m in t["messages"]} | posted_ids(t)
        for c in cs:
            if c["id"] in known or f"gh-{c['id']}" in known:
                continue
            t["messages"].append(to_message(c, me))
            added += 1
        t["messages"].sort(key=lambda m: m.get("at") or "")
    return added


def sync(cfg, meta):
    comments = github.fetch_review_comments(meta["repo"], meta["pr"])
    me = github.viewer_login()
    with locked(cfg, meta["slug"]):
        data = load_state(cfg, meta["slug"])
        added = merge(data, comments, me)
        if added:
            save_state(cfg, meta["slug"], data)
    return added
