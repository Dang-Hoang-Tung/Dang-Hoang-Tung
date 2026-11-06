import os
import unittest
from unittest import mock

from helpers import *  # noqa: F401,F403
from app.services import gh_sync, github, inbox, posting, state
from test_server import ServerBase

S = "acme-widgets-7"
META = {"slug": S, "repo": REPO, "pr": 7, "head_sha": HEAD}


def gc(i, body="x", reply=None, user="bob", line=5, at=None, **kw):
    return {"id": i, "in_reply_to_id": reply, "body": body, "user": {"login": user}, "created_at": at or f"2026-01-01T00:00:{i:02d}Z",
            "html_url": f"https://gh/c{i}", "path": "a.py", "line": line, "original_line": 4, "side": "RIGHT", "commit_id": "abc1234", **kw}


class SyncTests(TmpCase):
    def run_sync(self, comments, me="rev"):
        with mock.patch.object(github, "fetch_review_comments", return_value=comments), mock.patch.object(github, "viewer_login", return_value=me):
            return gh_sync.sync(self.cfg, META)

    def threads(self):
        return state.load_state(self.cfg, S)["threads"]

    def test_groups_replies_into_one_thread(self):
        self.assertEqual(self.run_sync([gc(1), gc(3, reply=1), gc(2, line=9)]), 3)
        by = {t["id"]: t for t in self.threads()}
        self.assertEqual([m["id"] for m in by["gh-1"]["messages"]], ["gh-1", "gh-3"])
        t = by["gh-1"]
        self.assertEqual((t["synced"], t["gh_root"], t["path"], t["line"], t["side"], t["commit"]), (True, 1, "a.py", 5, "RIGHT", "abc1234"))
        self.assertEqual(t["messages"][0], {"id": "gh-1", "who": "github", "author": "bob", "text": "x", "at": "2026-01-01T00:00:01Z", "gh_id": 1, "url": "https://gh/c1"})
        self.assertEqual(by["gh-2"]["line"], 9)

    def test_rerun_adds_nothing(self):
        cs = [gc(1), gc(2, reply=1)]
        self.run_sync(cs)
        self.assertEqual(self.run_sync(cs), 0)
        self.assertEqual(len(self.threads()[0]["messages"]), 2)

    def test_merges_into_thread_by_posted_message_without_dupes(self):
        state.save_state(self.cfg, S, {"threads": [thread("t1", [msg("m1", "me", "mine", "2026-01-01T00:00:00Z")], path="a.py", line=5,
                                                          posted_messages={"m1": {"id": 1, "url": "u", "at": "z"}})]})
        self.assertEqual(self.run_sync([gc(1, user="rev"), gc(2, reply=1)]), 1)
        (t,) = self.threads()
        self.assertEqual([m["id"] for m in t["messages"]], ["m1", "gh-2"])
        self.assertEqual((t["gh_root"], t["synced"]), (1, True))

    def test_existing_gh_id_not_duplicated(self):
        state.save_state(self.cfg, S, {"threads": [thread("t1", [{**msg("x", "me", "mine", "2026-01-01T00:00:00Z"), "gh_id": 2}], gh_root=1, synced=True)]})
        self.assertEqual(self.run_sync([gc(1), gc(2, reply=1)]), 1)
        self.assertEqual(len(self.threads()), 1)

    def test_viewer_comment_is_me(self):
        self.run_sync([gc(1, user="rev")])
        m = self.threads()[0]["messages"][0]
        self.assertEqual((m["who"], m["gh_id"], m["url"]), ("me", 1, "https://gh/c1"))

    def test_outdated_uses_original_line(self):
        self.run_sync([gc(1, line=None)])
        t = self.threads()[0]
        self.assertEqual((t["line"], t["outdated"]), (4, True))

    def test_existing_user_messages_untouched(self):
        mine = thread("t1", [msg("m1", "me", "keep", "2026-01-01T00:00:00Z")], gh_root=1, synced=True, resolved=True)
        state.save_state(self.cfg, S, {"threads": [mine]})
        self.run_sync([gc(1, body="changed")])
        self.assertEqual(self.threads()[0]["messages"][0]["text"], "keep")


