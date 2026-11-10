"""Build orchestration and the CLI."""
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
from app import cli, config
from app.services import build as builder
from app.services import git, github, manifest, state

from helpers import *  # noqa: F401,F403


class BuildHelper(TmpCase):
    def run_build(self, pr, diff_text=DIFF, only=None):
        review, queue = mock.Mock(), mock.Mock()
        review.render.side_effect = lambda m: f"review {m['pr']['slug']}"
        queue.render.side_effect = lambda m: f"queue {len(m['buckets'])}"
        with mock.patch.object(builder, "review_page", review), mock.patch.object(builder, "queue_page", queue), \
                mock.patch("sys.stdout"), mock.patch("app.services.gh_sync.sync", return_value=0), \
                mock.patch.object(github, "list_pending", return_value=[pr]), \
                mock.patch.object(github, "fetch_api_diff", return_value=diff_text), \
                mock.patch.object(github, "requested_at", return_value="2026-11-02T00:00:00Z"):
            return builder.build(self.cfg, only), review, queue


class BuildTests(BuildHelper):
    def test_build_writes_files_and_manifest(self):
        self.cfg["user_name"] = "Tony"
        m, review, queue = self.run_build(make_pr())
        d = config.dirs(self.cfg)
        self.assertEqual((d["pages"] / "acme-widgets-7.html").read_text(), "review acme-widgets-7")
        self.assertEqual((d["pages"] / "index.html").read_text(), "queue 1")
        self.assertEqual((d["diffs"] / "acme-widgets-7.diff").read_text(), DIFF)
        summary = json.loads((d["pages"] / "acme-widgets-7.json").read_text())
        self.assertEqual((summary["number"], summary["added"], summary["insights_status"]), (7, 3, "missing"))
        self.assertEqual(queue.render.call_args[0][0]["user"], "Tony")
        self.assertEqual(queue.render.call_args[0][0]["buckets"][0]["items"][0]["requested_at"], "2026-11-02T00:00:00Z")
        on_disk = json.loads((d["root"] / "manifest.json").read_text())
        self.assertEqual(on_disk["prs"][0]["requested_at"], "2026-11-02T00:00:00Z")
        self.assertEqual(on_disk["prs"], m["prs"])

    def test_build_uses_clone_diff_when_configured(self):
        pr = make_pr(source={"repo": REPO, "clone": "/x"})
        with mock.patch.object(git, "has_clone", return_value=True), mock.patch.object(git, "fetch_diff", return_value="diff --git a/a b/a\n") as g:
            self.assertEqual(builder.fetch_diff(pr), "diff --git a/a b/a\n")
        g.assert_called_once_with(pr)

    def test_fetch_failure_skips_pr(self):
        err = subprocess.CalledProcessError(1, "gh", stderr="boom")
        with mock.patch.object(github, "fetch_api_diff", side_effect=err), mock.patch("sys.stderr"):
            self.assertEqual(builder.fetch_diffs([make_pr()]), {})


class CliTests(TmpCase):
    def test_parse_pr(self):
        self.assertEqual(cli.parse_pr("12"), (None, 12))
        self.assertEqual(cli.parse_pr("a/b#12"), ("a/b", 12))

    def test_default_command_is_build(self):
        self.assertEqual(cli.normalise_argv([]), ["build"])
        self.assertEqual(cli.normalise_argv(["12"]), ["build", "12"])
        self.assertEqual(cli.normalise_argv(["--config", "c.json", "paths"]), ["--config", "c.json", "paths"])
        self.assertEqual(cli.normalise_argv(["--config", "c.json", "--no-open"]), ["--config", "c.json", "build", "--no-open"])

    def test_ai_reply_appends_message(self):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t", [msg("1", "me", "q", "1")])]})
        with mock.patch("sys.stdout"):
            cli.ai_reply(self.cfg, "acme-widgets-7", "t", "answer")
        last = state.load_state(self.cfg, "acme-widgets-7")["threads"][0]["messages"][-1]
        self.assertEqual((last["who"], last["text"]), ("ai", "answer"))
        self.assertEqual(state.waiting_threads(state.load_state(self.cfg, "acme-widgets-7")), [])

    def test_thinking_notes_show_while_waiting_then_move_onto_the_reply(self):
        state.save_state(self.cfg, "acme-widgets-7", {"threads": [thread("t", [msg("1", "me", "q", "1")])]})
        with mock.patch("sys.stdout"):
            cli.ai_thinking(self.cfg, "acme-widgets-7", "t", "reading the diff")
            cli.ai_thinking(self.cfg, "acme-widgets-7", "t", "checking callers")
        t = state.load_state(self.cfg, "acme-widgets-7")["threads"][0]
        self.assertEqual([n["text"] for n in t["thinking"]], ["reading the diff", "checking callers"])
        self.assertEqual(len(state.waiting_threads(state.load_state(self.cfg, "acme-widgets-7"))), 1)
        with mock.patch("sys.stdout"):
            cli.ai_reply(self.cfg, "acme-widgets-7", "t", "answer")
        t = state.load_state(self.cfg, "acme-widgets-7")["threads"][0]
        self.assertNotIn("thinking", t)
        self.assertEqual([n["text"] for n in t["messages"][-1]["steps"]], ["reading the diff", "checking callers"])

    def test_ensure_server_starts_module_from_repo_root(self):
        calls = []
        with mock.patch.object(cli, "server_info", side_effect=[None, {"port": 1, "token": "t"}]), \
                mock.patch.object(cli.subprocess, "Popen", side_effect=lambda *a, **k: calls.append((a, k))), \
                mock.patch.object(cli.time, "sleep"):
            info = cli.ensure_server(self.cfg)
        self.assertEqual(info["port"], 1)
        args, kw = calls[0]
        self.assertEqual(args[0][1:4], ["-m", "app.server.http", "--config"])
        self.assertEqual(kw["cwd"], str(config.ROOT))

    def test_queue_url(self):
        self.assertEqual(cli.queue_url({"port": 5, "token": "t"}, "x.html"), "http://127.0.0.1:5/?t=t&next=x.html")


