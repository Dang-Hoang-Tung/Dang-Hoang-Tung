import fcntl
import json
import os
import re
import sys
import tempfile
import time
from contextlib import contextmanager

from app.config import dirs

AI = "ai"


def state_path(cfg, s):
    if not re.fullmatch(r"[\w.-]+-\d+", s):
        raise ValueError("bad slug")
    return dirs(cfg)["state"] / f"{s}.json"


@contextmanager
def locked(cfg, s):
    """Exclusive lock for one PR's state, shared across threads and processes. Do not nest."""
    path = state_path(cfg, s).with_suffix(".lock")
    with open(path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def load_state(cfg, s):
    path = state_path(cfg, s)
    try:
        text = path.read_text()
    except OSError:
        return {}
    try:
        data = json.loads(text or "{}")
        if isinstance(data, dict):
            return data
    except ValueError:
        pass
    aside = path.with_name(f"{s}.corrupt-{time.strftime('%Y%m%dT%H%M%S')}-{time.time_ns() % 10**6:06d}.json")
    os.replace(path, aside)
    print(f"review state for {s} was not valid JSON; moved to {aside.name}", file=sys.stderr)
    return {}


def save_state(cfg, s, data):
    atomic_write(state_path(cfg, s), json.dumps(data, indent=2))


def _is_dict_of_dicts(v):
    return isinstance(v, dict) and all(isinstance(x, dict) for x in v.values())


def validate_state(mine):
    if not isinstance(mine, dict):
        raise ValueError("state must be a JSON object")
    threads = mine.get("threads", [])
    if not isinstance(threads, list):
        raise ValueError("threads must be a list")
    for t in threads:
        if not (isinstance(t, dict) and isinstance(t.get("id"), str) and isinstance(t.get("messages"), list)):
            raise ValueError("each thread needs a string id and a messages list")
        for m in t["messages"]:
            if not (isinstance(m, dict) and all(isinstance(m.get(k), str) for k in ("id", "at", "text"))):
                raise ValueError("each message needs string id, at and text")
            if "post" in m and not isinstance(m["post"], bool):
                raise ValueError("message post must be true or false")
    for key in ("read", "checked"):
        if not _is_dict_of_dicts(mine.get(key, {})):
            raise ValueError(f"{key} must be an object of objects")


def _later(a, b):
    out = dict(a or {})
    for k, v in (b or {}).items():
        if k not in out or (v.get("at") or "") > (out[k].get("at") or ""):
            out[k] = v
    return out


def _merge_thread(d, t):
    ids = {m.get("id") for m in d.setdefault("messages", [])}
    d["messages"] += [m for m in t["messages"] if m["id"] not in ids]
    d["messages"].sort(key=lambda m: m.get("at") or "")
    if (t.get("resolvedAt") or "") > (d.get("resolvedAt") or ""):
        d["resolved"], d["resolvedAt"] = t.get("resolved"), t.get("resolvedAt")
    d["posted"] = d.get("posted") or t.get("posted")
    if d.get("posted_messages") or t.get("posted_messages"):
        d["posted_messages"] = {**(t.get("posted_messages") or {}), **(d.get("posted_messages") or {})}


def merge_state(disk, mine):
    validate_state(mine)
    threads = {t["id"]: t for t in disk.get("threads", [])}
    for t in mine.get("threads", []):
        if t["id"] in threads:
            _merge_thread(threads[t["id"]], t)
        else:
            threads[t["id"]] = t
    out = {**disk, **{k: v for k, v in mine.items() if k not in ("threads", "read", "checked", "approval")}}
    out.update(threads=list(threads.values()), read=_later(disk.get("read"), mine.get("read")), checked=_later(disk.get("checked"), mine.get("checked")))
    return out


def is_ai(msg):
    """`claude` is the legacy value of `who`; new messages use `ai`."""
    return msg.get("who") in (AI, "claude")


def is_posted(thread, message_id):
    posted = thread.get("posted") or {}
    return posted.get("message_id") == message_id or message_id in (thread.get("posted_messages") or {})


def is_approved(state, head_sha):
    commit = (state.get("approval") or {}).get("commit") or ""
    return len(commit) >= 7 and len(head_sha or "") >= 7 and (commit.startswith(head_sha) or head_sha.startswith(commit))


def waiting_threads(state):
    out = []
    for t in state.get("threads", []):
        if t.get("resolved") or t.get("synced") or not t.get("messages"):
            continue
        last = t["messages"][-1]
        if not is_ai(last) and not is_posted(t, last["id"]):
            out.append(t)
    return out
