"""Local helper: serves review pages, saves review state, posts comments to GitHub.

Listens on 127.0.0.1 only. Every request needs the session cookie set from the ?t= link.
Stops after `idle_hours` without requests. State files untouched for `keep_days` are pruned on start.
Run from the repo root: python3 -m app.server.http --config PATH
"""
import argparse
import copy
import json
import sys
import subprocess
import os
import secrets
import threading
import time
import traceback
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from app.config import ROOT, dirs, load_config
from app.ui.components import file_section
from app.services import approval, events, fullfile, resolve, gh_sync, inbox, manifest, posting, state

MAX_BODY = 2 * 1024 * 1024
LOCAL_HOSTS = ("127.0.0.1", "localhost")
TYPES = {".html": "text/html; charset=utf-8", ".json": "application/json", ".css": "text/css", ".js": "text/javascript"}


class Reject(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code, self.message = code, message


def same(a, b):
    try:
        return secrets.compare_digest(a.encode(), b.encode())
    except UnicodeError:
        return False


REFRESH_LOCK = threading.Lock()
SYNC_EVERY = 30


def start_refresh(cfg, status):
    """Rebuild every page in the background; one refresh at a time."""
    with REFRESH_LOCK:
        if status["running"]:
            return
        status.update(running=True, error=None, started=time.time())

    def work():
        # A fresh process, so a refresh always uses the code on disk, not what this helper loaded at start.
        cmd = [sys.executable, "-m", "app.cli", "--config", cfg["config_path"], "build", "--no-open", "--source", "refresh"]
        try:
            run = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=900)
            if run.returncode:
                status["error"] = (run.stderr or run.stdout).strip()[-300:] or f"build exited {run.returncode}"
            status["changes"] = events.latest(cfg)
        except (OSError, subprocess.TimeoutExpired) as e:
            status["error"] = str(e)[:300]
        finally:
            status.update(running=False, finished=time.time())
    threading.Thread(target=work, daemon=True).start()


def cookie_name(port):
    """Cookies ignore ports, so each helper uses its own name and two helpers can't log each other out."""
    return f"rt{port}"


