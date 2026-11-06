"""Internal vs synced threads: script/CSS wiring and the sync call."""
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


class SyncedThreadTests(unittest.TestCase):
    def setUp(self):
        self.page = review_page.render(review_model())

    def test_badge_css_exists(self):
        css = (ROOT / "app/ui/static/css/threads.css").read_text()
        self.assertIn(".thread-head .pill", css)
        self.assertIn(".pill.outdated", css)
        self.assertIn(".msg.gh", css)

    def test_wiring_in_page(self):
        for part in ("function syncGithub", "/api/sync/", "function syncPills", "Reply on GitHub", "synced: true"):
            self.assertIn(part, self.page)

    def test_waiting_ignores_synced(self):
        self.assertRegex(self.page, r"waitingThreads = \(\) => state\.threads\.filter\(t => !isSynced\(t\)")

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_inline_scripts_parse(self):
        scripts = re.findall(r"<script>(.*?)</script>", self.page, re.S)
        self.assertTrue(scripts)
        for code in scripts:
            with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                f.write(code)
            r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_is_synced_helper(self):
        src = (ROOT / "app/ui/static/js/review/threads.js").read_text()
        line = next(l for l in src.splitlines() if l.startswith("const isSynced"))
        r = subprocess.run(["node", "-e", line + "; console.log(JSON.stringify([isSynced({synced:true}), isSynced({id:'gh-5'}), isSynced({id:'a'})]))"], capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "[true,true,false]")


if __name__ == "__main__":
    unittest.main()
