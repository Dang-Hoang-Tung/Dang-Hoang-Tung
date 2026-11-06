"""The chat bar, its box, and the script/CSS wiring."""
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


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.page = review_page.render(review_model())

    def test_bar_and_box_render(self):
        for part in ('id="chatbar"', 'id="chatbox"', 'id="chatinput"', 'id="chatsend"', 'id="chattoggle"', 'id="chatwait"'):
            self.assertIn(part, self.page)

    def test_chat_script_and_css_included(self):
        self.assertIn("function sendChat", self.page)
        self.assertIn("--chatbar", self.page)

    def test_fabs_sit_above_bar(self):
        css = (ROOT / "app/ui/static/css/chat.css").read_text()
        self.assertRegex(css, r"\.fabs\{bottom:calc\(var\(--chatbar\)")
        self.assertRegex(css, r"body\{padding-bottom:var\(--chatbar\)")

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_inline_scripts_parse(self):
        scripts = re.findall(r"<script>(.*?)</script>", self.page, re.S)
        self.assertTrue(scripts)
        for code in scripts:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(code)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
