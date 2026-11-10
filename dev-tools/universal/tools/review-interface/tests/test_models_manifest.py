"""View models, manifest and CI state."""
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
from app.services import github, insights, manifest, models, state

from helpers import *  # noqa: F401,F403


class ReviewModelTests(TmpCase):
    def model(self, pr=None, ins=None, status="missing", user="tony", diff_text=DIFF):
        return models.review_model(self.cfg, pr or make_pr(), diff_text, ins, status, user)

    def test_without_insights(self):
        m = self.model()
        self.assertFalse(m["summary"]["has_insights"])
        self.assertEqual(m["notes"], [])
        self.assertEqual(m["pr"]["slug"], "acme-widgets-7")
        self.assertEqual(m["pr"]["head_sha"], HEAD)
        self.assertEqual((m["pr"]["repo"], m["pr"]["number"], m["pr"]["author"]), (REPO, 7, "alice"))
        self.assertEqual(m["user"], "tony")
        self.assertEqual(len(m["files"]), 3)
        self.assertEqual(m["summary"]["minutes_source"], "estimate")
        self.assertEqual(m["summary"]["description"], "Some **description**")
        self.assertEqual(m["summary"]["tldr"], [])
        t = m["totals"]
        self.assertEqual((t["added"], t["deleted"], t["files"], t["effort"]), (2 + 1, 1 + 1, 3, "Small"))
        self.assertEqual((t["added_all"], t["deleted_all"]), (4, 3))
        self.assertEqual(m["banners"], [])

    def test_no_description_is_none(self):
        self.assertIsNone(self.model(pr=make_pr(body=""))["summary"]["description"])

    def test_json_serialisable(self):
        json.dumps(self.model(ins=insights.validate(good_insights()), status="current"))

    def test_with_insights_notes_mapped(self):
        m = self.model(ins=insights.validate(good_insights()), status="current")
        self.assertTrue(m["summary"]["has_insights"])
        self.assertEqual(m["summary"]["description"], "Some **description**")
        self.assertEqual(m["summary"]["tldr"], ["What: widget"])
        self.assertEqual(m["summary"]["questions"], ["Why?"])
        self.assertEqual(len(m["notes"]), 2)
        note = next(n for n in m["notes"] if n["key"] == "r1")
        fidx = next(f["idx"] for f in m["files"] if f["path"] == "src/app/Widget.tsx")
        self.assertEqual(note["file"], fidx)
        self.assertEqual(note["rows"], [f"r{fidx}-3", f"r{fidx}-4"])
        self.assertEqual(note["endRow"], f"r{fidx}-4")
        general = next(n for n in m["notes"] if n["title"] == "General nit")
        self.assertIsNone(general["file"])
        self.assertEqual(general["rows"], [])
        self.assertIsNone(general["endRow"])
        self.assertRegex(general["key"], r"^[0-9a-f]{10}$")
        self.assertEqual(m["files"][fidx]["notes"], ["r1"])
        self.assertEqual(m["files"][fidx]["kind"], "should")
        s = m["summary"]
        self.assertEqual((s["minutes"], s["minutes_source"], s["risk"], s["verdict"]), (25, "insights", "Medium", "Approve with nits"))

    def test_rows_are_lists_with_ids_matching_row_index(self):
        m = self.model()
        f = m["files"][0]
        self.assertEqual(f["rows"][0][0], "hunk")
        self.assertEqual(f["rows"][3], ["add", None, 11, "  const b = 3;"])

    def test_notes_sorted_by_severity(self):
        ins = insights.validate(good_insights(recommendations=[
            {"severity": "nit", "title": "n"}, {"severity": "block", "title": "b"}, {"severity": "look", "title": "l"}]))
        self.assertEqual([n["kind"] for n in self.model(ins=ins, status="current")["notes"]], ["block", "nit", "look"])

    def test_note_path_resolves_by_file_name(self):
        ins = insights.validate(good_insights(recommendations=[
            {"severity": "nit", "title": "n", "path": "util.ts", "start_line": 2}, {"severity": "nit", "title": "gone", "path": "nope.ts", "start_line": 2}]))
        notes = {n["title"]: n for n in self.model(ins=ins, status="current")["notes"]}
        self.assertEqual(notes["n"]["file"], 1)
        self.assertIsNone(notes["gone"]["file"])
        self.assertIsNone(notes["gone"]["start"])

    def test_banners(self):
        self.assertEqual(self.model(pr=make_pr(isDraft=True))["banners"], [{"type": "draft"}])
        self.assertEqual(self.model(pr=make_pr(baseRefName="feature/x"))["banners"], [{"type": "stacked", "base": "feature/x"}])
        ins = insights.validate(good_insights(head_sha="deadbee"))
        self.assertEqual(self.model(ins=ins, status="stale")["banners"], [{"type": "stale", "from": "deadbee", "to": HEAD[:7]}])
        self.assertEqual(self.model(status="invalid: schema must be x")["banners"], [{"type": "invalid", "reason": "schema must be x"}])

    def test_ci(self):
        self.assertEqual(self.model(pr=make_pr(statusCheckRollup=[{"conclusion": "FAILURE"}]))["pr"]["ci"], "failing")
        self.assertEqual(self.model()["pr"]["ci"], "none")

    def test_generated_file_flagged_and_kept_in_tree_order(self):
        m = self.model()
        gen = next(f for f in m["files"] if f["path"].endswith("api.ts"))
        self.assertTrue(gen["gen"])
        self.assertNotEqual(gen["layer"], "Generated")
        self.assertEqual(m["order"], models.leaf_order(m["tree"]))
        self.assertEqual(sorted(m["order"]), [0, 1, 2])

    def test_tree_and_layout(self):
        m = self.model()
        self.assertEqual([t["name"] for t in m["tree"]], ["src"])
        leaf_idx = sorted(n["file"] for n in m["tree_layout"]["nodes"] if n["role"] == "leaf")
        self.assertEqual(leaf_idx, [0, 1, 2])
        self.assertEqual(m["tree_layout"]["nodes"][0]["label"], "widgets")

    def test_effort_and_minutes_estimate(self):
        self.assertEqual(models.effort_of(99), "Small")
        self.assertEqual(models.effort_of(100), "Medium")
        self.assertEqual(models.effort_of(400), "Large")
        self.assertEqual(models.estimate_minutes(0, ""), 2)
        self.assertEqual(models.estimate_minutes(500, "High"), 15)

    def test_pr_summary(self):
        m = self.model(ins=insights.validate(good_insights()), status="current")
        s = models.pr_summary(m, "current")
        json.dumps(s)
        self.assertEqual(s["findings"], {"should": 1, "nit": 1})
        self.assertEqual((s["insights_status"], s["number"], s["base"]), ("current", 7, "main"))
        self.assertEqual(s["summary"]["tldr"], ["What: widget"])