def make_handler(cfg, token, touch):
    refresh = {"running": False, "error": None, "started": None, "finished": None}
    pages = dirs(cfg)["pages"].resolve()
    synced_at, sync_lock = {}, threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        server_version = "review-interface"

        def log_message(self, *args):
            pass

        def _send(self, code, body=b"", ctype="text/plain; charset=utf-8", headers=None):
            if isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj), "application/json")

        def _ok_request(self, write=False):
            touch()
            host = self.headers.get("Host") or ""
            if host.split(":")[0] not in LOCAL_HOSTS:
                self._send(403, "bad host")
                return False
            c = SimpleCookie(self.headers.get("Cookie") or "")
            name = cookie_name(self.server.server_address[1])
            if not (name in c and same(c[name].value, token)):
                self._send(403, "Open the review queue with review.py.")
                return False
            if write:
                if self.headers.get("Origin") != "http://" + host:
                    self._send(403, "bad origin")
                    return False
                if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "application/json":
                    self._json(415, {"error": "Content-Type must be application/json"})
                    return False
            return True

        def _body(self):
            try:
                size = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                raise Reject(400, "bad Content-Length")
            if size > MAX_BODY:
                self.close_connection = True
                raise Reject(413, "request body too large")
            try:
                return json.loads(self.rfile.read(size) or b"{}")
            except ValueError:
                raise Reject(400, "body is not valid JSON")

        def _guard(self, fn):
            try:
                fn()
            except Reject as e:
                self._json(e.code, {"error": e.message})
            except Exception:
                traceback.print_exc()
                try:
                    self._json(500, {"error": "internal error"})
                except OSError:
                    pass

        def _token_login(self, q):
            touch()
            if not same(q["t"][0], token):
                return self._send(403, "bad token")
            nxt = q.get("next", ["index.html"])[0].lstrip("/")
            if "/" in nxt or ".." in nxt:
                nxt = "index.html"
            return self._send(302, headers={"Location": "/" + nxt, "Set-Cookie": f"{cookie_name(self.server.server_address[1])}={token}; Path=/; HttpOnly; SameSite=Strict"})

        def _get_state(self, path):
            try:
                return self._json(200, state.load_state(cfg, path.rsplit("/", 1)[1]))
            except ValueError:
                return self._send(400, "bad slug")

        def _repo_call(self, s, fn):
            meta = manifest.manifest_entry(cfg, s)
            if not meta:
                return self._json(404, {"error": "This PR is not in the current build. Run review.py again."})
            try:
                return self._json(200, fn(resolve.clone_for(cfg, meta["repo"]), meta["head_sha"]))
            except resolve.NotFound as e:
                return self._json(404, {"error": str(e)})
            except subprocess.SubprocessError as e:
                return self._json(502, {"error": (getattr(e, "stderr", "") or str(e)).strip()[:300]})

        def _resolve(self, s, q):
            frm, spec = q.get("from", [""])[0], q.get("spec", [""])[0]
            if not frm or not spec:
                return self._json(400, {"error": "from and spec are required"})

            def go(clone, sha):
                hit = resolve.resolve(clone, sha, frm, spec)
                if not hit:
                    raise resolve.NotFound(f"Can't find {spec} in the repo")
                return {"path": hit}
            return self._repo_call(s, go)

        def _blob(self, s, q):
            path = q.get("path", [""])[0]
            if not path:
                return self._json(400, {"error": "path is required"})

            def go(clone, sha):
                html, lines = file_section.blob_table(resolve.read(clone, sha, path))
                return {"html": html, "lines": lines, "lang": file_section.lang(path)}
            return self._repo_call(s, go)

        def _get_file(self, s, q):
            meta = manifest.manifest_entry(cfg, s)
            if not meta:
                return self._json(404, {"error": "This PR is not in the current build. Run review.py again."})
            path, idx = q.get("path", [""])[0], q.get("i", [""])[0]
            if not path or not idx.isdigit():
                return self._json(400, {"error": "path and i are required"})
            try:
                return self._json(200, fullfile.render(cfg, meta, path, int(idx)))
            except fullfile.NoClone as e:
                return self._json(409, {"error": str(e)})
            except subprocess.SubprocessError as e:
                return self._json(502, {"error": (getattr(e, "stderr", "") or str(e)).strip()[:300]})

        def _get_page(self, path):
            f = (pages / (path.lstrip("/") or "index.html")).resolve()
            if pages not in f.parents or not f.is_file():
                return self._send(404, "not found")
            return self._send(200, f.read_bytes(), TYPES.get(f.suffix, "application/octet-stream"))

        def do_GET(self):
            self._guard(self._get)

        def _get(self):
            url = urlparse(self.path)
            q = parse_qs(url.query)
            if url.path == "/api/ping":
                touch()
                return self._send(200, "ok")
            if "t" in q:
                return self._token_login(q)
            if not self._ok_request():
                return
            if url.path.startswith("/api/state/"):
                return self._get_state(url.path)
            if url.path == "/api/refresh":
                return self._json(200, refresh)
            if url.path.startswith("/api/resolve/"):
                return self._resolve(url.path.rsplit("/", 1)[1], q)
            if url.path.startswith("/api/blob/"):
                return self._blob(url.path.rsplit("/", 1)[1], q)
            if url.path.startswith("/api/file/"):
                return self._get_file(url.path.rsplit("/", 1)[1], q)
            return self._get_page(url.path)

        def do_PUT(self):
            self._guard(self._put)

        def _put(self):
            if not self._ok_request(write=True):
                return
            url = urlparse(self.path)
            if not url.path.startswith("/api/state/"):
                return self._send(404, "not found")
            s = url.path.rsplit("/", 1)[1]
            try:
                mine = self._body()
                with state.locked(cfg, s):
                    before = state.load_state(cfg, s)
                    merged = state.merge_state(copy.deepcopy(before), mine)
                    state.save_state(cfg, s, merged)
                    inbox.append(cfg, inbox.entries_for(s, before, merged))
            except ValueError as e:
                return self._send(400, str(e))
            return self._json(200, merged)

        def do_POST(self):
            self._guard(self._post)

        def _post(self):
            if not self._ok_request(write=True):
                return
            url = urlparse(self.path)
            if url.path == "/api/refresh":
                start_refresh(cfg, refresh)
                return self._json(202, refresh)
            if url.path.startswith("/api/approve/"):
                return self._approve(url.path.rsplit("/", 1)[1])
            if url.path.startswith("/api/sync/"):
                return self._sync(url.path.rsplit("/", 1)[1])
            if not url.path.startswith("/api/post/"):
                return self._send(404, "not found")
            s = url.path.rsplit("/", 1)[1]
            meta = manifest.manifest_entry(cfg, s)
            if not meta:
                return self._json(404, {"error": "This PR is not in the current build. Run review.py again."})
            req = self._body()
            if not isinstance(req, dict):
                return self._json(400, {"error": "body must be a JSON object"})
            try:
                posted = posting.post_thread(cfg, meta, req.get("threadId"), req.get("messageId"))
                saved = state.load_state(cfg, s)
            except posting.PostConflict as e:
                return self._json(409, {"error": str(e)})
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            except Exception as e:  # gh failures: show the reason in the thread
                return self._json(502, {"error": (getattr(e, "stderr", "") or str(e)).strip()[:500]})
            return self._json(200, {"posted": posted, "state": saved})

        def _sync(self, s):
            meta = manifest.manifest_entry(cfg, s)
            if not meta:
                return self._json(404, {"error": "This PR is not in the current build. Run review.py again."})
            with sync_lock:
                if time.time() - synced_at.get(s, 0) < SYNC_EVERY:
                    return self._json(200, {"ok": True, "added": 0, "throttled": True})
                synced_at[s] = time.time()
            try:
                added = gh_sync.sync(cfg, meta)
            except Exception as e:
                with sync_lock:
                    synced_at.pop(s, None)
                return self._json(502, {"error": (getattr(e, "stderr", "") or str(e)).strip()[:500]})
            return self._json(200, {"ok": True, "added": added})

        def _approve(self, s):
            meta = manifest.manifest_entry(cfg, s)
            if not meta:
                return self._json(404, {"error": "This PR is not in the current build. Run review.py again."})
            req = self._body()
            if not isinstance(req, dict):
                return self._json(400, {"error": "body must be a JSON object"})
            try:
                record = approval.approve(cfg, meta, req.get("sha"), req.get("body"))
                saved = state.load_state(cfg, s)
            except approval.ApprovalConflict as e:
                return self._json(409, {"error": str(e)})
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            except Exception as e:  # gh failures: show the reason
                return self._json(502, {"error": (getattr(e, "stderr", "") or str(e)).strip()[:500]})
            return self._json(200, {"approval": record, "state": saved})

    return Handler


