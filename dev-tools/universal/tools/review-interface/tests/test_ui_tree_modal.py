"""The code tree sits under the description and moves into its modal; the floating button is always shown."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT  # noqa: E402,F401
from test_ui import review_model  # noqa: E402
from app.ui.pages import review_page  # noqa: E402


class TreeModalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = review_page.render(review_model())

    def test_no_tree_card(self):
        for needle in ("treecard", "treetoggle", "Where this change lands</h2><div class=\"zoom\">"):
            self.assertNotIn(needle, self.page)
        self.assertEqual(self.page.count('id="treecanvas"'), 1)

    def test_fab_always_present(self):
        fab = re.search(r'<button[^>]*id="treebtn"[^>]*>', self.page).group(0)
        self.assertNotIn("hidden", fab)

    def test_tree_block_under_description_holds_the_one_canvas(self):
        start = self.page.index('id="treeblock"')
        block = self.page[start:self.page.index("</section>", start)]
        self.assertIn('id="treecanvas"', block)
        self.assertIn("<svg", block)
        self.assertIn('id="treeexpand"', block)
        self.assertIn("Generated", block)
        self.assertEqual(self.page.count('id="treecanvas"'), 1)
        self.assertLess(self.page.index('class="summary"'), start)

    def test_modal_has_zoom_and_an_empty_body_for_the_canvas(self):
        modal = self.page[self.page.index('id="treemodal"'):self.page.index('id="mapmodal"')]
        self.assertIn('<div class="modal-body" id="treemodalbody"></div>', modal)
        for z in ("out", "fit", "in"):
            self.assertIn(f'data-zoom="{z}"', modal)
        self.assertIn("Generated", modal)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_inline_scripts_parse(self):
        scripts = re.findall(r"<script>(.*?)</script>", self.page, re.S)
        self.assertTrue(scripts)
        for body in scripts:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(body)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            Path(f.name).unlink()
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
