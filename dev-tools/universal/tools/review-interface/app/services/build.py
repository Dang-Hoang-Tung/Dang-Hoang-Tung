import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from app.config import dirs, slug
from app.services import diff, events
from app.services import git, github, manifest, models
from app.services.adapters import team_reviewer
from app.services.insights import load as load_insights
from app.services.shell import run
from app.services.state import load_state
from app.ui.pages import queue_page, review_page


def user_name(cfg):
    if cfg.get("user_name"):
        return cfg["user_name"]
    for cmd in (["git", "config", "user.name"], ["gh", "api", "user", "-q", ".name // .login"]):
        try:
            name = run(*cmd).split()
            if name:
                return name[0]
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
    return "there"


def fetch_diff(pr):
    if git.has_clone(pr["source"]):
        return git.fetch_diff(pr)
    return github.fetch_api_diff(pr)


def fetch_diffs(prs):
    diffs = {}
    for pr in prs:
        try:
            diffs[pr["repo"], pr["number"]] = fetch_diff(pr)
        except subprocess.CalledProcessError as e:
            print(f"  {pr['repo']}#{pr['number']}: failed: {(e.stderr or str(e)).strip()[:300]}", file=sys.stderr)
    return diffs


def _difft_spans(pr, base, f):
    pair = git.file_pair(pr, base, f["path"])
    data = pair and diff.run_difft(*pair, f["path"])
    spans = diff.difft_spans(f["rows"], data) if data else None
    moved = f.get("moved") or {}
    return {i: r for i, r in spans.items() if str(i) not in moved} if spans is not None else None


def refine_spans(pr, model):
    base = git.has_clone(pr["source"]) and shutil.which("difft") and git.merge_base(pr)
    if not base:
        return
    files = [f for f in model["files"] if not f["binary"] and {"del", "add"} <= {r[0] for r in f["rows"]}]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for f, spans in zip(files, pool.map(lambda f: _difft_spans(pr, base, f), files)):
            if spans is not None:
                f["spans"] = spans


def build_pr(cfg, pr, diff_text, name):
    d = dirs(cfg)
    s = slug(pr["repo"], pr["number"])
    ins, status = load_insights(cfg, pr["repo"], pr["number"], pr["headRefOid"])
    model = models.review_model(cfg, pr, diff_text, ins, status, name)
    refine_spans(pr, model)
    summary = models.pr_summary(model, status)
    (d["pages"] / f"{s}.html").write_text(review_page.render(model))
    (d["pages"] / f"{s}.json").write_text(json.dumps(summary))
    (d["diffs"] / f"{s}.diff").write_text(diff_text)
    return summary


def queue_items(cfg, entries):
    d = dirs(cfg)
    items = []
    for e in entries:
        try:
            summary = json.loads((d["pages"] / f"{e['slug']}.json").read_text())
        except (OSError, ValueError):
            print(f"  {e['slug']}: no page summary; left out of the queue page", file=sys.stderr)
            continue
        items.append(models.queue_item(summary, e["requested_at"], load_state(cfg, e["slug"])))
    return items


def build(cfg, only=None, source="cli"):
    d = dirs(cfg)
    prs = github.list_pending(cfg, only)
    name = user_name(cfg)
    diffs = fetch_diffs(prs)
    previous = {e["slug"]: e for e in manifest.read_manifest(cfg)["prs"] if "slug" in e}
    merged = dict(previous) if only else {}
    for pr in prs:
        s = slug(pr["repo"], pr["number"])
        if s in previous:
            merged[s] = previous[s]
    ok = [pr for pr in prs if (pr["repo"], pr["number"]) in diffs]
    team_reviewer.sync_briefs(cfg, ok)
    for pr in ok:
        try:
            summary = build_pr(cfg, pr, diffs[pr["repo"], pr["number"]], name)
            state = load_state(cfg, summary["slug"])
            requested = github.requested_at(cfg, pr)
            merged[summary["slug"]] = manifest.build_entry(cfg, summary, requested, state)
        except Exception as e:
            print(f"  {pr['repo']}#{pr['number']}: build failed: {e}", file=sys.stderr)
            continue
        print(f"  {pr['repo']}#{pr['number']}: {summary['files']} files, insights {summary['insights_status']}")
    entries = list(merged.values())
    (d["pages"] / "index.html").write_text(queue_page.render(models.queue_model(queue_items(cfg, entries), name)))
    written = manifest.write_manifest(cfg, entries)
    events.append(cfg, events.rebuild_event(previous, entries, source, partial=bool(only)))
    return written
