"""State files, merge, waiting threads and posting."""
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
from app.services import github, posting, state

from helpers import *  # noqa: F401,F403


class CoreTests(TmpCase):
    def test_slug(self):
        self.assertEqual(config.slug("acme/widgets", 7), "acme-widgets-7")
        self.assertEqual(config.slug("acme/widgets", "12"), "acme-widgets-12")
        with self.assertRaises(ValueError):
            config.slug("nonsense", 1)

    def test_load_config_defaults(self):
        self.assertEqual(self.cfg["port"], 0)
        self.assertEqual(self.cfg["sources"], [{"repo": REPO}])
        self.assertIsInstance(self.cfg["data_dir"], Path)

    def test_state_path_ok(self):
        p = state.state_path(self.cfg, "acme-widgets-7")
        self.assertEqual(p.name, "acme-widgets-7.json")
        self.assertEqual(p.parent.name, "state")

    def test_state_path_rejects_bad_slugs(self):
        for bad in ("", "../evil-1", "a/b-1", "acme-widgets", "acme-widgets-7/x", "a b-1", "x-1\n", "acme-widgets-7.json/.."):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                state.state_path(self.cfg, bad)

    def test_load_state_bad_slug_raises(self):
        with self.assertRaises(ValueError):
            state.load_state(self.cfg, "../evil-1")

    def test_load_state_corrupt_file_is_empty(self):
        path = state.state_path(self.cfg, "acme-widgets-7")
        path.write_text("{nope")
        with mock.patch("sys.stderr"):
            self.assertEqual(state.load_state(self.cfg, "acme-widgets-7"), {})
        self.assertFalse(path.exists())
        kept = list(path.parent.glob("acme-widgets-7.corrupt-*.json"))
        self.assertEqual([p.read_text() for p in kept], ["{nope"])

    def test_load_state_missing_is_empty(self):
        self.assertEqual(state.load_state(self.cfg, "acme-widgets-7"), {})

    def test_save_and_load_state(self):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [], "x": 1})
        self.assertEqual(state.load_state(self.cfg, "acme-widgets-7"), {"threads": [], "x": 1})

    def test_merge_messages_union_and_order(self):
        disk = {"threads": [thread("t1", [msg("m2", "ai", "b", "2026-01-01T00:00:02Z"), msg("m1", "me", "a", "2026-01-01T00:00:01Z")])]}
        mine = {"threads": [thread("t1", [msg("m1", "me", "a", "2026-01-01T00:00:01Z"), msg("m3", "me", "c", "2026-01-01T00:00:03Z"),
                                          msg("m0", "me", "z", "2026-01-01T00:00:00Z")])]}
        out = state.merge_state(disk, mine)
        ids = [m["id"] for m in out["threads"][0]["messages"]]
        self.assertEqual(ids, ["m0", "m1", "m2", "m3"])

    def test_merge_new_thread_added(self):
        out = state.merge_state({"threads": [thread("t1", [msg("m1", "me", "a", "1")])]}, {"threads": [thread("t2", [msg("m2", "me", "b", "2")])]})
        self.assertEqual({t["id"] for t in out["threads"]}, {"t1", "t2"})

    def test_merge_resolved_latest_wins(self):
        disk = {"threads": [thread("t1", [msg("m1", "me", "a", "1")], resolved=True, resolvedAt="2026-01-02")]}
        newer = {"threads": [thread("t1", [msg("m1", "me", "a", "1")], resolved=False, resolvedAt="2026-01-03")]}
        older = {"threads": [thread("t1", [msg("m1", "me", "a", "1")], resolved=False, resolvedAt="2026-01-01")]}
        self.assertFalse(state.merge_state(copy.deepcopy(disk), newer)["threads"][0]["resolved"])
        self.assertTrue(state.merge_state(copy.deepcopy(disk), older)["threads"][0]["resolved"])

    def test_merge_read_and_checked_latest_at_wins(self):
        disk = {"read": {"a": {"at": "2"}, "b": {"at": "5"}}, "checked": {"c": {"at": "1", "v": "old"}}}
        mine = {"read": {"a": {"at": "3"}, "b": {"at": "4"}, "n": {"at": "1"}}, "checked": {"c": {"at": "2", "v": "new"}}}
        out = state.merge_state(disk, mine)
        self.assertEqual(out["read"]["a"]["at"], "3")
        self.assertEqual(out["read"]["b"]["at"], "5")
        self.assertIn("n", out["read"])
        self.assertEqual(out["checked"]["c"]["v"], "new")

    def test_merge_posted_kept(self):
        posted = {"message_id": "m1", "url": "u"}
        disk = {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")], posted=posted)]}
        mine = {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")])]}
        self.assertEqual(state.merge_state(disk, mine)["threads"][0]["posted"], posted)
        disk2 = {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")])]}
        mine2 = {"threads": [thread("t1", [msg("m1", "me", "post: x", "1")], posted=posted)]}
        self.assertEqual(state.merge_state(disk2, mine2)["threads"][0]["posted"], posted)

    def test_merge_other_keys_from_mine(self):
        out = state.merge_state({"foo": 1}, {"foo": 2, "bar": 3})
        self.assertEqual((out["foo"], out["bar"]), (2, 3))

    def test_waiting_threads(self):
        human = thread("h", [msg("1", "me", "q?", "1")])
        ai_last = thread("a", [msg("1", "me", "q?", "1"), msg("2", "ai", "a", "2")])
        claude_last = thread("c", [msg("1", "me", "q?", "1"), msg("2", "claude", "a", "2")])
        resolved = thread("r", [msg("1", "me", "q?", "1")], resolved=True)
        posted = thread("p", [msg("1", "me", "post: hi", "1")], posted={"message_id": "1"})
        posted_old = thread("po", [msg("1", "me", "post: hi", "1"), msg("2", "me", "more", "2")], posted={"message_id": "1"})
        empty = thread("e", [])
        got = [t["id"] for t in state.waiting_threads({"threads": [human, ai_last, claude_last, resolved, posted, posted_old, empty]})]
        self.assertEqual(got, ["h", "po"])

    def test_post_body(self):
        t = thread("t", [msg("1", "me", "post: first", "1"), msg("2", "me", "just a note", "2"),
                         msg("3", "ai", "post: ai text", "3"), msg("4", "me", "  Post:   second  ", "4")])
        m, body = posting.post_body(t)
        self.assertEqual((m["id"], body), ("4", "second"))
        m, body = posting.post_body(t, "1")
        self.assertEqual((m["id"], body), ("1", "first"))

    def test_post_body_errors_when_none(self):
        with self.assertRaises(ValueError):
            posting.post_body(thread("t", [msg("1", "me", "hello", "1"), msg("2", "ai", "post: x", "2")]))
        with self.assertRaises(ValueError):
            posting.post_body(thread("t", [msg("1", "me", "post: x", "1")]), "nope")


class PostThreadTests(TmpCase):
    META = {"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD}

    def setUp(self):
        super().setUp()
        p = mock.patch.dict(os.environ, {"REVIEW_POST_DRY_RUN": "1"})
        p.start()
        self.addCleanup(p.stop)

    def test_dry_run_general_and_line_threads(self):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [
            thread("gen", [msg("m1", "me", "post: hello there", "1")]),
            thread("line", [msg("m2", "me", "post: nit", "2")], path="src/a.ts", line=4, side="RIGHT"),
        ]})
        with mock.patch.object(github, "run", side_effect=AssertionError("gh must not run")):
            g = posting.post_thread(self.cfg, self.META, "gen")
            l = posting.post_thread(self.cfg, self.META, "line")
        self.assertIn("conversation", g["url"])
        self.assertIn("line", l["url"])
        self.assertEqual(g["message_id"], "m1")
        self.assertEqual(g["body"], "hello there")
        saved = state.load_state(self.cfg, "acme-widgets-7")
        by = {t["id"]: t for t in saved["threads"]}
        self.assertEqual(by["gen"]["posted"]["message_id"], "m1")
        self.assertEqual(by["line"]["posted"]["message_id"], "m2")

    def test_idempotent(self):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("gen", [msg("m1", "me", "post: hi", "1")])]})
        first = posting.post_thread(self.cfg, self.META, "gen")
        with mock.patch.object(github, "post_comment", side_effect=AssertionError("posted twice")):
            second = posting.post_thread(self.cfg, self.META, "gen")
        self.assertEqual(first, second)

    def test_unknown_thread_and_empty_body(self):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("e", [msg("m1", "me", "post:   ", "1")])]})
        with self.assertRaises(ValueError):
            posting.post_thread(self.cfg, self.META, "nope")
        with self.assertRaises(ValueError):
            posting.post_thread(self.cfg, self.META, "e")


