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

from app.ui.components import appbar  # noqa: E402
from test_ui import review_model  # noqa: E402

JS = (ROOT / "app/ui/static/js/review/left-panel.js").read_text()
CSS = (ROOT / "app/ui/static/css/appbar.css").read_text()


def bar_html():
    model = review_model()
    return appbar.render(model["pr"], model["totals"], model["summary"]["minutes"])


class ProgressBarTests(unittest.TestCase):
    def test_markup(self):
        html = bar_html()
        for needle in ('id="leftchip"', 'class="ptrack"', 'id="pbar"', 'id="pfx"', 'class="left-files"', 'class="plines"'):
            self.assertIn(needle, html)

    def test_animates_only_on_increase(self):
        self.assertIn("n > prevDone", JS)
        self.assertIn("prefers-reduced-motion", JS)
        self.assertIn("prefers-reduced-motion", CSS)

    def test_title_tooltip_still_wired(self):
        self.assertIn('id="prtitle"', bar_html())

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_inline_scripts_parse(self):
        from app.ui.pages import review_page
        page = review_page.render(review_model()) if hasattr(review_page, "render") else ""
        scripts = re.findall(r"<script(?![^>]*\bsrc=)(?![^>]*application/json)[^>]*>(.*?)</script>", page, re.S)
        self.assertTrue(scripts)
        for src in scripts:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(src)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
