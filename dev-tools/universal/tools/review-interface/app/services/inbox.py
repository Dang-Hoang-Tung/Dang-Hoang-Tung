"""A log of what the reviewer writes, so an AI can `tail -F` it and answer at once."""
import json

from app.config import dirs, now
from app.services import state

KEEP = 500


def path(cfg):
    return dirs(cfg)["root"] / "inbox.jsonl"


def append(cfg, entries):
    if not entries:
        return
    f = path(cfg)
    with f.open("a") as out:
        out.write("".join(json.dumps(e, separators=(",", ":")) + "\n" for e in entries))
    lines = f.read_text().splitlines()
    if len(lines) > 2 * KEEP:
        f.write_text("\n".join(lines[-KEEP:]) + "\n")


def new_user_messages(before, after):
    """(thread, message) pairs in `after` and not in `before`, written by the reviewer."""
    seen = {(t["id"], m["id"]) for t in before.get("threads", []) for m in t.get("messages", [])}
    return [(t, m) for t in after.get("threads", []) for m in t.get("messages", [])
            if (t["id"], m["id"]) not in seen and not state.is_ai(m)]


def entries_for(slug, before, after):
    pr = int(slug.rsplit("-", 1)[1]) if slug.rsplit("-", 1)[-1].isdigit() else None
    return [{"at": now(), "slug": slug, "pr": pr, "thread": t["id"],
             "kind": "chat" if t["id"] == "chat" else "comment",
             "path": t.get("path"), "line": t.get("line"), "text": m["text"]}
            for t, m in new_user_messages(before, after)]
