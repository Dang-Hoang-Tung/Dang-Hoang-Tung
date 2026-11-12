import hashlib

from app.config import slug
from app.domain import LAYERS, SEVERITIES, worst
from app.services import diff as diffs
from app.services import git, github, tokdiff, tree
from app.services.state import is_approved, waiting_threads

ITEM_KEYS = ("slug", "number", "title", "url", "author", "head_sha", "ci", "draft", "effort", "minutes", "minutes_source",
             "added", "deleted", "files", "verdict", "risk", "findings", "has_insights", "summary")


def resolve_path(paths, ref):
    if not ref:
        return None
    ref = ref.strip()
    if ref.startswith("./"):
        ref = ref[2:]
    if ref in paths:
        return ref
    for hits in ([p for p in paths if p.endswith("/" + ref)], [p for p in paths if p.split("/")[-1] == ref.split("/")[-1]]):
        if hits:
            return hits[0] if len(hits) == 1 else None
    return None


def build_notes(ins, paths):
    notes = []
    for r in (ins or {}).get("recommendations", []):
        path = resolve_path(paths, r["path"])
        key = r["id"] or hashlib.sha1(f'{r["severity"]}|{r["title"]}|{r["path"]}'.encode()).hexdigest()[:10]
        notes.append({"key": key, "kind": r["severity"], "title": r["title"], "body": r["body"], "comment": r["draft_comment"],
                      "file": path, "start": r["start_line"] if path else None, "end": r["end_line"] if path else None,
                      "rows": [], "endRow": None})
    return notes


def attach_rows(notes, files, idx):
    for nt in notes:
        if not (nt["file"] and nt["start"] is not None):
            continue
        f = files[idx[nt["file"]]]
        stop = nt["end"] or nt["start"]
        hit = [ri for ri, r in enumerate(f["rows"]) if r[0] != "hunk" and r[2] is not None and nt["start"] <= r[2] <= stop]
        nt["rows"] = [f'r{f["idx"]}-{ri}' for ri in hit]
        nt["endRow"] = nt["rows"][-1] if nt["rows"] else None


def group_by_file(notes):
    by_file = {}
    for nt in notes:
        if nt["file"]:
            by_file.setdefault(nt["file"], []).append(nt)
    return by_file


def note_model(nt, idx):
    return {**nt, "file": idx[nt["file"]] if nt["file"] else None}


def nest_tree(t, idx):
    return {"name": t["name"], "file": idx[t["file"]] if t["file"] else None, "kids": [nest_tree(k, idx) for k in t["kids"]]}


def leaf_order(nodes):
    out = []
    for t in nodes:
        if t["file"] is not None:
            out.append(t["file"])
        out += leaf_order(t["kids"])
    return out


def display_order(top_nodes, files):
    return leaf_order(top_nodes)


def effort_of(added):
    return "Small" if added < 100 else "Medium" if added < 400 else "Large"


def estimate_minutes(added, risk):
    return max(2, round(added / 50)) + (5 if risk in ("High", "Medium") else 0)


def is_stacked(pr):
    """Based on another branch rather than the repo's default (main/master when the default is unknown)."""
    base = pr.get("baseRefName")
    default = pr.get("defaultBranch")
    return bool(base) and (base != default if default else base not in ("main", "master"))


def build_banners(pr, ins, ins_status):
    banners = []
    if pr.get("isDraft"):
        banners.append({"type": "draft"})
    if is_stacked(pr):
        banners.append({"type": "stacked", "base": pr["baseRefName"]})
    if ins_status == "stale":
        banners.append({"type": "stale", "from": ins["head_sha"][:7], "to": pr["headRefOid"][:7]})
    if ins_status.startswith("invalid"):
        banners.append({"type": "invalid", "reason": ins_status[9:]})
    return banners


def build_summary(pr, ins, summ, totals):
    risk = summ.get("risk") or ""
    minutes = summ.get("minutes") or estimate_minutes(totals["added"], risk)
    verdict = (summ.get("verdict") or "").split(". ")[0].rstrip(".")[:40]
    return {
        "has_insights": bool(ins), "verdict": verdict, "risk": risk, "risk_note": summ.get("risk_note") or "",
        "minutes": minutes, "minutes_source": "insights" if summ.get("minutes") else "estimate",
        "tldr": (summ.get("tldr") or []) if ins else [], "questions": (summ.get("questions") or []) if ins else [],
        "what": summ.get("what") or "",
        "check": [{"severity": r.get("severity"), "title": r.get("title") or "", "path": r.get("path"), "line": r.get("start_line")}
                  for r in (ins or {}).get("recommendations", []) if r.get("severity") != "look"],
        "description": pr.get("body") or None,
    }


def build_totals(files):
    real = [f for f in files if not f["gen"]]
    added, deleted = sum(f["a"] for f in real), sum(f["d"] for f in real)
    return {"added": added, "deleted": deleted, "files": len(files), "added_all": sum(f["a"] for f in files),
            "deleted_all": sum(f["d"] for f in files), "effort": effort_of(added)}


