#!/usr/bin/env python3
"""Call our API with the minted token. GET runs straight away; anything else needs --apply.

Usage: api.py <METHOD> <service-prefix> <path> [--json '<body>' | --json @file.json] [--apply]
e.g.   api.py GET items health
       api.py POST items search --json '{"query":"x"}' --apply
Base URL: from the local env file named in workspace/config.json. Token: saved by the workspace's token script
(~/.claude/agent-files/shared/qa/token).
"""
import argparse
import json
import pathlib
import urllib.error
import urllib.request
from _lib import require_config, AGENT_FILES, APP, LOCAL, apply_flag, env_file, fail, out
require_config()

apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("method")
p.add_argument("service")
p.add_argument("path")
p.add_argument("--json", dest="body")
a = p.parse_args()

method = a.method.upper()
root = env_file(APP / LOCAL["env_file"]).get(LOCAL["api_root_key"])
if not root:
    fail(f"{LOCAL['api_root_key']} missing from {LOCAL['env_file']}")
url = f"{root.rstrip('/')}/{a.service.strip('/')}/{a.path.lstrip('/')}"

if method != "GET" and not apply:
    out({"ok": True, "applied": False, "would_call": f"{method} {url}", "note": "re-run with --apply"})
    raise SystemExit

token_file = AGENT_FILES / "shared" / "qa" / "token"
if not token_file.exists():
    fail("no token: run the workspace token script first (see workspace/stack.md)")
data = None
if a.body:
    raw = pathlib.Path(a.body[1:]).read_text() if a.body.startswith("@") else a.body
    data = json.dumps(json.loads(raw)).encode()
req = urllib.request.Request(url, data=data, method=method, headers={
    "authorization": f"Bearer {token_file.read_text().strip()}", "content-type": "application/json"})
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        status, text = r.status, r.read().decode()
except urllib.error.HTTPError as e:
    status, text = e.code, e.read().decode()
except urllib.error.URLError as e:
    fail(f"request failed: {e.reason}", url=url)
try:
    body = json.loads(text)
except json.JSONDecodeError:
    body = text[:2000]
out({"ok": 200 <= status < 300, "status": status, "url": url, "body": body})
