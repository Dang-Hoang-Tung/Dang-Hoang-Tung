"""Insights validation and the team-reviewer adapter."""
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
from app.services import insights
from app.services.adapters import team_reviewer

from helpers import *  # noqa: F401,F403


class InsightsTests(TmpCase):
    def test_validate_good(self):
        out = insights.validate(good_insights())
        self.assertEqual(len(out["recommendations"]), 2)
        r = out["recommendations"][0]
        self.assertEqual((r["severity"], r["start_line"], r["end_line"]), ("should", 11, 12))
        r2 = out["recommendations"][1]
        self.assertEqual((r2["path"], r2["end_line"], r2["body"], r2["id"]), (None, None, "", ""))

    def test_validate_rejects(self):
        cases = {
            "schema": good_insights(schema="nope/2"),
            "risk": good_insights(summary={"risk": "Extreme"}),
            "severity": good_insights(recommendations=[{"severity": "bad", "title": "t"}]),
            "title": good_insights(recommendations=[{"severity": "nit"}]),
            "repo": good_insights(repo=""),
            "head_sha": good_insights(head_sha=None),
        }
        for name, obj in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                insights.validate(obj)

    def _write(self, obj, raw=None):
        f = config.dirs(self.cfg)["insights"] / "acme-widgets-7.json"
        f.write_text(raw if raw is not None else json.dumps(obj))

    def test_load_missing(self):
        self.assertEqual(insights.load(self.cfg, REPO, 7, HEAD), (None, "missing"))

    def test_load_current(self):
        self._write(good_insights())
        ins, status = insights.load(self.cfg, REPO, 7, HEAD)
        self.assertEqual(status, "current")
        self.assertEqual(ins["summary"]["risk"], "Medium")

    def test_load_stale(self):
        self._write(good_insights(head_sha="deadbee"))
        ins, status = insights.load(self.cfg, REPO, 7, HEAD)
        self.assertEqual(status, "stale")
        self.assertIsNotNone(ins)

    def test_load_invalid(self):
        self._write(None, raw=json.dumps(good_insights(schema="x")))
        ins, status = insights.load(self.cfg, REPO, 7, HEAD)
        self.assertIsNone(ins)
        self.assertTrue(status.startswith("invalid: "))

    def test_load_non_object_json_is_invalid_not_crash(self):
        for raw in ("[1, 2]", "null", '"x"', "3", "{nope"):
            with self.subTest(raw=raw):
                self._write(None, raw=raw)
                ins, status = insights.load(self.cfg, REPO, 7, HEAD)
                self.assertIsNone(ins)
                self.assertTrue(status.startswith("invalid: "))

    def test_validate_rejects_bad_nested_types(self):
        for obj in (good_insights(summary=[1]), good_insights(recommendations=["x"]), good_insights(head_sha=123)):
            with self.subTest(obj=obj), self.assertRaises(ValueError):
                insights.validate(obj)

    def test_brief_to_insights(self):
        ins = team_reviewer.brief_to_insights(BRIEF, REPO, 7, HEAD[:7])
        insights.validate(ins)
        self.assertEqual(ins["source"], "team-reviewer-brief")
        s = ins["summary"]
        self.assertTrue(s["verdict"].startswith("Approve with nits"))
        self.assertEqual(s["risk"], "Medium")
        self.assertEqual(s["minutes"], 25)
        self.assertEqual(s["questions"], ["Why 5 and not 4?", "Is there a ticket?"])
        recs = ins["recommendations"]
        by_title = {r["title"]: r for r in recs}
        blk = by_title["Counter off by one"]
        self.assertEqual((blk["severity"], blk["path"], blk["start_line"], blk["end_line"]), ("block", "src/app/Widget.tsx", 11, 12))
        self.assertIn("loop bound", blk["body"])
        self.assertEqual(blk["draft_comment"], "This looks off by one, can you check?")
        self.assertEqual(by_title["Magic number"]["severity"], "should")
        self.assertEqual(by_title["Spelling"]["severity"], "nit")
        looks = [r for r in recs if r["severity"] == "look"]
        self.assertEqual(len(looks), 2)
        self.assertEqual((looks[0]["path"], looks[0]["start_line"], looks[0]["end_line"]), ("src/app/Widget.tsx", 10, 14))
        self.assertEqual((looks[1]["start_line"], looks[1]["end_line"]), (2, 2))

    def test_brief_without_sections(self):
        ins = team_reviewer.brief_to_insights("# nothing", REPO, 7, "abc")
        self.assertEqual(ins["recommendations"], [])
        self.assertIsNone(ins["summary"]["minutes"])
        self.assertEqual(ins["summary"]["risk"], "")

    def _sync_cfg(self):
        briefs = Path(self.tmp) / "briefs"
        briefs.mkdir()
        self.cfg["adapters"] = {"team_reviewer_briefs": str(briefs)}
        return briefs

    def test_sync_briefs_writes_insights(self):
        briefs = self._sync_cfg()
        (briefs / f"widgets-7-{HEAD[:7]}.md").write_text(BRIEF)
        team_reviewer.sync_briefs(self.cfg, [make_pr()])
        target = config.dirs(self.cfg)["insights"] / "acme-widgets-7.json"
        self.assertTrue(target.exists())
        data = json.loads(target.read_text())
        self.assertEqual(data["source"], "team-reviewer-brief")
        self.assertEqual(data["head_sha"], HEAD[:7])
        self.assertEqual(insights.load(self.cfg, REPO, 7, HEAD)[1], "current")

    def test_sync_briefs_keeps_direct_insights(self):
        briefs = self._sync_cfg()
        (briefs / f"widgets-7-{HEAD[:7]}.md").write_text(BRIEF)
        target = config.dirs(self.cfg)["insights"] / "acme-widgets-7.json"
        direct = good_insights(source="my-ai")
        target.write_text(json.dumps(direct))
        os.utime(target, (1, 1))
        team_reviewer.sync_briefs(self.cfg, [make_pr()])
        self.assertEqual(json.loads(target.read_text()), direct)

    def test_sync_briefs_refreshes_older_brief_insights(self):
        briefs = self._sync_cfg()
        target = config.dirs(self.cfg)["insights"] / "acme-widgets-7.json"
        target.write_text(json.dumps(team_reviewer.brief_to_insights("# old", REPO, 7, HEAD[:7])))
        os.utime(target, (1, 1))
        (briefs / f"widgets-7-{HEAD[:7]}.md").write_text(BRIEF)
        team_reviewer.sync_briefs(self.cfg, [make_pr()])
        self.assertEqual(len(json.loads(target.read_text())["recommendations"]), 5)

    def test_sync_briefs_noop_without_adapter(self):
        team_reviewer.sync_briefs(self.cfg, [make_pr()])
        self.assertEqual(list(config.dirs(self.cfg)["insights"].glob("*.json")), [])


class InsightsHardeningTests(TmpCase):
    def rec(self, **kw):
        return good_insights(recommendations=[{"severity": "nit", "title": "t", **kw}])

    def test_line_numbers_coerced_or_rejected(self):
        r = insights.validate(self.rec(start_line="11", end_line=" 12 "))["recommendations"][0]
        self.assertEqual((r["start_line"], r["end_line"]), (11, 12))
        r = insights.validate(self.rec(start_line=None))["recommendations"][0]
        self.assertEqual((r["start_line"], r["end_line"]), (None, None))
        for bad in ("abc", 1.5, True, [3], 0, -2, "1x"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                insights.validate(self.rec(start_line=bad))
        with self.assertRaises(ValueError):
            insights.validate(self.rec(start_line=3, end_line="x"))

    def test_short_head_sha_is_not_current(self):
        self.assertTrue(insights.is_current(HEAD, HEAD[:7]))
        self.assertTrue(insights.is_current(HEAD, HEAD))
        self.assertFalse(insights.is_current(HEAD, HEAD[:6]))
        self.assertFalse(insights.is_current(HEAD, ""))


if __name__ == "__main__":
    unittest.main()
