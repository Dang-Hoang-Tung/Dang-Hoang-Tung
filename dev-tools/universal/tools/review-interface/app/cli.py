"""Review interface: local pages for reviewing pull requests, with optional AI insights.

  review.py [build] [PR ...]      find pending reviews (or the given PRs), build pages, start the helper, open the queue
  review.py build --no-open       build only
  review.py serve                 start the local helper and print the queue link
  review.py paths                 print where pages, state, insights and diffs live (for an AI)
  review.py ai list               threads waiting for a reply
  review.py ai reply SLUG THREAD TEXT
  review.py ai post SLUG THREAD   post the thread's latest message marked for posting to GitHub

PRs can be given as 123 (first configured repo) or owner/repo#123. Every command takes --config PATH first.
"""
import argparse
import json
import secrets
import subprocess
import sys
import time
import urllib.request

from app.config import ROOT, dirs, load_config, now
from app.services import build as builder
from app.services import events, manifest, posting, state

COMMANDS = ("build", "serve", "paths", "ai")


def parse_pr(arg):
    if "#" in arg:
        repo, n = arg.split("#")
        return repo, int(n)
    return None, int(arg)


def server_info(info_file):
    try:
        info = json.loads(info_file.read_text())
        with urllib.request.urlopen(f'http://127.0.0.1:{info["port"]}/api/ping', timeout=1) as r:
            return info if r.status == 200 else None
    except (OSError, ValueError, KeyError):
        return None


def ensure_server(cfg):
    d = dirs(cfg)
    info_file = d["root"] / "server.json"
    info = server_info(info_file)
    if info:
        return info
    log = open(d["root"] / "server.log", "a")
    subprocess.Popen([sys.executable, "-m", "app.server.http", "--config", cfg["config_path"]],
                     stdout=log, stderr=log, stdin=subprocess.DEVNULL, start_new_session=True, cwd=str(ROOT))
    for _ in range(50):
        time.sleep(0.1)
        info = server_info(info_file)
        if info:
            return info
    sys.exit(f"the review helper did not start; see {d['root'] / 'server.log'}")


def queue_url(info, page="index.html"):
    return f"http://127.0.0.1:{info['port']}/?t={info['token']}&next={page}"


def ai_list(cfg):
    found = False
    for p in manifest.read_manifest(cfg)["prs"]:
        for t in state.waiting_threads(state.load_state(cfg, p["slug"])):
            found = True
            where = (t.get("path") or "general") + (f':{t["start_line"]}-{t["line"]}' if t.get("line") else "")
            print(f'{p["slug"]} {t["id"]} {where}{" note=" + t["noteKey"] if t.get("noteKey") else ""}')
            for msg in t["messages"]:
                print(f'    {"ai" if state.is_ai(msg) else "me"}: {msg["text"]}')
    if not found:
        print("no threads waiting")


def ai_reply(cfg, s, thread_id, text):
    with state.locked(cfg, s):
        data = state.load_state(cfg, s)
        t = next((t for t in data.get("threads", []) if t["id"] == thread_id), None)
        if not t:
            sys.exit("thread not found")
        t["messages"].append({"id": secrets.token_hex(5), "who": state.AI, "text": text, "at": now()})
        state.save_state(cfg, s, data)
    print("replied")


def ai_post(cfg, s, thread_id):
    meta = manifest.manifest_entry(cfg, s)
    if not meta:
        sys.exit("PR not in the current build; run review.py build first")
    try:
        print(posting.post_thread(cfg, meta, thread_id)["url"])
    except ValueError as e:
        sys.exit(str(e))


def build_parser():
    ap = argparse.ArgumentParser(description="Local PR review pages.")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    b.add_argument("prs", nargs="*")
    b.add_argument("--no-open", action="store_true")
    b.add_argument("--source", default="cli", help=argparse.SUPPRESS)
    sub.add_parser("serve")
    sub.add_parser("paths")
    ai = sub.add_parser("ai")
    ai_sub = ai.add_subparsers(dest="ai_cmd", required=True)
    ai_sub.add_parser("list")
    ai_sub.add_parser("changes", help="what changed in the latest rebuild or refresh")
    r = ai_sub.add_parser("reply")
    r.add_argument("slug")
    r.add_argument("thread")
    r.add_argument("text")
    p = ai_sub.add_parser("post")
    p.add_argument("slug")
    p.add_argument("thread")
    return ap


def normalise_argv(argv):
    pre = argv[:2] if argv[:1] == ["--config"] else []
    rest = argv[len(pre):]
    if not rest or (rest[0] not in COMMANDS and rest[0] not in ("-h", "--help")):
        rest = ["build"] + rest
    return pre + rest


def run_build(cfg, a):
    m = builder.build(cfg, [parse_pr(x) for x in a.prs] or None, source=a.source)
    print(f"built {len(m['prs'])} page(s). For an AI: {dirs(cfg)['root'] / 'manifest.json'}")
    if not a.no_open:
        info = ensure_server(cfg)
        hit = [p for p in m["prs"] if len(a.prs) == 1 and p["pr"] == parse_pr(a.prs[0])[1]]
        page = f"{hit[0]['slug']}.html" if hit else "index.html"
        subprocess.run(["open", queue_url(info, page)])


def print_paths(cfg):
    d = dirs(cfg)
    print(json.dumps({"manifest": str(d["root"] / "manifest.json"), "contract": str(ROOT / "CONTRACT.md"),
                      **{k: str(v) for k, v in d.items()}}, indent=2))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    a = build_parser().parse_args(normalise_argv(argv))
    cfg = load_config(a.config)
    if a.cmd == "build":
        run_build(cfg, a)
    elif a.cmd == "serve":
        print(queue_url(ensure_server(cfg)))
    elif a.cmd == "paths":
        print_paths(cfg)
    elif a.cmd == "ai":
        if a.ai_cmd == "list":
            ai_list(cfg)
        elif a.ai_cmd == "changes":
            print(json.dumps(events.latest(cfg) or {"type": "none", "note": "no rebuild recorded yet"}, indent=2))
        elif a.ai_cmd == "reply":
            ai_reply(cfg, a.slug, a.thread, a.text)
        elif a.ai_cmd == "post":
            ai_post(cfg, a.slug, a.thread)


if __name__ == "__main__":
    main()
