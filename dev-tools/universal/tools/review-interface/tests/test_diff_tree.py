"""Diff parsing and tree layout."""
import copy
import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401
from app import config
from app.services import diff as diffmod
from app.services import tree

from helpers import *  # noqa: F401,F403


class ParseDiffTests(unittest.TestCase):
    def setUp(self):
        self.files = diffmod.parse_diff(DIFF, config.DEFAULTS["generated"])

    def test_files_and_counts(self):
        self.assertEqual([f["path"] for f in self.files], ["src/app/Widget.tsx", "src/lib/util.ts", "src/generated/api.ts"])
        self.assertEqual([(f["a"], f["d"]) for f in self.files], [(2, 1), (1, 1), (1, 1)])
        self.assertEqual([f["idx"] for f in self.files], [0, 1, 2])

    def test_generated_flag(self):
        self.assertEqual([f["gen"] for f in self.files], [False, False, True])

    def test_row_kinds_and_line_numbers(self):
        rows = self.files[0]["rows"]
        self.assertEqual(rows[0][0], "hunk")
        self.assertEqual(rows[1], ("ctx", 10, 10, "  const a = 1;"))
        self.assertEqual(rows[2], ("del", 11, None, "  const b = 2;"))
        self.assertEqual(rows[3], ("add", None, 11, "  const b = 3;"))
        self.assertEqual(rows[4], ("add", None, 12, "  const c = 4;"))
        self.assertEqual(rows[5], ("ctx", 12, 13, "  return a;"))

    def test_no_phantom_trailing_row(self):
        for f in self.files:
            self.assertNotEqual(f["rows"][-1][3], "")
        self.assertEqual(self.files[1]["rows"][-1][3], "export const z = 3;")
        self.assertEqual(len(self.files[0]["rows"]), 7)

    def test_blank_context_line_kept(self):
        d = "diff --git a/a.ts b/a.ts\n@@ -1,3 +1,3 @@\n x\n \n-y\n+z\n"
        rows = diffmod.parse_diff(d, [])[0]["rows"]
        self.assertEqual([r[0] for r in rows], ["hunk", "ctx", "ctx", "del", "add"])
        self.assertEqual(rows[2][3], "")

    def test_no_newline_marker_ignored(self):
        d = DIFF.replace("+  const c = 4;\n", "+  const c = 4;\n\\ No newline at end of file\n")
        rows = diffmod.parse_diff(d, [])[0]["rows"]
        self.assertFalse(any(r[3].startswith("No newline") or r[3].startswith("\\") for r in rows))

    def test_empty_diff(self):
        self.assertEqual(diffmod.parse_diff("", []), [])

    def test_layer_of(self):
        layer = lambda path, gen=False: diffmod.layer_of({"path": path, "gen": gen})
        self.assertEqual(layer("a/b.tsx"), "UI")
        self.assertEqual(layer("a/useThing.ts"), "Hooks")
        self.assertEqual(layer("a/b.test.ts"), "Tests")
        self.assertEqual(layer("a/b/api/x.ts"), "API")
        self.assertEqual(layer("a/db/x.ts"), "Data")
        self.assertEqual(layer("a/i18n/en.json"), "Copy")
        self.assertEqual(layer("a/x.yaml"), "Config")
        self.assertEqual(layer("a/x.ts", gen=True), "Generated")
        self.assertEqual(layer("README.md"), "Other")

    def test_file_hash_changes_with_content(self):
        a, b = self.files[0]["rows"], self.files[1]["rows"]
        self.assertEqual(diffmod.file_hash(a), diffmod.file_hash(list(a)))
        self.assertNotEqual(diffmod.file_hash(a), diffmod.file_hash(b))


