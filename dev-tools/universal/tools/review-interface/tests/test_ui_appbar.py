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
    def test_timer_replaces_verdict(self):
        html = page()
        self.assertNotIn('chip verdict', html)
        self.assertIn('id="timer"', html)
        self.assertIn('data-default="720"', html)
        self.assertIn('<span id="timerval">12:00</span>', html)

    def test_timer_defaults_to_ten_minutes(self):
        self.assertIn('data-default="600"', appbar.timer_chip(None))

    def test_timeup_popup_options(self):
        html = page()
        for label, mins in (("Just a minute!", 1), ("Give me 5 more mins", 5), ("I need a solid 10 mins", 10)):
            self.assertIn(f'<button type="button" data-add="{mins}">{label}</button>', html)
        self.assertIn('id="timeupclose"', html)
        self.assertIn("used all the time you allocated", html)

    def test_brief_button_label(self):
        self.assertIn("<span>AI Brief</span>", page())

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
