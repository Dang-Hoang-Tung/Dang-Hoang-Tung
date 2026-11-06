"""Post flag, approval and github.submit_approval."""
import json
import os
import unittest
from unittest import mock

import helpers  # noqa: F401
from app.services import approval, github, posting, state

from helpers import *  # noqa: F401,F403


class PostFlagTests(unittest.TestCase):
    def test_flag_and_legacy_prefix(self):
        t = thread("t", [msg("m1", "me", "plain", "1"), msg("m2", "me", "ship it", "2"), msg("m3", "me", "post: old", "3"), msg("m4", "ai", "post: no", "4")])
        t["messages"][1]["post"] = True
        self.assertEqual(posting.post_body(t)[1], "old")
        self.assertEqual(posting.post_body(t, "m2")[1], "ship it")
        self.assertEqual(posting.post_body(t, "m3")[1], "old")
        with self.assertRaises(ValueError):
            posting.post_body(t, "m1")
        with self.assertRaises(ValueError):
            posting.post_body(t, "m4")

    def test_flag_only_latest(self):
        t = thread("t", [{**msg("m1", "me", "first", "1"), "post": True}, {**msg("m2", "me", "second", "2"), "post": True}])
        self.assertEqual(posting.post_body(t)[0]["id"], "m2")

    def test_state_accepts_bool_only(self):
        state.validate_state({"threads": [thread("t", [{**msg("m", "me", "x", "1"), "post": True}])]})
        with self.assertRaises(ValueError):
            state.validate_state({"threads": [thread("t", [{**msg("m", "me", "x", "1"), "post": "yes"}])]})


class ApproveTests(TmpCase):
    META = {"slug": "acme-widgets-7", "repo": REPO, "pr": 7, "head_sha": HEAD}

    def setUp(self):
        super().setUp()
        p = mock.patch.dict(os.environ, {"REVIEW_POST_DRY_RUN": "1"})
        p.start()
        self.addCleanup(p.stop)

    def test_dry_run_saves_record(self):
        rec = approval.approve(self.cfg, self.META, HEAD[:7], " ok ")
        self.assertTrue(rec["dry_run"])
        saved = state.load_state(self.cfg, "acme-widgets-7")["approval"]
        self.assertEqual((saved["commit"], saved["body"], saved["url"].startswith("https://example.invalid")), (HEAD, "ok", True))

    def test_stale_sha_409(self):
        with self.assertRaisesRegex(approval.ApprovalConflict, "new commits"):
            approval.approve(self.cfg, self.META, "deadbeef00")
        self.assertNotIn("approval", state.load_state(self.cfg, "acme-widgets-7"))

    def test_repeat_409(self):
        approval.approve(self.cfg, self.META, HEAD)
        with mock.patch.object(github, "submit_approval", side_effect=AssertionError("twice")):
            with self.assertRaisesRegex(approval.ApprovalConflict, "Already approved at a1b2c3d."):
                approval.approve(self.cfg, self.META, HEAD)

    def test_new_commit_can_be_approved_again(self):
        state.save_state(self.cfg, "acme-widgets-7", {"approval": {"commit": "f" * 40}})
        approval.approve(self.cfg, self.META, HEAD)

    def test_merge_keeps_server_approval(self):
        disk = {"approval": {"commit": HEAD}}
        self.assertEqual(state.merge_state(disk, {"approval": None})["approval"], {"commit": HEAD})


class SubmitApprovalTests(unittest.TestCase):
    def test_args(self):
        seen = []
        def fake(*a, **k):
            seen.append(a)
            return json.dumps({"html_url": "https://github.com/x", "id": 9})
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(github, "run", side_effect=fake):
            os.environ.pop("REVIEW_POST_DRY_RUN", None)
            self.assertEqual(github.submit_approval("o/r", 5, "abc1234", "good"), {"url": "https://github.com/x", "id": 9})
            github.submit_approval("o/r", 5, "abc1234")
        self.assertEqual(seen[0], ("gh", "api", "-X", "POST", "repos/o/r/pulls/5/reviews", "-f", "event=APPROVE", "-f", "commit_id=abc1234", "-f", "body=good"))
        self.assertFalse(any(x.startswith("body=") for x in seen[1]))


if __name__ == "__main__":
    unittest.main()
