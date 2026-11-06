"""Left-to-right code tree: directory ordering and x growing with depth."""
import unittest

import helpers  # noqa: F401
from helpers import tree_stats
from app.services import tree
from app.ui.components import tree_svg

PATHS = ["zeta/b.ts", "Alpha/z.ts", "alpha2/a.ts", "README.md", "apple.md", "Zebra.md", "zeta/A.ts"]


def names(node):
    return [k["name"] for k in node["kids"]]


class TreeLtrTests(unittest.TestCase):
    def setUp(self):
        self.t = tree.build_tree(PATHS, "repo")
        self.lay = tree.layout(self.t, tree_stats(PATHS))

    def test_folders_first_then_files_case_insensitive(self):
        self.assertEqual(names(self.t), ["Alpha", "alpha2", "zeta", "apple.md", "README.md", "Zebra.md"])
        self.assertEqual(names(self.t["kids"][2]), ["A.ts", "b.ts"])

    def test_x_increases_with_depth(self):
        by_title = {n["title"]: n for n in self.lay["nodes"]}
        root, zeta, leaf = by_title["repo"], by_title["zeta"], by_title["zeta/A.ts"]
        self.assertEqual(root["x"], 0)
        self.assertGreater(zeta["x"], root["x"] + root["w"] - 0.001)
        self.assertGreater(leaf["x"], zeta["x"] + zeta["w"] - 0.001)

    def test_first_child_shares_row_and_rows_follow_order(self):
        nodes = self.lay["nodes"]
        self.assertEqual(nodes[0]["y"], nodes[1]["y"])
        ys = [n["y"] for n in nodes]
        self.assertEqual(ys, sorted(ys))

    def test_svg_size_and_links(self):
        html = tree_svg.render(self.lay)
        self.assertIn(f'viewBox="-2 -2 {tree_svg._n(self.lay["width"] + 4)} {tree_svg._n(self.lay["height"] + 4)}"', html)
        self.assertEqual(html.count('class="tlink" data-file='), len(PATHS))


if __name__ == "__main__":
    unittest.main()
