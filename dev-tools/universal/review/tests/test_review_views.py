import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import code_tree  # noqa: E402
import pr_files  # noqa: E402
import treemap  # noqa: E402


def change(url="https://github.com/acme/widgets/pull/7"):
    files = [pr_files._file(p, a, d, s, pr_files.GENERATED) for p, a, d, s in (
        ("src/app/core.py", 40, 10, "modified"),
        ("src/app/util.py", 5, 0, "added"),
        ("tests/test_core.py", 20, 2, "modified"),
        ("package-lock.json", 900, 300, "modified"),
    )]
    return {"title": "#7 Add widget", "url": url, "root": "widgets", "files": files}


class PrFilesTests(unittest.TestCase):
    def test_numstat_with_a_rename_and_a_binary(self):
        numstat = "3\t1\tsrc/a.py\0" "0\t0\t\0old/b.py\0new/b.py\0" "-\t-\tlogo.png\0"
        names = "M\0src/a.py\0R100\0old/b.py\0new/b.py\0A\0logo.png\0"
        self.assertEqual(pr_files.parse_numstat(numstat, names), [
            ("src/a.py", 3, 1, "modified"), ("new/b.py", 0, 0, "renamed"), ("logo.png", 0, 0, "added")])

    def test_notes_match_by_path_or_unique_file_name(self):
        c = change()
        left = pr_files.add_notes(c, {"recommendations": [
            {"path": "src/app/core.py", "severity": "should", "title": "a"},
            {"path": "util.py", "severity": "nit", "title": "b"},
            {"path": "nowhere.py", "severity": "nit", "title": "c"},
        ]})
        self.assertEqual([n["title"] for n in left], ["c"])
        self.assertEqual(c["files"][0]["notes"][0]["severity"], "should")
        self.assertEqual(c["files"][1]["notes"][0]["severity"], "nit")

    def test_lockfiles_count_as_generated(self):
        self.assertEqual([f["gen"] for f in change()["files"]], [False, False, False, True])

    def test_pr_refs(self):
        for ref in ("acme/widgets#7", "https://github.com/acme/widgets/pull/7", "https://github.com/acme/widgets/pull/7/"):
            self.assertIsNotNone(pr_files.PR_REF.fullmatch(ref.rstrip("/")), ref)
        self.assertIsNone(pr_files.PR_REF.fullmatch("main...HEAD"))


class CodeTreeTests(unittest.TestCase):
    def test_collapse_merges_single_child_folders(self):
        tree = code_tree.build_tree(["src/app/core.py", "src/app/util.py"], "widgets")
        self.assertEqual([k["name"] for k in tree["kids"]], ["src/app"])
        full = code_tree.build_tree(["src/app/core.py"], "widgets", collapse=False)
        self.assertEqual(full["kids"][0]["name"], "src")

    def test_page_has_both_trees_links_and_note_colours(self):
        c = change()
        pr_files.add_notes(c, [{"path": "core.py", "severity": "should", "title": "Check this"}])
        html = code_tree.render(c)
        self.assertEqual(html.count('<svg class="tree"'), 2)
        self.assertIn('class="node file should"', html)
        self.assertIn("/pull/7/files#diff-", html)
        self.assertIn("Should fix: Check this", html)

    def test_local_range_has_no_links(self):
        self.assertNotIn('class="tlink"', code_tree.render(change(url=None)))


class TreemapTests(unittest.TestCase):
    def test_boxes_fill_the_map(self):
        rs = treemap.boxes(change()["files"])
        self.assertEqual(len(rs), 4)
        self.assertAlmostEqual(sum(r["w"] * r["h"] for r in rs), treemap.W * treemap.H, places=3)

    def test_generated_file_is_capped_at_the_biggest_real_file(self):
        rs = {r["f"]["path"]: r["v"] for r in treemap.boxes(change()["files"])}
        self.assertEqual(rs["package-lock.json"], rs["src/app/core.py"])

    def test_page_renders_cells(self):
        html = treemap.render(change())
        self.assertEqual(html.count('class="tm '), 4)
        self.assertIn('class="tm gen"', html)


if __name__ == "__main__":
    unittest.main()
