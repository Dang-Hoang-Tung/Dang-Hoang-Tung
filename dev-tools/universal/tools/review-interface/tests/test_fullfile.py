"""Show entire file: the whole file with the PR's changes marked."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.services import fullfile  # noqa: E402
from app.ui.components import file_section  # noqa: E402


def sh(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout.strip()


class FullFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        repo = self.repo = self.tmp.name
        sh(repo, "init", "-q", "-b", "main")
        sh(repo, "config", "user.email", "t@t"); sh(repo, "config", "user.name", "t")
        Path(repo, "a.py").write_text("".join(f"line {i}\n" for i in range(1, 61)))
        sh(repo, "add", "."); sh(repo, "commit", "-qm", "base")
        sh(repo, "update-ref", "refs/review/base-7", "HEAD")
        lines = [f"line {i}\n" for i in range(1, 61)]
        lines[29] = "changed 30\n"
        Path(repo, "a.py").write_text("".join(lines))
        sh(repo, "commit", "-qam", "pr")
        self.cfg = {"sources": [{"repo": "acme/w", "clone": repo}]}
        self.meta = {"repo": "acme/w", "pr": 7, "head_sha": sh(repo, "rev-parse", "HEAD")}

    def tearDown(self):
        self.tmp.cleanup()

    def test_whole_file_with_change_marked(self):
        rows = fullfile.rows(self.cfg, self.meta, "a.py")
        self.assertEqual(len([r for r in rows if r[0] == "ctx"]), 59)
        self.assertIn(("del", 30, None, "line 30"), rows)
        self.assertIn(("add", None, 30, "changed 30"), rows)
        self.assertEqual(rows[0], ("ctx", 1, 1, "line 1"))

    def test_render_uses_own_row_ids(self):
        out = fullfile.render(self.cfg, self.meta, "a.py", 3)
        self.assertIn('id="x3-0"', out["html"])
        self.assertNotIn('id="r3-', out["html"])
        self.assertEqual(out["lines"], 61)

    def test_no_clone(self):
        with self.assertRaises(fullfile.NoClone):
            fullfile.rows({"sources": [{"repo": "acme/w"}]}, self.meta, "a.py")

    def test_pathspec_magic_is_literal(self):
        self.assertEqual(fullfile.rows(self.cfg, self.meta, ":(glob)*"), [])

    def test_header_has_eye_button(self):
        f = {"idx": 2, "path": "src/a.py", "kind": None, "gen": False, "a": 1, "d": 1, "rows": []}
        html = file_section.render(f, [])
        self.assertIn('class="iconbtn sm fullbtn" data-full="2"', html)
        self.assertLess(html.index("fullbtn"), html.index('class="viewed"'))


class CommentsAndToggleTests(unittest.TestCase):
    def page(self):
        from app.ui.pages import review_page
        from test_ui import review_model
        return review_page.render(review_model())

    def test_comments_button_under_brief(self):
        html = self.page()
        self.assertLess(html.index('id="briefbtn"'), html.index('id="commentsbtn"'))
        self.assertLess(html.index('id="commentsbtn"'), html.index('id="treebtn"'))
        self.assertIn("<span>PR comments</span>", html)
        self.assertIn('id="commentsmodal"', html)

    def test_viewer_has_mode_toggle(self):
        html = self.page()
        self.assertIn('data-mode="preview"', html)
        self.assertIn('data-mode="full"', html)


if __name__ == "__main__":
    unittest.main()
