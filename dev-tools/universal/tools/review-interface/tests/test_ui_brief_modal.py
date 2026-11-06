"""The Brief floating button and modal, and the PR description heading."""
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


def page_with(**summary):
    model = review_model()
    return review_page.render(review_model(summary=dict(model["summary"], **summary)))


class BriefModalTests(unittest.TestCase):
    def test_button_and_modal_exist(self):
        page = page_with(has_insights=True, verdict="Looks good", what="Adds a thing", risk="Low", minutes=5,
                         check=[{"severity": "should", "title": "check A", "path": "a.py", "line": 3}], questions=["why B?"])
        self.assertIn('id="briefbtn"', page)
        modal = page[page.index('id="briefmodal"'):]
        for needle in ("Verdict:", "What:", "Adds a thing", "Risk:", "Time:", "check A", "why B?", "Ask the author", "a.py:3"):
            self.assertIn(needle, modal, needle)

    def test_what_is_optional(self):
        modal = page_with(has_insights=True, verdict="Ok", risk="Low", minutes=3)
        self.assertNotIn("What:", modal)

    def test_no_insights(self):
        page = page_with(has_insights=False)
        self.assertIn("No brief yet.", page[page.index('id="briefmodal"'):])

    def test_rename(self):
        page = page_with(has_insights=False)
        self.assertIn("PR description", page)
        self.assertNotIn("About this PR", page)

    def test_fabs_stack_vertically(self):
        css = (ROOT / "app/ui/static/css/modals.css").read_text()
        self.assertRegex(css, r"\.fabs\{[^}]*flex-direction:column")

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_inline_scripts_parse(self):
        scripts = re.findall(r"<script>(.*?)</script>", page_with(has_insights=True), re.S)
        self.assertTrue(scripts)
        for i, code in enumerate(scripts):
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(code)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
