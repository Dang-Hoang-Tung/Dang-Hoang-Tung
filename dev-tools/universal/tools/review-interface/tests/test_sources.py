"""Sources: one repo, or every repo under an owner; and the cache clones for repos without a clone."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401
from app.services import git, github, sources

OWNER = {"owner": "acme", "search": "review-requested:@me", "clone": "/code/{name}", "exclude": ["acme/old-*"]}


def fake_run(found, listed=({"number": 1, "title": "t"},)):
    def fake(*args, **kw):
        if args[:2] == ("gh", "api"):
            return json.dumps(found)
        if args[:3] == ("gh", "pr", "view"):
            return json.dumps({"number": int(args[3]), "title": "t"})
        if args[:3] == ("gh", "pr", "list"):
            return json.dumps(list(listed))
        if args[:3] == ("gh", "repo", "view"):
            return "main\n"
        raise AssertionError(args)
    return fake


class OwnerSourceTests(unittest.TestCase):
    def test_owner_search_lists_prs_from_every_repo_except_excluded(self):
        found = [["acme/app", 1], ["acme/chat", 2], ["acme/old-site", 3], ["other/x", 4]]
        with mock.patch.object(github, "run", side_effect=fake_run(found)):
            prs = github.list_pending({"sources": [OWNER]})
        self.assertEqual([(p["repo"], p["number"]) for p in prs], [("acme/app", 1), ("acme/chat", 2)])
        self.assertEqual(prs[1]["source"]["clone"], "/code/chat")
        self.assertNotIn("owner", prs[1]["source"])

    def test_search_is_scoped_to_the_owner_newest_first_and_one_page(self):
        calls = []
        def fake(*args, **kw):
            calls.append(args)
            return "[]"
        with mock.patch.object(github, "run", side_effect=fake):
            github.list_pending({"sources": [dict(OWNER, limit=500)]})
        args = calls[0]
        self.assertIn("q=is:pr is:open user:acme review-requested:@me", args)
        self.assertIn("sort=created", args)
        self.assertIn("order=desc", args)
        self.assertIn("per_page=100", args)

    def test_a_pr_found_by_two_sources_is_listed_once(self):
        sources_ = [{"repo": "acme/app"}, OWNER]
        with mock.patch.object(github, "run", side_effect=fake_run([["acme/app", 1]])):
            prs = github.list_pending({"sources": sources_})
        self.assertEqual([(p["repo"], p["number"]) for p in prs], [("acme/app", 1)])
        self.assertEqual(prs[0]["source"], {"repo": "acme/app"})

    def test_first_source_wins_when_listing(self):
        own = {"repo": "acme/x", "clone": "/own/x"}
        fake = fake_run([["acme/x", 5]], listed=[{"number": 5, "title": "t"}])
        with mock.patch.object(github, "run", side_effect=fake) as run:
            prs = github.list_pending({"sources": [own, OWNER]})
        self.assertEqual([(p["repo"], p["number"]) for p in prs], [("acme/x", 5)])
        self.assertEqual(prs[0]["source"]["clone"], "/own/x")
        self.assertNotIn(("gh", "pr", "view"), [c.args[:3] for c in run.call_args_list])

    def test_explicit_pr_under_an_owner(self):
        with mock.patch.object(github, "run", side_effect=fake_run([])):
            prs = github.list_pending({"sources": [OWNER]}, only=[("acme/chat", 9), ("acme/old-site", 3)])
        self.assertEqual([(p["repo"], p["number"]) for p in prs], [("acme/chat", 9)])


class BarePrNumberTests(unittest.TestCase):
    def test_bare_number_goes_to_the_first_repo_source_even_after_an_owner(self):
        cfg = {"sources": [dict(OWNER, owner="other"), {"repo": "acme/app"}]}
        with mock.patch.object(github, "run", side_effect=fake_run([])):
            prs = github.list_pending(cfg, only=[(None, 7)])
        self.assertEqual([(p["repo"], p["number"]) for p in prs], [("acme/app", 7)])

    def test_bare_number_without_a_repo_source_says_how_to_give_it(self):
        with mock.patch.object(github, "run", side_effect=fake_run([])), mock.patch("sys.stderr") as err:
            prs = github.list_pending({"sources": [OWNER]}, only=[(None, 7)])
        self.assertEqual(prs, [])
        self.assertIn("owner/repo#N", "".join(c.args[0] for c in err.write.call_args_list))


class DefaultBranchTests(unittest.TestCase):
    def setUp(self):
        github._default_branches.clear()

    def test_listed_prs_carry_the_repo_default_branch_looked_up_once(self):
        calls = []
        def fake(*args, **kw):
            calls.append(args[:3])
            return fake_run([["acme/app", 1], ["acme/app", 2]])(*args, **kw)
        with mock.patch.object(github, "run", side_effect=fake):
            prs = github.list_pending({"sources": [OWNER]})
        self.assertEqual([p["defaultBranch"] for p in prs], ["main", "main"])
        self.assertEqual(calls.count(("gh", "repo", "view")), 1)

    def test_unreadable_default_branch_is_none(self):
        with mock.patch.object(github, "run", side_effect=subprocess.CalledProcessError(1, "gh")), mock.patch("sys.stderr"):
            self.assertIsNone(github.default_branch("acme/app"))


class SourcesTests(unittest.TestCase):
    def test_matching_ignores_case(self):
        src = dict(OWNER, owner="Acme", exclude=["ACME/Old-*"])
        self.assertTrue(sources.covers(src, "acme/chat"))
        self.assertFalse(sources.covers(src, "acme/old-site"))
        self.assertTrue(sources.covers({"repo": "Acme/App"}, "acme/app"))

    def test_for_repo_fills_in_the_repo(self):
        cfg = {"sources": [{"repo": "acme/app", "clone": "/x"}, OWNER]}
        self.assertEqual(sources.for_repo(cfg, "acme/app"), {"repo": "acme/app", "clone": "/x"})
        self.assertEqual(sources.for_repo(cfg, "acme/chat")["clone"], "/code/chat")
        self.assertIsNone(sources.for_repo(cfg, "acme/old-site"))
        self.assertIsNone(sources.for_repo(cfg, "other/x"))

    def test_validate_accepts_repo_or_owner_sources(self):
        sources.validate([{"repo": "acme/app", "clone": "/x"}, OWNER])

    def test_validate_rejects_bad_entries(self):
        for bad in ({}, {"repo": "a/b", "owner": "a"}, dict(OWNER, clone="/code/{nam}"), dict(OWNER, clone="/code/{}"),
                    dict(OWNER, exclude="acme/old-*"), dict(OWNER, limit="50"), dict(OWNER, limit=True)):
            with self.assertRaises(SystemExit, msg=bad):
                sources.validate([bad])


class CacheCloneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = {"data_dir": self.tmp.name, "auto_clone": True}
        self.cache = Path(self.tmp.name, "clones", "acme", "chat")

    def fake_clone(self, calls):
        def fake(*args, **kw):
            calls.append(args)
            Path(args[4], ".git").mkdir(parents=True)
            return ""
        return fake

    def test_own_clone_is_kept(self):
        own = Path(self.tmp.name, "own")
        (own / ".git").mkdir(parents=True)
        src = {"repo": "acme/app", "clone": str(own)}
        with mock.patch.object(git, "run", side_effect=AssertionError):
            self.assertIs(git.ensure_clone(self.cfg, src), src)

    def test_missing_clone_makes_a_blobless_cache_clone(self):
        calls = []
        with mock.patch.object(git, "run", side_effect=self.fake_clone(calls)), mock.patch("sys.stderr") as err:
            src = git.ensure_clone(self.cfg, {"repo": "acme/chat", "clone": "/nope/chat"})
        self.assertEqual(src["clone"], str(self.cache))
        self.assertIn("--filter=blob:none", calls[0])
        self.assertIn("--no-checkout", calls[0])
        self.assertTrue(self.cache.joinpath(".git").exists())
        self.assertEqual(list(self.cache.parent.glob("*.tmp-*")), [])
        self.assertIn("cloning acme/chat", "".join(c.args[0] for c in err.write.call_args_list))

    def test_existing_cache_clone_is_reused(self):
        (self.cache / ".git").mkdir(parents=True)
        with mock.patch.object(git, "run", side_effect=AssertionError):
            src = git.ensure_clone(self.cfg, {"repo": "acme/chat"})
        self.assertEqual(src["clone"], str(self.cache))

    def test_failed_clone_leaves_no_clone_and_no_temp_dir(self):
        def fake(*args, **kw):
            Path(args[4], ".git").mkdir(parents=True)
            raise subprocess.CalledProcessError(1, "gh", stderr="no access")
        with mock.patch.object(git, "run", side_effect=fake), mock.patch("sys.stderr") as err:
            src = git.ensure_clone(self.cfg, {"repo": "acme/chat"})
        self.assertNotIn("clone", src)
        self.assertEqual(list(self.cache.parent.glob("*")), [])
        self.assertIn("no access", "".join(c.args[0] for c in err.write.call_args_list))

    def test_stale_temp_dirs_from_a_killed_clone_are_swept(self):
        stale = Path(f"{self.cache}.tmp-1")
        (stale / ".git").mkdir(parents=True)
        with mock.patch.object(git, "run", side_effect=self.fake_clone([])), mock.patch("sys.stderr"):
            git.ensure_clone(self.cfg, {"repo": "acme/chat"})
        self.assertFalse(stale.exists())
        self.assertTrue(self.cache.joinpath(".git").exists())

    def test_cached_clone_never_clones(self):
        with mock.patch.object(git, "run", side_effect=AssertionError):
            self.assertNotIn("clone", git.cached_clone(self.cfg, {"repo": "acme/chat"}))

    def test_no_cache_clone_when_auto_clone_is_off(self):
        with mock.patch.object(git, "run", side_effect=AssertionError):
            self.assertNotIn("clone", git.ensure_clone(dict(self.cfg, auto_clone=False), {"repo": "acme/chat"}))

    def test_clone_for_finds_existing_clones_only(self):
        cfg = dict(self.cfg, sources=[{"owner": "acme", "clone": "/nope/{name}"}])
        self.assertIsNone(git.clone_for(cfg, "acme/chat"))
        self.assertIsNone(git.clone_for(cfg, "other/x"))
        (self.cache / ".git").mkdir(parents=True)
        self.assertEqual(git.clone_for(cfg, "acme/chat"), str(self.cache))


if __name__ == "__main__":
    unittest.main()
