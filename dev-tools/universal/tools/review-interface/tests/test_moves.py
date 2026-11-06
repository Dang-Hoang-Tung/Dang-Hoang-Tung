"""Moved-code detection (real git output) and the git diff arguments."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401
from app.services import diff as diffmod
from app.services import git

BLOCK = ["    alphaFunction(first);", "    betaFunction(second);", "    gammaFunction(third);", "    deltaFunction(fourth);"]
FILLER = [f"line {i}" for i in range(40)]
ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def sh(repo, *args):
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, env=ENV)


def write(repo, name, lines):
    Path(repo, name).write_text("\n".join(lines) + "\n")


class RepoCase(unittest.TestCase):
    def make_diff(self, before, after):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        repo = tmp.name
        sh(repo, "init", "-q", "-b", "main")
        for name, lines in before.items():
            write(repo, name, lines)
        sh(repo, "add", "-A")
        sh(repo, "commit", "-qm", "base")
        sh(repo, "checkout", "-qb", "pr")
        for name, lines in after.items():
            write(repo, name, lines)
        sh(repo, "add", "-A")
        sh(repo, "commit", "-qm", "head")
        return git.diff(repo, "main...pr")

    def moves(self, d):
        files = diffmod.parse_diff(d, [])
        return files, diffmod.find_moves(files, d.moved)


@unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git missing")
class MoveTests(RepoCase):
    def test_reindented_block_within_file(self):
        before = FILLER[:10] + BLOCK + FILLER[10:]
        after = FILLER[:30] + ["  " + x.strip() for x in BLOCK] + FILLER[30:]
        files, m = self.moves(self.make_diff({"a.ts": before}, {"a.ts": after}))
        rows = files[0]["rows"]
        to = {k: v for k, v in m[0].items() if v["dir"] == "to"}
        frm = {k: v for k, v in m[0].items() if v["dir"] == "from"}
        self.assertEqual(len(to), 4)
        self.assertEqual(len(frm), 4)
        self.assertEqual([k for k, v in to.items() if v["start"]], [min(to, key=int)])
        first_to, first_from = min(to, key=int), min(frm, key=int)
        self.assertEqual(to[first_to], {"dir": "to", "file": 0, "row": int(first_from), "path": "a.ts",
                                        "line": rows[int(first_from)][2], "start": True})
        self.assertEqual(frm[first_from]["row"], int(first_to))
        self.assertEqual(frm[first_from]["line"], rows[int(first_to)][1])
        self.assertEqual(sum(v["start"] for v in m[0].values()), 2)

    def test_block_moved_across_files(self):
        before = {"a.ts": FILLER[:10] + BLOCK + FILLER[10:], "b.ts": FILLER}
        after = {"a.ts": FILLER[:10] + FILLER[10:], "b.ts": FILLER[:5] + BLOCK + FILLER[5:]}
        files, m = self.moves(self.make_diff(before, after))
        first_to, first_from = min(m[0], key=int), min(m[1], key=int)
        self.assertEqual(m[0][first_to]["dir"], "to")
        self.assertEqual((m[0][first_to]["file"], m[0][first_to]["path"]), (1, "b.ts"))
        self.assertEqual(m[0][first_to]["row"], int(first_from))
        self.assertEqual(m[1][first_from]["dir"], "from")
        self.assertEqual((m[1][first_from]["file"], m[1][first_from]["row"], m[1][first_from]["path"]), (0, int(first_to), "a.ts"))
        self.assertEqual(sum(v["start"] for f in m for v in f.values()), 2)

    def test_plain_edit_not_marked(self):
        files, m = self.moves(self.make_diff({"a.ts": FILLER}, {"a.ts": FILLER[:5] + ["new one", "new two"] + FILLER[5:]}))
        self.assertEqual(m, [{}])

    def test_rows_stay_four_columns(self):
        before = {"a.ts": FILLER[:10] + BLOCK + FILLER[10:], "b.ts": FILLER}
        after = {"a.ts": FILLER, "b.ts": FILLER[:5] + BLOCK + FILLER[5:]}
        d = self.make_diff(before, after)
        files = diffmod.parse_diff(d, [])
        self.assertTrue(all(len(r) == 4 for f in files for r in f["rows"]))


class PairingTests(unittest.TestCase):
    def colored(self, body):
        return ("\x1b[1mdiff --git a/a.ts b/a.ts\x1b[m\n\x1b[1m--- a/a.ts\x1b[m\n\x1b[1m+++ b/a.ts\x1b[m\n\x1b[36m@@ -1,5 +1,5 @@\x1b[m\n" + body)

    def test_no_counterpart_gives_nulls(self):
        d = ("diff --git a/a.ts b/a.ts\n--- a/a.ts\n+++ b/a.ts\n@@ -1,5 +1,5 @@\n-one()\n-two()\n-three()\n ctx\n+other()\n")
        col = self.colored("\x1b[35m-one()\x1b[m\n\x1b[35m-two()\x1b[m\n\x1b[35m-three()\x1b[m\n ctx\n\x1b[36m+other()\x1b[m\n")
        files = diffmod.parse_diff(d, [])
        m = diffmod.find_moves(files, col)[0]
        self.assertEqual(m["1"], {"dir": "to", "file": None, "row": None, "path": None, "line": None, "start": True})
        self.assertEqual({k: v["start"] for k, v in m.items()}, {"1": True, "2": False, "3": False, "5": True})
        self.assertEqual(m["5"]["dir"], "from")

    def test_api_diff_has_no_moves(self):
        d = "diff --git a/a.ts b/a.ts\n--- a/a.ts\n+++ b/a.ts\n@@ -1 +1 @@\n-a\n+b\n"
        files = diffmod.parse_diff(d, [])
        self.assertEqual(diffmod.find_moves(files, None), [{}])
        self.assertEqual(getattr(d, "moved", None), None)


class GitArgsTests(unittest.TestCase):
    def test_histogram(self):
        with mock.patch.object(git, "run", return_value="") as run:
            git.diff("/c", "base...head")
        plain, moved = (c.args for c in run.call_args_list)
        for args in (plain, moved):
            self.assertIn("--histogram", args)
            self.assertIn("-U12", args)
            self.assertIn("base...head", args)
        self.assertIn("--color-moved=blocks", moved)
        self.assertIn("--color-moved-ws=allow-indentation-change", moved)


if __name__ == "__main__":
    unittest.main()
