"""A log of rebuilds, so an AI knows which of its reads on PRs may be out of date."""
import json

from app.config import dirs, now

KEEP = 500


def path(cfg):
    return dirs(cfg)["root"] / "events.jsonl"


def rebuild_event(previous, entries, source, partial):
    """What changed between the previous manifest entries (by slug) and the new ones."""
    current = {e["slug"]: e for e in entries}
    pick = lambda e: {"slug": e["slug"], "pr": e["pr"], "title": e["title"]}
    changed = [s for s in current if s not in previous or previous[s]["head_sha"] != current[s]["head_sha"]]
    return {
        "type": "rebuild", "source": source, "at": now(), "partial": partial,
        "check": [current[s]["pr"] for s in changed],
        "new": [{**pick(e), "head_sha": e["head_sha"]} for s, e in current.items() if s not in previous],
        "moved": [{**pick(e), "from": previous[s]["head_sha"], "to": e["head_sha"]}
                  for s, e in current.items() if s in previous and previous[s]["head_sha"] != e["head_sha"]],
        "gone": [] if partial else [s for s in previous if s not in current],
        "needs_insights": [{**pick(e), "status": e["insights_status"]}
                           for e in entries if e.get("insights_status") != "current"],
    }


def append(cfg, event):
    """Appends, so `tail -F` sees only the new line; trims only when the file has doubled."""
    f = path(cfg)
    with f.open("a") as out:
        out.write(json.dumps(event) + "\n")
    lines = f.read_text().splitlines()
    if len(lines) > 2 * KEEP:
        f.write_text("\n".join(lines[-KEEP:]) + "\n")


def latest(cfg):
    f = path(cfg)
    if not f.exists():
        return None
    lines = [l for l in f.read_text().splitlines() if l.strip()]
    return json.loads(lines[-1]) if lines else None