def file_model(f, by_file, moved, strong=({}, ())):
    ns = by_file.get(f["path"], [])
    return {**{k: f[k] for k in ("noeol", "mode") if k in f},
            "idx": f["idx"], "path": f["path"], "a": f["a"], "d": f["d"], "gen": f["gen"], "layer": diffs.layer_of(f),
            "hash": diffs.file_hash(f["rows"]), "binary": f["binary"],
            "status": f.get("status", "modified"), "old_path": f.get("old_path"), "kind": worst(x["kind"] for x in ns), "notes": [x["key"] for x in ns],
            "rows": [list(r) for r in f["rows"]], "moved": moved, "spans": strong[0], "quiet": sorted(strong[1])}


def review_model(cfg, pr, diff_text, ins, ins_status, user_name):
    repo, n = pr["repo"], pr["number"]
    files = diffs.parse_diff(diff_text, cfg["generated"])
    attr_gen = git.generated_paths(pr, [f["path"] for f in files if not f["gen"]])
    for f in files:
        f["gen"] = f["gen"] or f["path"] in attr_gen
    moves = diffs.find_moves(files, getattr(diff_text, "moved", None))
    text_files = [f for f in files if not f["binary"] and not f["gen"]]
    strong = dict(zip((f["idx"] for f in text_files), tokdiff.strong_spans(text_files)))
    paths = [f["path"] for f in files]
    idx = {f["path"]: f["idx"] for f in files}
    notes = build_notes(ins, paths)
    attach_rows(notes, files, idx)
    by_file = group_by_file(notes)
    root = tree.build_tree(paths, repo.split("/")[1])
    top_nodes = [nest_tree(k, idx) for k in root["kids"]]
    file_stats = {f["path"]: {"idx": f["idx"], "a": f["a"], "d": f["d"], "gen": f["gen"], "status": f.get("status", "modified"), "notes": by_file.get(f["path"], [])} for f in files}
    totals = build_totals(files)
    return {
        "pr": {"repo": repo, "number": n, "slug": slug(repo, n), "title": pr["title"], "url": pr["url"],
               "author": (pr.get("author") or {}).get("login", ""), "head_sha": pr["headRefOid"], "base": pr.get("baseRefName"),
               "head": pr.get("headRefName"), "stacked": is_stacked(pr),
               "draft": bool(pr.get("isDraft")), "ci": github.ci_state(pr.get("statusCheckRollup")), "created": pr.get("createdAt")},
        "user": user_name, "ai_name": cfg["ai_name"], "layers": LAYERS,
        "files": [file_model(f, by_file, moves[f["idx"]], strong.get(f["idx"], ({}, ()))) for f in files],
        "order": display_order(top_nodes, files),
        "tree": top_nodes,
        "tree_layout": tree.layout(root, file_stats),
        "tree_layout_full": tree.layout(tree.build_tree(paths, repo.split("/")[1], collapse=False), file_stats, aligned=True),
        "notes": [note_model(x, idx) for x in sorted(notes, key=lambda x: SEVERITIES.index(x["kind"]))],
        "summary": build_summary(pr, ins, (ins or {}).get("summary", {}), totals),
        "totals": totals,
        "banners": build_banners(pr, ins, ins_status),
    }


def pr_summary(model, ins_status):
    pr, totals, summ = model["pr"], model["totals"], model["summary"]
    notes = model["notes"]
    return {
        "slug": pr["slug"], "repo": pr["repo"], "number": pr["number"], "title": pr["title"], "url": pr["url"],
        "author": pr["author"], "head_sha": pr["head_sha"], "base": pr["base"], "ci": pr["ci"], "draft": pr["draft"], "created": pr.get("created"),
        "effort": totals["effort"], "minutes": summ["minutes"], "minutes_source": summ["minutes_source"],
        "added": totals["added"], "deleted": totals["deleted"], "files": totals["files"],
        "verdict": summ["verdict"], "risk": summ["risk"],
        "findings": {k: sum(1 for x in notes if x["kind"] == k) for k in SEVERITIES if any(x["kind"] == k for x in notes)},
        "has_insights": summ["has_insights"], "insights_status": ins_status,
        "summary": {"tldr": summ["tldr"], "questions": summ["questions"], "description": summ["description"]},
    }


def queue_item(summary, requested_at, state):
    item = {k: summary[k] for k in ITEM_KEYS}
    item.update(requested_at=requested_at, created=summary.get("created") or requested_at, threads=len(state.get("threads", [])), open_threads=len(waiting_threads(state)),
                approved=is_approved(state, summary["head_sha"]))
    return item


def avatar_url(login, size=48):
    return f"https://github.com/{login.split('/')[-1]}.png?size={size}"


def queue_model(items, user_name):
    by_author = {}
    for it in items:
        by_author.setdefault(it["author"] or "unknown", []).append(it)
    opened = lambda it: it.get("created") or it["requested_at"]
    authors = sorted(by_author, key=lambda a: (-len(by_author[a]), min(opened(it) for it in by_author[a]), a.lower()))
    return {
        "user": user_name,
        "total_minutes": sum(it["minutes"] for it in items),
        "authors": authors,
        "buckets": [{"author": a, "avatar": avatar_url(a), "items": sorted(by_author[a], key=opened)} for a in authors],
    }
