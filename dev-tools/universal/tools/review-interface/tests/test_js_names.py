"""The review page's scripts share one scope, so a top-level name declared twice silently replaces the first."""
import re
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.ui.pages import review_page  # noqa: E402

DECL = re.compile(r"^(?:async\s+)?(?:function\s*\*?\s*|const\s+|let\s+|var\s+|class\s+)([A-Za-z_$][\w$]*)", re.M)


class JsNameTests(unittest.TestCase):
    def test_no_duplicate_top_level_names(self):
        js = ROOT / "app" / "ui" / "static" / "js"
        names = Counter(n for f in review_page.JS for n in DECL.findall((js / f).read_text()))
        self.assertEqual([n for n, c in names.items() if c > 1], [])


if __name__ == "__main__":
    unittest.main()