class QueueModelTests(unittest.TestCase):
    def test_groups_by_author_case_insensitive_and_orders_oldest_first(self):
        items = [models.queue_item(summary_for("a-b-1", 1, "bob"), "2026-11-03T00:00:00Z", {}),
                 models.queue_item(summary_for("a-b-2", 2, "Alice", 5), "2026-11-02T00:00:00Z", {}),
                 models.queue_item(summary_for("a-b-3", 3, "bob", 7), "2026-11-01T00:00:00Z", {}),
                 models.queue_item(summary_for("a-b-4", 4, "alice", 3), "2026-11-04T00:00:00Z", {})]
        q = models.queue_model(items, "Tony")
        self.assertEqual(q["user"], "Tony")
        self.assertEqual(q["total_minutes"], 25)
        self.assertEqual(q["authors"], ["bob", "Alice", "alice"])
        self.assertEqual([b["author"] for b in q["buckets"]], q["authors"])
        bob = q["buckets"][0]
        self.assertEqual([i["number"] for i in bob["items"]], [3, 1])

    def test_avatar_strips_app_prefix(self):
        q = models.queue_model([models.queue_item(summary_for("a-b-1", 1, "app/dependabot"), "2026-11-01T00:00:00Z", {}),
                                models.queue_item(summary_for("a-b-2", 2, "carol"), "2026-11-01T00:00:00Z", {})], "")
        self.assertEqual([b["avatar"] for b in q["buckets"]],
                         ["https://github.com/dependabot.png?size=48", "https://github.com/carol.png?size=48"])

    def test_empty_queue(self):
        self.assertEqual(models.queue_model([], "x"), {"user": "x", "total_minutes": 0, "authors": [], "buckets": []})

    def test_item_carries_threads_and_design_keys(self):
        st = {"threads": [thread("h", [msg("1", "me", "q", "1")]), thread("r", [msg("1", "me", "q", "1")], resolved=True)]}
        item = models.queue_item(summary_for("a-b-1", 1, "bob", findings={"nit": 2}), "2026-11-01T00:00:00Z", st)
        self.assertEqual((item["threads"], item["open_threads"]), (2, 1))
        self.assertEqual(item["requested_at"], "2026-11-01T00:00:00Z")
        self.assertEqual(sorted(item), sorted(["slug", "number", "title", "url", "author", "requested_at", "head_sha", "ci", "draft", "effort",
                                               "minutes", "minutes_source", "added", "deleted", "files", "verdict", "risk", "findings",
                                               "has_insights", "threads", "open_threads", "approved", "summary", "created"]))
        self.assertFalse(item["approved"])
        self.assertEqual(item["created"], "2026-11-01T00:00:00Z")

        st["approval"] = {"commit": HEAD}
        self.assertTrue(models.queue_item(summary_for("a-b-1", 1, "bob"), "2026-11-01T00:00:00Z", st)["approved"])


