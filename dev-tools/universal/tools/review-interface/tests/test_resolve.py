"""Import links in the 1-file viewer: finding the file an import points at, and reading untouched files."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services import resolve  # noqa: E402
from app.ui.components import file_section  # noqa: E402


def sh(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout.strip()


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.repo = self.tmp.name
        files = {
            "apps/web/src/page.ts": "import { a } from './util'\n",
            "apps/web/src/util.ts": "export const a = 1\n",
            "apps/web/src/dir/index.tsx": "export default 1\n",
            "packages/ui/package.json": json.dumps({"name": "@acme/ui"}),
            "packages/ui/src/button.ts": "export const b = 1\n",
            "packages/ui/src/index.ts": "export * from './button'\n",
            "packages/shared/form/schema.ts": "export const s = 1\n",
            "node_modules/x/index.js": "",
        }
        for p, body in files.items():
            Path(r, p).parent.mkdir(parents=True, exist_ok=True)
            Path(r, p).write_text(body)
        sh(r, "init", "-q", "-b", "main"); sh(r, "config", "user.email", "t@t"); sh(r, "config", "user.name", "t")
        sh(r, "add", "-f", "."); sh(r, "commit", "-qm", "x")
        self.sha = sh(r, "rev-parse", "HEAD")
        resolve._trees.clear()

    def tearDown(self):
        self.tmp.cleanup()

    def res(self, spec, frm="apps/web/src/page.ts"):
        return resolve.resolve(self.repo, self.sha, frm, spec)

    def test_relative(self):
        self.assertEqual(self.res("./util"), "apps/web/src/util.ts")
        self.assertEqual(self.res("./util.js"), "apps/web/src/util.ts")
        self.assertEqual(self.res("./dir"), "apps/web/src/dir/index.tsx")
        self.assertIsNone(self.res("./missing"))

    def test_workspace_package(self):
        self.assertEqual(self.res("@acme/ui"), "packages/ui/src/index.ts")
        self.assertEqual(self.res("@acme/ui/button"), "packages/ui/src/button.ts")

    def test_alias_by_path_suffix(self):
        self.assertEqual(self.res("@acme/packages/shared/form/schema"), "packages/shared/form/schema.ts")

    def test_outside_packages_not_found(self):
        self.assertIsNone(self.res("react"))
        self.assertIsNone(self.res("x"))

    def test_read_untouched_file(self):
        self.assertIn("export const s", resolve.read(self.repo, self.sha, "packages/shared/form/schema.ts"))
        with self.assertRaises(resolve.NotFound):
            resolve.read(self.repo, self.sha, "nope.ts")

    def test_blob_rows_cannot_be_selected(self):
        html, n = file_section.blob_table("a\nb\n")
        self.assertEqual(n, 2)
        self.assertNotIn("data-f=", html)
        self.assertIn('id="b-0"', html)


if __name__ == "__main__":
    unittest.main()
