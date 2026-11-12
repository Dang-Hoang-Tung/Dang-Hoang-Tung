import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from app.ui.components import appbar  # noqa: E402
from test_ui import SHA, review_model  # noqa: E402


def bar(**pr):
    model = review_model()
    model["pr"].update(pr)
    return appbar.render(model["pr"], model["totals"], model["summary"]["minutes"])


class TopbarTests(unittest.TestCase):
    def test_second_line_has_author_link_sha_ci(self):
        html = bar()
        meta = html[html.index('<div class="meta">'):]
        meta = meta[:meta.index("</div>")]
        self.assertIn("alice", meta)
        self.assertIn('<a class="prlink" href="https://github.com/acme/widgets/pull/42"', meta)
        self.assertIn(">#42</a>", meta)
        self.assertIn(SHA[:7], meta)
        self.assertIn("CI passing", meta)

    def test_no_duplicates_in_chip_row(self):
        html = bar()
        self.assertEqual(html.count('class="ci ok"'), 1)
        self.assertEqual(html.count(SHA[:7]), 1)
        self.assertEqual(html.count('data-tip="Author: alice"'), 1)
        self.assertNotIn('class="chip hide-md', html)

    def test_ci_none_omitted(self):
        self.assertNotIn("CI none", bar(ci="none"))

    def test_title_on_line_one_without_native_title(self):
        html = bar()
        h1 = re.search(r"<h1[^>]*>", html).group(0)
        self.assertNotIn(" title=", h1)
        self.assertIn('aria-label="Make the button &lt;great&gt;"', h1)
        self.assertLess(html.index("<h1"), html.index('<div class="meta">'))

    def test_timer_before_navchip(self):
        html = bar()
        self.assertLess(html.index('id="timer"'), html.index('<div class="navchip"'))

    def test_pbar_inside_leftchip(self):
        html = bar()
        chip = html.index('id="leftchip"')
        prog = html.index('<b id="pbar"></b>')
        self.assertLess(chip, prog)
        self.assertEqual(html.count('id="pbar"'), 1)

    def test_ids_kept(self):
        html = bar()
        for i in ("navchip", "approvebtn", "approvepop", "morebtn", "focus", "palettebtn", "thememenu", "themebtn", "hidews"):
            self.assertIn(f'id="{i}"', html)


if __name__ == "__main__":
    unittest.main()
