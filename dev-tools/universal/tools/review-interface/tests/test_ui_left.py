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

from app.ui.components import left_panel  # noqa: E402
from test_ui import review_model  # noqa: E402
from app.ui.pages import review_page  # noqa: E402

CSS = (ROOT / "app/ui/static/css/left-panel.css").read_text()
JS = (ROOT / "app/ui/static/js/review/left-panel.js").read_text()


def rule(selector):
    return [m for m in re.findall(r"([^{}]+)\{([^}]*)\}", CSS) if selector in m[0]]


class LeftPanelMarkupTests(unittest.TestCase):
    def test_no_where_you_are_section(self):
        html = left_panel.render()
        for gone in ("pgrid", "pcount", "Where you are", "progress"):
            self.assertNotIn(gone, html)

    def test_page_renders_panel_without_progress(self):
        page = review_page.render(review_model())
        self.assertIn('class="left"', page)
        for gone in ("pgrid", "pcount", "Where you are"):
            self.assertNotIn(gone, page)


class LeftPanelStyleTests(unittest.TestCase):
    def test_no_progress_styles(self):
        for gone in ("#pcount", ".grid", ".progress", ".pbar"):
            self.assertNotIn(gone, CSS)

    def test_no_strikethrough(self):
        self.assertNotIn("line-through", CSS)

    def test_hover_reveal(self):
        self.assertTrue(any("opacity:0" in b for _, b in rule(".tcount")))
        self.assertIn(".trow:focus-within .tcount", CSS)
        self.assertIn(".lhead:focus-within .lcount", CSS)
        self.assertIn(".trow:focus-within .lead>input.rd", CSS)
        self.assertNotIn("display:none", "".join(b for s, b in rule(".lead>input.rd")))

    def test_viewed_mark_is_muted_green(self):
        body = "".join(b for s, b in rule(".vmark"))
        self.assertIn("var(--add)", body)
        self.assertIn("opacity:.55", body)


class LeftPanelScriptTests(unittest.TestCase):
    def test_ring_only_with_notes(self):
        self.assertIn("if (D.files[i].kind) row.append(el('span', 'ring ' + ringOf(i)))", JS)
        self.assertNotIn("row.append(lead, el('span', 'ring", JS)

    def test_viewed_mark_and_checkbox_kept_in_dom(self):
        self.assertIn("el('span', 'vmark', '✓')", JS)
        self.assertIn("'Mark as viewed'", JS)
        self.assertIn("'Mark folder as viewed'", JS)
        self.assertIn("'Mark layer as viewed'", JS)

    def test_progress_targets_pbar_only(self):
        self.assertIn("const bar = $('#pbar');", JS); self.assertIn("bar.style.width", JS)
        self.assertNotIn("pgrid", JS)
        self.assertNotIn("pcount", JS)

    def test_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("node not available")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "left-panel.js"
            path.write_text(JS)
            r = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