class StateSafetyTests(TmpCase):
    def test_lock_excludes_other_holders(self):
        import fcntl
        lock = state.state_path(self.cfg, "acme-widgets-7").with_suffix(".lock")
        with state.locked(self.cfg, "acme-widgets-7"):
            with open(lock, "a") as other, self.assertRaises(BlockingIOError):
                fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with open(lock, "a") as other:
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_save_leaves_no_tmp_files(self):
        state.save_state(self.cfg, "acme-widgets-7", {"a": 1})
        state.save_state(self.cfg, "acme-widgets-7", {"a": 2})
        self.assertEqual(list(state.state_path(self.cfg, "acme-widgets-7").parent.glob("*.tmp")), [])

    def test_merge_rejects_bad_shapes(self):
        ok_msg = msg("m1", "me", "a", "1")
        bad = [[], {"threads": {}}, {"threads": ["x"]}, {"threads": [{"id": 1, "messages": []}]},
               {"threads": [{"id": "t", "messages": "x"}]}, {"threads": [{"id": "t", "messages": [{"id": "m"}]}]},
               {"threads": [{"id": "t", "messages": [dict(ok_msg, at=5)]}]}, {"read": []}, {"read": {"f": 1}}, {"checked": {"k": "v"}}]
        for mine in bad:
            with self.subTest(mine=mine), self.assertRaises(ValueError):
                state.merge_state({}, mine)

    def test_merge_posted_messages_union(self):
        disk = {"threads": [thread("t", [msg("m1", "me", "post: a", "1")], posted_messages={"m1": {"url": "u1"}})]}
        mine = {"threads": [thread("t", [msg("m1", "me", "post: a", "1")], posted_messages={"m2": {"url": "u2"}})]}
        self.assertEqual(set(state.merge_state(disk, mine)["threads"][0]["posted_messages"]), {"m1", "m2"})

    def test_waiting_ignores_message_in_posted_messages(self):
        t = thread("t", [msg("m1", "me", "post: a", "1")], posted_messages={"m1": {"url": "u"}})
        self.assertEqual(state.waiting_threads({"threads": [t]}), [])