class ManifestTests(TmpCase):

    def test_buckets_by_count_then_oldest_pr(self):
        mk = lambda n, author, created: {"author": author, "minutes": 1, "created": created, "requested_at": created, "number": n}
        model = models.queue_model([mk(1, "amy", "2026-11-05T00:00:00Z"), mk(2, "bea", "2026-10-01T00:00:00Z"),
                                    mk(3, "cal", "2026-11-01T00:00:00Z"), mk(4, "cal", "2026-11-02T00:00:00Z")], "Tony")
        self.assertEqual(model["authors"], ["cal", "bea", "amy"])

    def test_bucket_sorted_by_opened_oldest_first(self):
        mk = lambda n, created, req: {"author": "bob", "minutes": 1, "created": created, "requested_at": req, "number": n}
        model = models.queue_model([mk(1, "2026-11-05T00:00:00Z", "2026-11-01T00:00:00Z"),
                                    mk(2, "2026-10-01T00:00:00Z", "2026-11-06T00:00:00Z")], "Tony")
        self.assertEqual([i["number"] for i in model["buckets"][0]["items"]], [2, 1])
    def test_entry_and_roundtrip(self):
        m = models.review_model(self.cfg, make_pr(), DIFF, None, "missing", "x")
        summary = models.pr_summary(m, "missing")
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t", [msg("1", "me", "q", "1")])]})
        entry = manifest.build_entry(self.cfg, summary, "2026-11-01T10:00:00Z", state.load_state(self.cfg, "acme-widgets-7"))
        self.assertEqual((entry["slug"], entry["pr"], entry["repo"], entry["requested_at"]), ("acme-widgets-7", 7, REPO, "2026-11-01T10:00:00Z"))
        self.assertEqual((entry["threads"], entry["waiting_threads"], entry["insights_status"]), (1, 1, "missing"))
        self.assertFalse(entry["approved"])
        state.save_state(self.cfg, "acme-widgets-7", {"approval": {"commit": HEAD[:7]}})
        self.assertTrue(manifest.build_entry(self.cfg, summary, "x", state.load_state(self.cfg, "acme-widgets-7"))["approved"])
        for key in ("page", "state_file", "insights_file", "diff_file"):
            self.assertIn("acme-widgets-7", entry[key])
        written = manifest.write_manifest(self.cfg, [entry])
        self.assertEqual(written["schema"], "review-manifest/1")
        self.assertEqual(manifest.read_manifest(self.cfg)["prs"], [entry])
        self.assertEqual(manifest.manifest_entry(self.cfg, "acme-widgets-7"), entry)
        self.assertIsNone(manifest.manifest_entry(self.cfg, "nope-1"))

    def test_read_missing(self):
        self.assertEqual(manifest.read_manifest(self.cfg), {"prs": []})


class CiStateTests(unittest.TestCase):
    def test_ci_state(self):
        self.assertEqual(github.ci_state(None), "none")
        self.assertEqual(github.ci_state([]), "none")
        self.assertEqual(github.ci_state([{"conclusion": "SUCCESS"}, {"state": "SUCCESS"}]), "passing")
        self.assertEqual(github.ci_state([{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}]), "failing")
        self.assertEqual(github.ci_state([{"state": "ERROR"}]), "failing")
        self.assertEqual(github.ci_state([{"conclusion": "SUCCESS"}, {"status": "IN_PROGRESS", "conclusion": ""}]), "pending")
        self.assertEqual(github.ci_state([{"state": "PENDING"}]), "pending")
        self.assertEqual(github.ci_state([{"conclusion": "failure"}, {"status": "QUEUED"}]), "failing")
        self.assertEqual(github.ci_state([{"conclusion": "SKIPPED"}, {"conclusion": "NEUTRAL"}]), "passing")


class ResolvePathTests(unittest.TestCase):
    PATHS = ["src/a/Widget.tsx", "src/b/Widget.tsx", "src/lib/util.ts", "web/util.ts", "pkg/only.ts", ".hidden/x.ts"]

    def test_resolution_rules(self):
        r = models.resolve_path
        self.assertEqual(r(self.PATHS, "src/lib/util.ts"), "src/lib/util.ts")
        self.assertEqual(r(self.PATHS, "./src/lib/util.ts"), "src/lib/util.ts")
        self.assertEqual(r(self.PATHS, "lib/util.ts"), "src/lib/util.ts")
        self.assertEqual(r(self.PATHS, "only.ts"), "pkg/only.ts")
        self.assertEqual(r(self.PATHS, "nope/only.ts"), "pkg/only.ts")
        self.assertIsNone(r(self.PATHS, "Widget.tsx"))
        self.assertIsNone(r(self.PATHS, "util.ts"))
        self.assertIsNone(r(self.PATHS, "missing.ts"))
        self.assertEqual(r(self.PATHS, ".hidden/x.ts"), ".hidden/x.ts")
        self.assertIsNone(r(self.PATHS, ""))

    def test_verdict_truncated_in_model_and_avatar_helper(self):
        ins = good_insights(summary={"verdict": "Approve. " + "x" * 80})
        self.assertEqual(models.build_summary(make_pr(), ins, ins["summary"], {"added": 1})["verdict"], "Approve")
        long = models.build_summary(make_pr(), {"x": 1}, {"verdict": "y" * 80}, {"added": 1})["verdict"]
        self.assertEqual(len(long), 40)
        self.assertEqual(models.avatar_url("app/bot", 36), "https://github.com/bot.png?size=36")


if __name__ == "__main__":
    unittest.main()
