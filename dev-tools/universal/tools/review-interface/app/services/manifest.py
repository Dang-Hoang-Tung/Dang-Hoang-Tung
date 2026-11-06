import json

from app.config import ROOT, dirs, now
from app.services.state import atomic_write, state_path, waiting_threads

SUMMARY_KEYS = ("slug", "repo", "pr", "title", "url", "author", "head_sha", "ci", "draft", "base", "added", "deleted", "files",
                "effort", "minutes", "minutes_source", "verdict", "risk", "findings")


def read_manifest(cfg):
    try:
        return json.loads((dirs(cfg)["root"] / "manifest.json").read_text())
    except (OSError, ValueError):
        return {"prs": []}


def manifest_entry(cfg, s):
    return next((p for p in read_manifest(cfg)["prs"] if p["slug"] == s), None)


def build_entry(cfg, summary, requested_at, state):
    d = dirs(cfg)
    s = summary["slug"]
    flat = {**summary, "pr": summary["number"]}
    return {**{k: flat[k] for k in SUMMARY_KEYS},
            "page": str(d["pages"] / f"{s}.html"), "state_file": str(state_path(cfg, s)),
            "insights_file": str(d["insights"] / f"{s}.json"), "insights_status": summary["insights_status"],
            "requested_at": requested_at, "diff_file": str(d["diffs"] / f"{s}.diff"),
            "threads": len(state.get("threads", [])), "waiting_threads": len(waiting_threads(state))}


def write_manifest(cfg, entries):
    d = dirs(cfg)
    manifest = {"schema": "review-manifest/1", "generated_at": now(), "config": cfg["config_path"],
                "contract": str(ROOT / "CONTRACT.md"), "dirs": {k: str(v) for k, v in d.items()}, "prs": entries}
    atomic_write(d["root"] / "manifest.json", json.dumps(manifest, indent=2))
    return manifest