class PostingSafetyTests(TmpCase):
    META = {"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD}

    def save(self, **kw):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t", [msg("m1", "me", "post: hi", "1")], **kw)]})

    def saved(self):
        return state.load_state(self.cfg, "acme-widgets-7")["threads"][0]

    def test_records_posted_messages_and_clears_marker(self):
        self.save()
        seen = []

        def fake(repo, pr, commit, t, body):
            seen.append(self.saved().get("posting"))
            return {"url": "https://x/1", "id": 5}
        with mock.patch.object(github, "post_comment", side_effect=fake):
            out = posting.post_thread(self.cfg, self.META, "t")
        self.assertEqual(seen[0]["message_id"], "m1")
        t = self.saved()
        self.assertNotIn("posting", t)
        self.assertEqual(set(t["posted_messages"]["m1"]), {"url", "id", "at"})
        self.assertEqual((t["posted"]["message_id"], t["posted"]["url"], out["url"]), ("m1", "https://x/1", "https://x/1"))

    def test_recent_marker_refuses_old_marker_allows(self):
        self.save(posting={"message_id": "m1", "at": config.now()})
        with mock.patch.object(github, "post_comment", side_effect=AssertionError("must not post")):
            with self.assertRaisesRegex(posting.PostConflict, "already posting"):
                posting.post_thread(self.cfg, self.META, "t")
        self.save(posting={"message_id": "m1", "at": "2020-01-01T00:00:00.000Z"})
        with mock.patch.object(github, "post_comment", return_value={"url": "u", "id": 1}):
            self.assertEqual(posting.post_thread(self.cfg, self.META, "t")["url"], "u")

    def test_failure_clears_marker(self):
        self.save()
        with mock.patch.object(github, "post_comment", side_effect=RuntimeError("boom")), self.assertRaises(RuntimeError):
            posting.post_thread(self.cfg, self.META, "t")
        self.assertNotIn("posting", self.saved())

    def test_stale_commit_refused(self):
        self.save(commit="deadbeef0000")
        with mock.patch.object(github, "post_comment", side_effect=AssertionError("must not post")):
            with self.assertRaisesRegex(posting.PostConflict, r"older commit \(deadbee\); open the PR again"):
                posting.post_thread(self.cfg, self.META, "t")
        self.save(commit=HEAD[:7])
        with mock.patch.object(github, "post_comment", return_value={"url": "u", "id": 1}):
            posting.post_thread(self.cfg, self.META, "t")


class PostCommentArgsTests(unittest.TestCase):
    def call(self, thread):
        with mock.patch.object(github, "run", return_value='{"html_url": "https://x", "id": 3}') as run, mock.patch.dict(os.environ):
            os.environ.pop("REVIEW_POST_DRY_RUN", None)
            out = github.post_comment(REPO, 7, HEAD, thread, "hi")
        return out, list(run.call_args[0])

    def test_single_line(self):
        out, a = self.call({"path": "a.ts", "line": 4})
        self.assertEqual(out, {"url": "https://x", "id": 3})
        self.assertIn(f"repos/{REPO}/pulls/7/comments", a)
        for pair in (["-F", "line=4"], ["-f", "side=RIGHT"], ["-f", f"commit_id={HEAD}"], ["-f", "path=a.ts"]):
            self.assertIn(pair, [a[i:i + 2] for i in range(len(a) - 1)])
        self.assertFalse(any(x.startswith("start_line") for x in a))

    def test_range_and_left_side(self):
        _, a = self.call({"path": "a.ts", "line": 9, "start_line": 5, "side": "LEFT"})
        for x in ("line=9", "start_line=5", "side=LEFT", "start_side=LEFT"):
            self.assertIn(x, a)

    def test_conversation_comment(self):
        _, a = self.call({"messages": []})
        self.assertIn(f"repos/{REPO}/issues/7/comments", a)
        self.assertFalse(any(x.startswith(("line=", "path=")) for x in a))


if __name__ == "__main__":
    unittest.main()
