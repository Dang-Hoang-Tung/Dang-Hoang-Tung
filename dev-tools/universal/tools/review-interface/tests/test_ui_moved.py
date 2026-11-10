import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.ui.pages import review_page  # noqa: E402
from test_ui import review_model  # noqa: E402


def moved_model():
    model = review_model()
    model["files"][0]["moved"] = {
        "2": {"dir": "to", "file": 1, "row": 1, "path": "src/components/Button.test.tsx", "line": 1, "start": True},
        "3": {"dir": "from", "file": 1, "row": 1, "path": "src/other/Old.tsx", "line": 9, "start": True},
        "4": {"dir": "from", "file": 1, "row": 1, "path": "src/other/Old.tsx", "line": 10, "start": False},
        "5": {"dir": "to", "file": None, "row": None, "path": None, "line": None, "start": True},
    }
    return model


class MovedTests(unittest.TestCase):
    def test_moved_classes_and_label(self):
        html = review_page.render(moved_model())
        self.assertRegex(html, r'<tr id="r0-2"[^>]*class="del moved moved-to')
        self.assertRegex(html, r'<tr id="r0-3"[^>]*class="add moved moved-from')
        self.assertIn('>moved to Button.test.tsx L1</button>', html)
        self.assertIn('>moved from Old.tsx L9</button>', html)
        self.assertNotIn("L10</button>", html)
        self.assertRegex(html, r'<tr id="r0-5"[^>]*class="ctx moved moved-to')
        self.assertIn('<span class="mvlabel plain">moved</span>', html)

    def test_same_file_move_names_only_the_line(self):
        model = review_model()
        model["files"][0]["moved"] = {"2": {"dir": "to", "file": 0, "row": 4, "path": model["files"][0]["path"], "line": 7, "start": True}}
        html = review_page.render(model)
        self.assertIn('>moved to L7</button>', html)

    def test_missing_moved_key_is_fine(self):
        html = review_page.render(review_model())
        self.assertNotIn('class="del moved', html)
        self.assertNotIn("<button type=\"button\" class=\"mvlabel", html)

    def test_hidews_in_overflow_menu(self):
        html = review_page.render(review_model())
        menu = html[html.index('id="overflowmenu"'):html.index('</header>')]
        self.assertIn('id="hidews"', menu)

    def test_inline_scripts_parse(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not available")
        html = review_page.render(moved_model())
        scripts = re.findall(r"<script(?![^>]*(?:src=|json))[^>]*>(.*?)</script>", html, re.S)
        self.assertTrue(scripts)
        for n, body in enumerate(scripts):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"s{n}.js"
                path.write_text(body)
                r = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