class TreeTests(unittest.TestCase):
    PATHS = ["src/app/Widget.tsx", "src/app/Other.tsx", "src/lib/util.ts", "README.md"]

    def test_build_tree_compresses_single_child_dirs(self):
        t = tree.build_tree(["a/b/c/x.ts", "a/b/c/y.ts"], "repo")
        self.assertEqual([k["name"] for k in t["kids"]], ["a/b/c"])
        self.assertEqual([k["name"] for k in t["kids"][0]["kids"]], ["x.ts", "y.ts"])

    def test_build_tree_dirs_before_files_sorted(self):
        t = tree.build_tree(self.PATHS, "repo")
        self.assertEqual([k["name"] for k in t["kids"]], ["src", "README.md"])
        self.assertEqual([k["name"] for k in t["kids"][0]["kids"]], ["app", "lib"])

    def test_layout_geometry(self):
        t = tree.build_tree(self.PATHS, "repo")
        lay = tree.layout(t, tree_stats(self.PATHS))
        roles = [n["role"] for n in lay["nodes"]]
        self.assertEqual(roles[0], "root")
        self.assertEqual(roles.count("leaf"), 4)
        self.assertTrue(all(n["h"] == tree.NODE_H for n in lay["nodes"]))
        self.assertEqual(lay["nodes"][0]["y"], 0)
        self.assertEqual(lay["nodes"][0]["a"], 4)
        self.assertEqual(lay["nodes"][0]["d"], 8)
        self.assertEqual(lay["height"], max(n["y"] + n["h"] for n in lay["nodes"]))
        self.assertGreater(lay["width"], 0)
        for n in lay["nodes"]:
            self.assertAlmostEqual(n["x"], n["cx"] - n["w"] / 2)
            self.assertLessEqual(n["x"] + n["w"], lay["width"] + 0.001)

    def test_layout_leaves_map_to_file_idx_and_dirs_do_not(self):
        t = tree.build_tree(self.PATHS, "repo")
        lay = tree.layout(t, tree_stats(self.PATHS))
        leaves = {n["title"]: n["file"] for n in lay["nodes"] if n["role"] == "leaf"}
        self.assertEqual(leaves, {p: i for i, p in enumerate(self.PATHS)})
        self.assertTrue(all(n["file"] is None for n in lay["nodes"] if n["role"] != "leaf"))

    def test_layout_edges_are_path_strings(self):
        t = tree.build_tree(self.PATHS, "repo")
        lay = tree.layout(t, tree_stats(self.PATHS))
        self.assertTrue(lay["edges"])
        for e in lay["edges"]:
            self.assertRegex(e, r"^M-?[\d.]+,-?[\d.]+ [VH]-?[\d.]+$")

    def test_layout_stacks_leaves_vertically(self):
        t = tree.build_tree(["a/x.ts", "a/y.ts", "a/z.ts"], "repo")
        lay = tree.layout(t, tree_stats(["a/x.ts", "a/y.ts", "a/z.ts"]))
        leaves = [n for n in lay["nodes"] if n["role"] == "leaf"]
        ys = [n["y"] for n in leaves]
        self.assertEqual(ys, sorted(ys))
        self.assertEqual(ys[1] - ys[0], tree.NODE_H + tree.STACK_GAP)
        self.assertEqual(len({round(n["x"] - n["w"] * 0, 3) for n in leaves}), 1)

    def test_layout_kind_notes_and_gen(self):
        paths = ["a/x.ts", "a/gen.ts"]
        notes = {"a/x.ts": [{"kind": "nit"}, {"kind": "block"}]}
        lay = tree.layout(tree.build_tree(paths, "repo"), tree_stats(paths, notes))
        by = {n["title"]: n for n in lay["nodes"]}
        self.assertEqual((by["a/x.ts"]["kind"], by["a/x.ts"]["notes"]), ("block", 2))
        self.assertTrue(by["a/gen.ts"]["gen"])
        self.assertEqual(by["repo"]["notes"], 2)
        self.assertEqual(by["repo"]["kind"], "block")

    def test_long_labels_are_shortened(self):
        name = "x" * 60 + ".ts"
        lay = tree.layout(tree.build_tree([name], "repo"), tree_stats([name]))
        leaf = next(n for n in lay["nodes"] if n["role"] == "leaf")
        self.assertEqual(len(leaf["label"]), 44)
        self.assertEqual(leaf["title"], name)

    def test_layout_does_not_mutate_tree(self):
        t = tree.build_tree(self.PATHS, "repo")
        before = json.dumps(t)
        tree.layout(t, tree_stats(self.PATHS))
        self.assertEqual(json.dumps(t), before)


# ---------------------------------------------------------------- models


class ParseDiffPathTests(unittest.TestCase):
    def test_spaces_unicode_binary_and_deletes(self):
        d = ("diff --git a/my file.txt b/my file.txt\n--- a/my file.txt\t\n+++ b/my file.txt\t\n@@ -1 +1 @@\n-a\n+b\n"
             'diff --git "a/caf\\303\\251.txt" "b/caf\\303\\251.txt"\n--- "a/caf\\303\\251.txt"\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n'
             "diff --git a/img.png b/img.png\nBinary files a/img.png and b/img.png differ\n"
             "diff --git a/old.ts b/new name.ts\nsimilarity index 100%\nrename from old.ts\nrename to new name.ts\n")
        files = diffmod.parse_diff(d, [])
        self.assertEqual([f["path"] for f in files], ["my file.txt", "caf\u00e9.txt", "img.png", "new name.ts"])
        self.assertEqual([f["binary"] for f in files], [False, False, True, False])
        self.assertEqual(files[2]["rows"], [])
        self.assertEqual((files[0]["a"], files[0]["d"], files[1]["d"]), (1, 1, 1))

    def test_layers_come_from_domain(self):
        from app.domain import LAYERS
        self.assertEqual(diffmod.layer_of({"path": "x", "gen": True}), LAYERS[-1])


if __name__ == "__main__":
    unittest.main()

