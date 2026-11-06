import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.ui.components import appbar  # noqa: E402
from app.ui.pages import review_page  # noqa: E402
from test_ui import review_model  # noqa: E402

VERDICT = "Approve with nits (two small cleanups). Merge after."


def page(verdict=VERDICT):
    model = review_model()
    model["summary"]["verdict"] = verdict
    return review_page.render(model)


class AppbarTests(unittest.TestCase):
    def test_short_verdict(self):
        self.assertEqual(appbar.short_verdict(VERDICT), "Approve with nits")
        self.assertEqual(appbar.short_verdict("Needs work - see notes"), "Needs work")
        self.assertEqual(appbar.short_verdict("Approve"), "Approve")

    def test_verdict_chip_and_title(self):
        html = page()
        self.assertIn(f'<span class="chip verdict" title="{VERDICT.replace("(", "(")}">Approve with nits</span>', html)

    def test_overflow_menu_holds_controls(self):
        html = page()
        start = html.index('id="overflowmenu"')
        end = html.index('</header>')
        menu = html[start:end]
        for needle in ('id="focus"', 'id="palettebtn"', 'id="thememenu"', 'id="themebtn"'):
            self.assertIn(needle, menu)
        self.assertIn('id="morebtn"', html[:start])

    def test_navchip(self):
        html = page()
        for needle in ('class="navchip" id="navchip"', 'id="navprev"', 'id="navcount"', 'id="navnext"'):
            self.assertIn(needle, html)

    def test_approve_markup_kept(self):
        html = page()
        for needle in ('id="approvebtn"', 'id="approvepop"', 'id="leftchip"'):
            self.assertIn(needle, html)


if __name__ == "__main__":
    unittest.main()
