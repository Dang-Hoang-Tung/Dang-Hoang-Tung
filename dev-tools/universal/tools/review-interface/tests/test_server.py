"""The local helper over HTTP."""
import copy
import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401
from app import config
from app.server import http as helper
from app.services import github, state

from helpers import *  # noqa: F401,F403


TOKEN = "tok-123"


class ServerBase(TmpCase):
    def setUp(self):
        super().setUp()
        p = mock.patch.dict(os.environ, {"REVIEW_POST_DRY_RUN": "1"})
        p.start()
        self.addCleanup(p.stop)
        self.touched = []
        handler = helper.make_handler(self.cfg, TOKEN, lambda: self.touched.append(1))
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]
        t = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        t.start()
        self.addCleanup(self._stop, t)
        self.pages = config.dirs(self.cfg)["pages"]
        (self.pages / "index.html").write_text("<h1>queue</h1>")
        (self.pages / "acme-widgets-7.html").write_text("<h1>pr</h1>")
        (Path(self.tmp) / "secret.txt").write_text("secret")
        self.cookie = {"Cookie": f"rt={TOKEN}"}

    def _stop(self, t):
        self.httpd.shutdown()
        self.httpd.server_close()
        t.join(5)

    def req(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            h = dict(headers or {})
            if method != "GET" and "Origin" not in h:
                h["Origin"] = f"http://127.0.0.1:{self.port}"
            h = {k: v for k, v in h.items() if v is not None}
            data = None
            if body is not None:
                data = json.dumps(body).encode()
                h["Content-Type"] = "application/json"
            c.request(method, path, body=data, headers=h)
            r = c.getresponse()
            return r.status, dict(r.getheaders()), r.read()
        finally:
            c.close()

    def write_manifest(self, *entries):
        (config.dirs(self.cfg)["root"] / "manifest.json").write_text(json.dumps({"prs": list(entries)}))


class ServerTests(ServerBase):
    # --- auth and static
    def test_ping(self):
        status, _, body = self.req("GET", "/api/ping")
        self.assertEqual((status, body), (200, b"ok"))

    def test_page_without_cookie_403(self):
        self.assertEqual(self.req("GET", "/index.html")[0], 403)
        self.assertEqual(self.req("GET", "/")[0], 403)

    def test_wrong_token_403(self):
        self.assertEqual(self.req("GET", "/?t=wrong")[0], 403)

    def test_good_token_redirects_with_cookie(self):
        status, headers, _ = self.req("GET", f"/?t={TOKEN}")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], "/index.html")
        self.assertIn(f"rt={TOKEN}", headers["Set-Cookie"])
        self.assertIn("HttpOnly", headers["Set-Cookie"])
        self.assertIn("SameSite=Strict", headers["Set-Cookie"])

    def test_token_next_param_sanitised(self):
        _, h, _ = self.req("GET", f"/?t={TOKEN}&next=acme-widgets-7.html")
        self.assertEqual(h["Location"], "/acme-widgets-7.html")
        _, h, _ = self.req("GET", f"/?t={TOKEN}&next=../secret.txt")
        self.assertEqual(h["Location"], "/index.html")
        _, h, _ = self.req("GET", f"/?t={TOKEN}&next=a/b.html")
        self.assertEqual(h["Location"], "/index.html")

    def test_pages_with_cookie(self):
        status, h, body = self.req("GET", "/", headers=self.cookie)
        self.assertEqual((status, body), (200, b"<h1>queue</h1>"))
        self.assertTrue(h["Content-Type"].startswith("text/html"))
        self.assertEqual(self.req("GET", "/acme-widgets-7.html", headers=self.cookie)[2], b"<h1>pr</h1>")
        self.assertEqual(self.req("GET", "/missing.html", headers=self.cookie)[0], 404)

    def test_wrong_cookie_403(self):
        self.assertEqual(self.req("GET", "/index.html", headers={"Cookie": "rt=nope"})[0], 403)

    def test_path_traversal_404(self):
        for p in ("/../secret.txt", "/..%2fsecret.txt", "/%2e%2e/secret.txt", "/../../etc/passwd"):
            with self.subTest(p=p):
                status, _, body = self.req("GET", p, headers=self.cookie)
                self.assertIn(status, (403, 404))
                self.assertNotIn(b"secret", body)
        self.assertEqual(self.req("GET", "/../secret.txt", headers=self.cookie)[0], 404)

    def test_pages_dir_itself_404(self):
        sub = self.pages / "sub"
        sub.mkdir()
        self.assertEqual(self.req("GET", "/sub", headers=self.cookie)[0], 404)

    def test_bad_host_403(self):
        self.assertEqual(self.req("GET", "/index.html", headers={**self.cookie, "Host": "evil.example"})[0], 403)
        self.assertEqual(self.req("GET", "/index.html", headers={**self.cookie, "Host": f"localhost:{self.port}"})[0], 200)

    def test_bad_host_on_put_403(self):
        status, _, _ = self.req("PUT", "/api/state/acme-widgets-7", {"threads": []}, {**self.cookie, "Host": "evil.example"})
        self.assertEqual(status, 403)

    # --- state
    def test_state_get_empty(self):
        status, _, body = self.req("GET", "/api/state/acme-widgets-7", headers=self.cookie)
        self.assertEqual((status, json.loads(body)), (200, {}))

    def test_state_requires_cookie(self):
        self.assertEqual(self.req("GET", "/api/state/acme-widgets-7")[0], 403)
        self.assertEqual(self.req("PUT", "/api/state/acme-widgets-7", {})[0], 403)

    def test_state_put_get_round_trip_with_merge(self):
        a = {"threads": [thread("t1", [msg("m1", "me", "hi", "2026-01-01T00:00:01Z")])], "read": {"f1": {"at": "1"}}}
        status, _, body = self.req("PUT", "/api/state/acme-widgets-7", a, self.cookie)
        self.assertEqual(status, 200)
        b = {"threads": [thread("t1", [msg("m2", "ai", "yo", "2026-01-01T00:00:02Z")]), thread("t2", [msg("m3", "me", "x", "3")])],
             "read": {"f2": {"at": "2"}}}
        status, _, body = self.req("PUT", "/api/state/acme-widgets-7", b, self.cookie)
        self.assertEqual(status, 200)
        merged = json.loads(body)
        t1 = next(t for t in merged["threads"] if t["id"] == "t1")
        self.assertEqual([m["id"] for m in t1["messages"]], ["m1", "m2"])
        self.assertEqual({t["id"] for t in merged["threads"]}, {"t1", "t2"})
        self.assertEqual(set(merged["read"]), {"f1", "f2"})
        _, _, body = self.req("GET", "/api/state/acme-widgets-7", headers=self.cookie)
        self.assertEqual(json.loads(body), merged)
        self.assertEqual(state.load_state(self.cfg, "acme-widgets-7"), merged)

    def test_put_evil_origin_403(self):
        status, _, _ = self.req("PUT", "/api/state/acme-widgets-7", {"threads": []}, {**self.cookie, "Origin": "https://evil.example"})
        self.assertEqual(status, 403)
        self.assertEqual(state.load_state(self.cfg, "acme-widgets-7"), {})

    def test_put_local_origin_ok(self):
        status, _, _ = self.req("PUT", "/api/state/acme-widgets-7", {"threads": []}, {**self.cookie, "Origin": f"http://127.0.0.1:{self.port}"})
        self.assertEqual(status, 200)

    def test_put_bad_slug_400(self):
        status, _, _ = self.req("PUT", "/api/state/not-a-slug", {"threads": []}, self.cookie)
        self.assertEqual(status, 400)

    def test_put_bad_json_400(self):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("PUT", "/api/state/acme-widgets-7", body=b"{nope",
                  headers={**self.cookie, "Origin": f"http://127.0.0.1:{self.port}", "Content-Type": "application/json"})
        self.assertEqual(c.getresponse().status, 400)
        c.close()

    def test_put_unknown_path_404(self):
        self.assertEqual(self.req("PUT", "/api/other", {}, self.cookie)[0], 404)

    def test_get_bad_slug_400(self):
        status, _, _ = self.req("GET", "/api/state/not-a-slug", headers=self.cookie)
        self.assertEqual(status, 400)

    # --- post
    def test_post_dry_run(self):
        self.write_manifest({"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD})
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t1", [msg("m1", "me", "post: ship it", "1")])]})
        status, _, body = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"}, self.cookie)
        self.assertEqual(status, 200)
        out = json.loads(body)
        self.assertIn("example.invalid", out["posted"]["url"])
        self.assertEqual(out["posted"]["message_id"], "m1")
        t = out["state"]["threads"][0]
        self.assertEqual(t["posted"]["body"], "ship it")
        self.assertEqual(state.load_state(self.cfg, "acme-widgets-7")["threads"][0]["posted"]["message_id"], "m1")
        status, _, body2 = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1", "messageId": "m1"}, self.cookie)
        self.assertEqual(json.loads(body2)["posted"], out["posted"])

    def test_post_unknown_slug_404(self):
        self.write_manifest({"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD})
        status, _, body = self.req("POST", "/api/post/acme-widgets-99", {"threadId": "t1"}, self.cookie)
        self.assertEqual(status, 404)
        self.assertIn("error", json.loads(body))

    def test_post_no_manifest_404(self):
        self.assertEqual(self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"}, self.cookie)[0], 404)

    def test_post_unknown_thread_400(self):
        self.write_manifest({"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD})
        status, _, body = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "zzz"}, self.cookie)
        self.assertEqual(status, 400)
        self.assertIn("thread not found", json.loads(body)["error"])

    def test_post_evil_origin_403(self):
        self.write_manifest({"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD})
        status, _, _ = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"}, {**self.cookie, "Origin": "https://evil.example"})
        self.assertEqual(status, 403)

    def test_post_requires_cookie(self):
        self.assertEqual(self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"})[0], 403)

    def test_post_gh_failure_502(self):
        os.environ.pop("REVIEW_POST_DRY_RUN", None)
        self.write_manifest({"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD})
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")])]})
        with mock.patch.object(github, "run", side_effect=RuntimeError("gh exploded")):
            status, _, body = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"}, self.cookie)
        self.assertEqual(status, 502)
        self.assertIn("gh exploded", json.loads(body)["error"])
        self.assertNotIn("posted", state.load_state(self.cfg, "acme-widgets-7")["threads"][0])


class ApproveRouteTests(ServerBase):
    SLUG = "acme-widgets-7"

    def approve(self, body, slug=None, **kw):
        status, _, out = self.req("POST", f"/api/approve/{slug or self.SLUG}", body, kw.get("headers", self.cookie))
        return status, json.loads(out) if out.startswith(b"{") else out

    def test_codes(self):
        self.write_manifest({"slug": self.SLUG, "repo": REPO, "pr": 7, "head_sha": HEAD})
        self.assertEqual(self.approve({"sha": HEAD}, "acme-widgets-99")[0], 404)
        self.assertEqual(self.approve({"body": "x"})[0], 400)
        self.assertEqual(self.approve([1])[0], 400)
        self.assertEqual(self.approve({"sha": "deadbeef00"})[0], 409)
        status, out = self.approve({"sha": HEAD, "body": "lgtm"})
        self.assertEqual(status, 200)
        self.assertTrue(out["approval"]["dry_run"])
        self.assertEqual(out["state"]["approval"]["body"], "lgtm")
        status, out = self.approve({"sha": HEAD})
        self.assertEqual((status, out["error"]), (409, "Already approved at a1b2c3d."))

    def test_auth_rules(self):
        self.write_manifest({"slug": self.SLUG, "repo": REPO, "pr": 7, "head_sha": HEAD})
        self.assertEqual(self.approve({"sha": HEAD}, headers={})[0], 403)
        self.assertEqual(self.approve({"sha": HEAD}, headers={**self.cookie, "Origin": "https://evil.example"})[0], 403)

    def test_gh_failure_502(self):
        os.environ.pop("REVIEW_POST_DRY_RUN", None)
        self.write_manifest({"slug": self.SLUG, "repo": REPO, "pr": 7, "head_sha": HEAD})
        with mock.patch.object(github, "run", side_effect=RuntimeError("gh exploded")):
            status, out = self.approve({"sha": HEAD})
        self.assertEqual(status, 502)
        self.assertIn("gh exploded", out["error"])
        self.assertNotIn("approval", state.load_state(self.cfg, self.SLUG))


class ServerHardeningTests(ServerBase):
    def put(self, headers=None, body=b"{}", path="/api/state/acme-widgets-7", method="PUT"):
        h = {**self.cookie, **(headers or {})}
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            c.request(method, path, body=body, headers=h)
            r = c.getresponse()
            return r.status, r.read()
        finally:
            c.close()

    def good(self, **kw):
        return {"Origin": f"http://127.0.0.1:{self.port}", "Content-Type": "application/json", **kw}

    def test_origin_must_equal_http_host(self):
        for method, path in (("PUT", "/api/state/acme-widgets-7"), ("POST", "/api/post/acme-widgets-7")):
            for origin in (None, "http://127.0.0.1", f"https://127.0.0.1:{self.port}", f"http://localhost:{self.port}", "null"):
                with self.subTest(method=method, origin=origin):
                    h = self.good()
                    h.pop("Origin")
                    if origin:
                        h["Origin"] = origin
                    self.assertEqual(self.put(h, method=method, path=path)[0], 403)
        self.assertEqual(self.put(self.good())[0], 200)

    def test_content_type_must_be_json(self):
        for ct in ("text/plain", "application/x-www-form-urlencoded"):
            self.assertEqual(self.put(self.good(**{"Content-Type": ct}))[0], 415)
        self.assertEqual(self.put({k: v for k, v in self.good().items() if k != "Content-Type"})[0], 415)
        self.assertEqual(self.put(self.good(**{"Content-Type": "application/json; charset=utf-8"}))[0], 200)

    def test_oversize_body_413(self):
        status, _ = self.put(self.good(**{"Content-Length": str(helper.MAX_BODY + 1)}))
        self.assertEqual(status, 413)

    def test_non_ascii_cookie_403(self):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("GET", "/index.html", headers={"Cookie": "rt=t\u00f6k\u00e9n"})
        self.assertEqual(c.getresponse().status, 403)
        c.close()
        self.assertEqual(self.req("GET", "/?t=t%C3%B6k")[0], 403)

    def test_unexpected_error_is_json_500(self):
        with mock.patch.object(state, "load_state", side_effect=RuntimeError("kaboom")), mock.patch("traceback.print_exc"):
            status, _, body = self.req("GET", "/api/state/acme-widgets-7", headers=self.cookie)
        self.assertEqual(status, 500)
        self.assertIn("error", json.loads(body))
        self.assertEqual(self.req("GET", "/api/ping")[0], 200)

    def test_put_bad_shape_400(self):
        self.assertEqual(self.put(self.good(), body=b'{"threads": {"a": 1}}')[0], 400)
        self.assertEqual(self.put(self.good(), body=b"[1]")[0], 400)

    def test_post_conflicts_409(self):
        self.write_manifest({"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD})
        marker = {"message_id": "m1", "at": config.now()}
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")], posting=marker)]})
        status, _, body = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"}, self.cookie)
        self.assertEqual((status, json.loads(body)["error"]), (409, "already posting"))
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")], commit="deadbeef0")]})
        status, _, body = self.req("POST", "/api/post/acme-widgets-7", {"threadId": "t1"}, self.cookie)
        self.assertEqual(status, 409)
        self.assertIn("older commit (deadbee)", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
