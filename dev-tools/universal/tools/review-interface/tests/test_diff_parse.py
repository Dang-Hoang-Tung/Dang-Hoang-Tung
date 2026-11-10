"""Parsing git's output: line endings, no-newline markers, mode changes, generated files."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401
from app.services import diff as diffmod
from app.services import git
from app.services.shell import run

ENV = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def sh(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True, env=ENV).stdout.strip()


class LineEndingTests(unittest.TestCase):
    def test_lone_cr_stays_inside_its_line(self):
        self.assertEqual(run("python3", "-c", "import sys; sys.stdout.buffer.write(b'a\\rb\\n')"), "a\rb\n")
        self.assertEqual(run("python3", "-c", "import sys; sys.stdout.buffer.write(b'a\\r\\n')").split("\n"), ["a\r", ""])

    def test_invalid_utf8_is_replaced_unless_strict(self):
        code = "import sys; sys.stdout.buffer.write(b'a\\xffb')"
        self.assertEqual(run("python3", "-c", code), "a�b")
        with self.assertRaises(UnicodeDecodeError):
            run("python3", "-c", code, errors="strict")

    def test_crlf_rows_have_no_trailing_cr(self):
        rows, a, d = diffmod.parse_file_rows(["@@ -1,2 +1,2 @@", " keep\r", "-old\r", "+new\r"])
        self.assertEqual([r[3] for r in rows[1:]], ["keep", "old", "new"])
        self.assertEqual((a, d), (1, 1))


class HeaderTests(unittest.TestCase):
    DIFF = """diff --git a/a.ts b/a.ts
index 111..222 100644
--- a/a.ts
+++ b/a.ts
@@ -1,2 +1,2 @@
 keep
-old
\\ No newline at end of file
+new
diff --git a/run.sh b/run.sh
old mode 100644
new mode 100755
diff --git a/new.sh b/new.sh
new file mode 100755
index 0000000..333
--- /dev/null
+++ b/new.sh
@@ -0,0 +1 @@
+x
"""

    def test_no_newline_markers_are_recorded_per_side(self):
        files = diffmod.parse_diff(self.DIFF, [])
        self.assertEqual(files[0]["noeol"], {"old": True, "new": False})
        self.assertEqual([r[0] for r in files[0]["rows"]], ["hunk", "ctx", "del", "add"])
        self.assertNotIn("noeol", files[2])

    def test_context_marker_marks_both_sides(self):
        self.assertEqual(diffmod.no_eol(["@@ -1 +1 @@", " same", "\\ No newline at end of file"]), {"old": True, "new": True})

    def test_mode_only_change_is_a_file_with_modes(self):
        files = diffmod.parse_diff(self.DIFF, [])
        self.assertEqual([f["path"] for f in files], ["a.ts", "run.sh", "new.sh"])
        self.assertEqual(files[1]["mode"], {"old": "100644", "new": "100755"})
        self.assertEqual(files[1]["rows"], [])
        self.assertNotIn("mode", files[2])
        self.assertEqual(files[2]["status"], "added")

    def test_flow_into_file_model(self):
        from app.services import models
        f = diffmod.parse_diff(self.DIFF, [])[1]
        m = models.file_model(f, {}, {})
        self.assertEqual(m["mode"], {"old": "100644", "new": "100755"})
        self.assertNotIn("noeol", m)


class GeneratedAttrTests(unittest.TestCase):
    def test_check_attr_marks_generated_paths(self):
        with tempfile.TemporaryDirectory() as repo:
            sh(repo, "init", "-q", "-b", "main")
            Path(repo, ".gitattributes").write_text("out/*.ts linguist-generated\nkeep.ts linguist-generated=false\n")
            sh(repo, "add", "-A")
            sh(repo, "commit", "-qm", "base")
            sh(repo, "update-ref", "refs/review/pr-1", "HEAD")
            pr = {"number": 1, "source": {"clone": repo}}
            self.assertEqual(git.generated_paths(pr, ["out/a.ts", "keep.ts", "src/b.ts"]), {"out/a.ts"})

    def test_no_clone_or_failure_is_empty(self):
        self.assertEqual(git.generated_paths({"number": 1, "source": {}}, ["a"]), set())
        with mock.patch.object(git, "has_clone", return_value=True), mock.patch.object(git, "run", side_effect=OSError):
            self.assertEqual(git.generated_paths({"number": 1, "source": {"clone": "/x"}}, ["a"]), set())


if __name__ == "__main__":
    unittest.main()