class PartialBuildTests(BuildHelper):
    def manifest_slugs(self):
        return [p["slug"] for p in manifest.read_manifest(self.cfg)["prs"]]

    def test_only_keeps_other_entries_and_queue_lists_all(self):
        self.run_build(make_pr(number=7))
        _, _, queue = self.run_build(make_pr(number=8, title="Other"), only=[(None, 8)])
        self.assertEqual(self.manifest_slugs(), ["acme-widgets-7", "acme-widgets-8"])
        self.assertEqual(sorted(i["number"] for b in queue.render.call_args[0][0]["buckets"] for i in b["items"]), [7, 8])

    def test_full_build_drops_prs_no_longer_pending(self):
        self.run_build(make_pr(number=7))
        self.run_build(make_pr(number=8))
        self.assertEqual(self.manifest_slugs(), ["acme-widgets-8"])

    def test_failed_diff_keeps_previous_entry(self):
        self.run_build(make_pr(number=7, title="Old"))
        with mock.patch.object(github, "fetch_api_diff", side_effect=subprocess.CalledProcessError(1, "gh", stderr="x")), \
                mock.patch.object(github, "list_pending", return_value=[make_pr(number=7, title="New")]), \
                mock.patch.object(builder, "review_page"), mock.patch.object(builder, "queue_page") as q, \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            q.render.return_value = "q"
            m = builder.build(self.cfg)
        self.assertEqual([p["title"] for p in m["prs"]], ["Old"])

    def test_one_bad_pr_does_not_abort_the_run(self):
        good, bad = make_pr(number=7), make_pr(number=8)
        real = builder.build_pr

        def flaky(cfg, pr, diff_text, name):
            if pr["number"] == 8:
                raise RuntimeError("render exploded")
            return real(cfg, pr, diff_text, name)
        with mock.patch.object(builder, "build_pr", side_effect=flaky), mock.patch.object(builder, "review_page") as rp, \
                mock.patch.object(builder, "queue_page") as qp, mock.patch.object(github, "list_pending", return_value=[bad, good]), \
                mock.patch.object(github, "fetch_api_diff", return_value=DIFF), \
                mock.patch.object(github, "requested_at", return_value="2026-11-02T00:00:00Z"), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr") as err:
            rp.render.return_value = qp.render.return_value = "x"
            m = builder.build(self.cfg)
        self.assertEqual([p["slug"] for p in m["prs"]], ["acme-widgets-7"])
        self.assertTrue(err.write.called)


class ListPendingTests(unittest.TestCase):
    CFG = {"sources": [{"repo": "a/one"}, {"repo": "b/two"}]}

    def test_bare_number_applies_to_first_source_only(self):
        calls = []
        with mock.patch.object(github, "run", side_effect=lambda *a, **k: calls.append(a) or '{"number": 5}'):
            out = github.list_pending(self.CFG, [(None, 5)])
        self.assertEqual([p["repo"] for p in out], ["a/one"])
        self.assertEqual(len(calls), 1)

    def test_explicit_repo_goes_to_its_source(self):
        with mock.patch.object(github, "run", return_value='{"number": 5}'):
            self.assertEqual([p["repo"] for p in github.list_pending(self.CFG, [("b/two", 5)])], ["b/two"])

    def test_failures_are_skipped_per_source_and_per_pr(self):
        boom = subprocess.CalledProcessError(1, "gh", stderr="no access")

        def fake(*a, **k):
            if "a/one" in a:
                raise boom
            return '[{"number": 1}]'
        with mock.patch.object(github, "run", side_effect=fake), mock.patch("sys.stderr"):
            self.assertEqual([p["repo"] for p in github.list_pending(self.CFG)], ["b/two"])

        def fake_view(*a, **k):
            if "5" in a:
                raise boom
            return '{"number": 6}'
        with mock.patch.object(github, "run", side_effect=fake_view), mock.patch("sys.stderr"):
            out = github.list_pending({"sources": [{"repo": "a/one"}]}, [("a/one", 5), ("a/one", 6)])
        self.assertEqual([p["number"] for p in out], [6])


if __name__ == "__main__":
    unittest.main()
