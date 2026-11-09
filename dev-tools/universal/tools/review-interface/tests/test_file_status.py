"""GitHub-style file status icons: added, deleted, renamed or modified."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services.diff import parse_diff  # noqa: E402
from app.ui.components import file_section  # noqa: E402

DIFF = """diff --git a/new.ts b/new.ts
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/new.ts
@@ -0,0 +1 @@
+a
diff --git a/gone.ts b/gone.ts
deleted file mode 100644
index 1111111..0000000
--- a/gone.ts
+++ /dev/null
@@ -1 +0,0 @@
-a
diff --git a/old/name.ts b/new/name.ts
similarity index 90%
rename from old/name.ts
rename to new/name.ts
index 1111111..2222222 100644
--- a/old/name.ts
+++ b/new/name.ts
@@ -1 +1 @@
-a
+b
diff --git a/same.ts b/same.ts
index 1111111..2222222 100644
--- a/same.ts
+++ b/same.ts
@@ -1 +1 @@
-a
+b
diff --git a/pure/move.ts b/other/move.ts
similarity index 100%
rename from pure/move.ts
rename to other/move.ts
"""


class FileStatusTests(unittest.TestCase):
    def test_statuses(self):
        files = {f["path"]: (f["status"], f["old_path"]) for f in parse_diff(DIFF, [])}
        self.assertEqual(files["new.ts"], ("added", None))
        self.assertEqual(files["gone.ts"], ("deleted", None))
        self.assertEqual(files["new/name.ts"], ("renamed", "old/name.ts"))
        self.assertEqual(files["same.ts"], ("modified", None))
        self.assertEqual(files["other/move.ts"], ("renamed", "pure/move.ts"))

    def test_header_icon_and_tooltip(self):
        f = {"idx": 0, "path": "new/name.ts", "kind": None, "gen": False, "a": 1, "d": 1, "rows": [],
             "status": "renamed", "old_path": "old/name.ts"}
        html = file_section.render(f, [])
        self.assertIn('class="fstat renamed"', html)
        self.assertIn('title="Renamed or moved from old/name.ts"', html)
        self.assertLess(html.index("fstatus"), html.index('class="path"'))

    def test_missing_status_shows_modified(self):
        f = {"idx": 0, "path": "a.ts", "kind": None, "gen": False, "a": 0, "d": 0, "rows": []}
        self.assertIn('class="fstat modified"', file_section.render(f, []))


if __name__ == "__main__":
    unittest.main()