def prune_state(cfg):
    cutoff = time.time() - cfg["keep_days"] * 86400
    for f in dirs(cfg)["state"].glob("*.json"):
        if f.stat().st_mtime < cutoff:
            f.unlink()


def housekeeping(httpd, cfg, last):
    """Prune old state every few hours; stop after `idle_hours` without requests (0 = never stop)."""
    pruned = time.time()
    while True:
        time.sleep(30)
        if time.time() - pruned > 6 * 3600:
            prune_state(cfg)
            pruned = time.time()
        if cfg["idle_hours"] > 0 and time.time() - last[0] > cfg["idle_hours"] * 3600:
            httpd.shutdown()
            return


def session_token(root):
    """Reuse the saved token so links and bookmarks survive restarts."""
    f = root / "token"
    try:
        token = f.read_text().strip()
        if len(token) >= 32:
            return token
    except OSError:
        pass
    token = secrets.token_urlsafe(24)
    f.write_text(token)
    os.chmod(f, 0o600)
    return token


def remove_info(info):
    try:
        if json.loads(info.read_text()).get("pid") == os.getpid():
            info.unlink()
    except (OSError, ValueError):
        pass


def serve(cfg):
    d = dirs(cfg)
    prune_state(cfg)
    token = session_token(d["root"])
    last = [time.time()]
    handler = make_handler(cfg, token, lambda: last.__setitem__(0, time.time()))
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", cfg["port"]), handler)
    except OSError:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    info = d["root"] / "server.json"
    info.write_text(json.dumps({"pid": os.getpid(), "port": httpd.server_address[1], "token": token, "started": time.time()}))
    os.chmod(info, 0o600)
    threading.Thread(target=housekeeping, args=(httpd, cfg, last), daemon=True).start()
    try:
        httpd.serve_forever()
    finally:
        remove_info(info)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config")
    serve(load_config(ap.parse_args().config))