class PostingTests(TmpCase):
    def post(self, t):
        state.save_state(self.cfg, S, {"threads": [t]})
        with mock.patch.object(github, "post_comment", return_value={"url": "u", "id": 11}) as pc, \
                mock.patch.object(github, "post_reply", return_value={"url": "r", "id": 12}) as pr:
            out = posting.post_thread(self.cfg, META, t["id"])
        return out, pc, pr

    def test_first_post_is_new_comment_and_sets_root(self):
        t = thread("t1", [{**msg("m1", "me", "hi", "2026-01-01T00:00:00Z"), "post": True}], path="a.py", line=3, synced=True)
        _, pc, pr = self.post(t)
        pc.assert_called_once()
        pr.assert_not_called()
        saved = self.threads_saved()
        self.assertEqual((saved["synced"], saved["gh_root"]), (True, 11))

    def test_later_post_is_reply(self):
        t = thread("t1", [msg("m0", "github", "q", "2026-01-01T00:00:00Z"), {**msg("m1", "me", "hi", "2026-01-01T00:00:01Z"), "post": True}],
                   path="a.py", line=3, synced=True, gh_root=5, commit="old1234")
        _, pc, pr = self.post(t)
        pc.assert_not_called()
        pr.assert_called_once_with(REPO, 7, 5, "hi")

    def test_internal_thread_with_messages_refused(self):
        t = thread("t1", [msg("m0", "me", "a", "2026-01-01T00:00:00Z"), msg("m1", "ai", "b", "2026-01-01T00:00:01Z"),
                          {**msg("m2", "me", "c", "2026-01-01T00:00:02Z"), "post": True}], path="a.py", line=3)
        with self.assertRaisesRegex(ValueError, "internal thread"):
            self.post(t)

    def threads_saved(self):
        return state.load_state(self.cfg, S)["threads"][0]


class AiSideTests(unittest.TestCase):
    def test_waiting_ignores_synced(self):
        st = {"threads": [thread("a", [msg("m", "me", "x", "1")], synced=True), thread("b", [msg("m", "me", "x", "1")])]}
        self.assertEqual([t["id"] for t in state.waiting_threads(st)], ["b"])

    def test_github_is_not_ai(self):
        self.assertFalse(state.is_ai({"who": "github"}))

    def test_inbox_ignores_synced_and_github(self):
        after = {"threads": [thread("a", [msg("m", "me", "x", "1")], synced=True),
                             thread("b", [msg("m", "github", "x", "1"), msg("n", "me", "y", "2")])]}
        self.assertEqual([(t["id"], m["id"]) for t, m in inbox.new_user_messages({}, after)], [("b", "n")])


class SyncEndpointTests(ServerBase):
    def setUp(self):
        super().setUp()
        from app.services import manifest
        manifest.write_manifest(self.cfg, [{"slug": S, "repo": REPO, "pr": 7}])

    def test_sync_throttled_and_errors(self):
        with mock.patch.object(gh_sync, "sync", return_value=2) as sy:
            self.assertEqual(self.req("POST", f"/api/sync/{S}", {}, self.cookie)[0], 200)
            _, _, body = self.req("POST", f"/api/sync/{S}", {}, self.cookie)
            self.assertTrue(json.loads(body)["throttled"])
            self.assertEqual(sy.call_count, 1)

    def test_sync_error_502(self):
        with mock.patch.object(gh_sync, "sync", side_effect=RuntimeError("boom")):
            status, _, body = self.req("POST", f"/api/sync/{S}", {}, self.cookie)
        self.assertEqual((status, json.loads(body)["error"]), (502, "boom"))


if __name__ == "__main__":
    unittest.main()
