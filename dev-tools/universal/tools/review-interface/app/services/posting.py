import re
from datetime import datetime, timezone

from app.config import now
from app.services import github
from app.services.state import is_ai, load_state, locked, save_state

POST_PREFIX = re.compile(r"^\s*post:\s*", re.I)
POSTING_TTL = 120


class PostConflict(ValueError):
    """The post cannot go ahead now (409), as opposed to a bad request (400)."""


def post_body(thread, message_id=None):
    msgs = [m for m in thread["messages"] if not is_ai(m) and (m.get("post") is True or POST_PREFIX.match(m["text"]))]
    if message_id:
        msgs = [m for m in msgs if m["id"] == message_id]
    if not msgs:
        raise ValueError("no message marked for posting in this thread")
    m = msgs[-1]
    return m, POST_PREFIX.sub("", m["text"], count=1).strip()


def age_seconds(at):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(at.replace("Z", "+00:00"))).total_seconds()
    except (ValueError, AttributeError):
        return float("inf")


def same_commit(a, b):
    a, b = a.lower(), b.lower()
    return len(a) >= 7 and len(b) >= 7 and (a.startswith(b) or b.startswith(a))


def find_thread(data, thread_id):
    t = next((t for t in data.get("threads", []) if t["id"] == thread_id), None)
    if not t:
        raise ValueError("thread not found")
    return t


def start_post(cfg, meta, thread_id, message_id):
    """Under the lock: pick the message, check it may go out, leave a `posting` marker. Returns (done, message, body, thread)."""
    s = meta["slug"]
    with locked(cfg, s):
        data = load_state(cfg, s)
        t = find_thread(data, thread_id)
        m, body = post_body(t, message_id)
        if t.get("posted") and t["posted"].get("message_id") == m["id"]:
            return t["posted"], m, body, t
        if m["id"] in (t.get("posted_messages") or {}):
            return {**t["posted_messages"][m["id"]], "message_id": m["id"], "body": body}, m, body, t
        if not body:
            raise ValueError("nothing to post")
        marker = t.get("posting")
        if marker and marker.get("message_id") == m["id"] and age_seconds(marker.get("at")) < POSTING_TTL:
            raise PostConflict("already posting")
        if t.get("commit") and not same_commit(t["commit"], meta["head_sha"]):
            raise PostConflict(f"This comment was written on an older commit ({t['commit'][:7]}); open the PR again to comment on the current code.")
        t["posting"] = {"message_id": m["id"], "at": now()}
        save_state(cfg, s, data)
        return None, m, body, dict(t)


def finish_post(cfg, meta, thread_id, m, body, res):
    s = meta["slug"]
    with locked(cfg, s):
        data = load_state(cfg, s)
        t = find_thread(data, thread_id)
        if res:
            at = now()
            t.setdefault("posted_messages", {})[m["id"]] = {"url": res["url"], "id": res["id"], "at": at}
            t["posted"] = {**res, "at": at, "message_id": m["id"], "body": body}
        if (t.get("posting") or {}).get("message_id") == m["id"]:
            del t["posting"]
        save_state(cfg, s, data)
        return t.get("posted")


def post_thread(cfg, meta, thread_id, message_id=None):
    done, m, body, t = start_post(cfg, meta, thread_id, message_id)
    if done:
        return done
    try:
        res = github.post_comment(meta["repo"], meta["pr"], meta["head_sha"], t, body)
    except BaseException:
        finish_post(cfg, meta, thread_id, m, body, None)
        raise
    return finish_post(cfg, meta, thread_id, m, body, res)
