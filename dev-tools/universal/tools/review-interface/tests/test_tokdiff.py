"""Strong highlights: API shape, fallbacks, cross-file moves, per-language rules, and wiring into the page model."""
import unittest
from unittest import mock

import helpers
from app.services import diff as diffmod
from app.services import models, tokdiff


def rows(*lines):
    """Rows of one hunk from "-old", "+new" and " context" lines."""
    old = new = 1
    out = [("hunk", None, None, "@@")]
    for ln in lines:
        kind = {"-": "del", "+": "add", " ": "ctx"}[ln[0]]
        out.append((kind, old if kind != "add" else None, new if kind != "del" else None, ln[1:]))
        old += kind != "add"
        new += kind != "del"
    return out


def one(path, *lines):
    return tokdiff.strong_spans([{"path": path, "rows": rows(*lines)}])[0]


class SpanTests(unittest.TestCase):
    def test_only_the_changed_token_is_strong(self):
        spans, quiet = one("a.ts", "-const b = 2;", "+const b = 3;")
        self.assertEqual(spans, {1: [[10, 11]], 2: [[10, 11]]})
        self.assertEqual(quiet, set())

    def test_reindent_is_quiet(self):
        spans, quiet = one("a.ts", " if (x) {", "-  run();", "+    run();", " }")
        self.assertEqual((spans, quiet), ({}, {2, 3}))

    def test_added_braces_are_strong(self):
        spans, _ = one("a.ts", "-if (x) run();", "+if (x) {", "+  run();", "+}")
        self.assertIn(2, spans)
        self.assertEqual(spans[4], [[0, 1]])

    def test_kept_name_moved_into_a_new_object_is_strong(self):
        spans, _ = one("a.ts", " return {", "-  a: f(x),", "-  ownerId,", "+  a,", "+  owner: t ? { id: ownerId, kind: t } : null,", " };")
        self.assertIn(3, spans)

    def test_return_split_by_newline_is_strong(self):
        spans, _ = one("a.ts", "-  return f(a);", "+  return", "+    f(a);")
        self.assertEqual(spans[2], [[2, 8]])

    def test_python_indent_and_trailing_comma_are_strong(self):
        spans, quiet = one("a.py", " if x:", "-    run()", "+run()")
        self.assertEqual((sorted(spans), quiet), ([2, 3], set()))
        spans, _ = one("a.py", "-t = (1)", "+t = (1,)")
        self.assertIn(2, spans)

    def test_plain_text_marks_changed_words(self):
        spans, _ = one("notes.md", "-The quick fox", "+The slow fox")
        self.assertEqual(spans, {1: [[4, 9]], 2: [[4, 8]]})

    def test_huge_block_highlights_every_token(self):
        with mock.patch.object(tokdiff, "MAX_BLOCK_TOKENS", 4):
            spans, _ = one("a.ts", "-const b = 2;", "+const b = 3;")
        self.assertEqual(spans, {1: [[0, 12]], 2: [[0, 12]]})

    def test_slow_file_falls_back_to_whole_rows(self):
        with mock.patch.object(tokdiff, "FILE_SECONDS", -1):
            spans, quiet = one("a.ts", "-  const b = 2;", "+    const b = 2;", " x();")
        self.assertEqual((spans, quiet), ({1: [[2, 14]], 2: [[4, 16]]}, set()))


class MoveTests(unittest.TestCase):
    FN = ["export function pick(items: Item[]) {", "  return items.slice(0, 1);", "}"]

    def test_function_moved_to_another_file_is_quiet(self):
        files = [{"path": "a.ts", "rows": rows(*("-" + ln for ln in self.FN))},
                 {"path": "b.ts", "rows": rows(*("+" + ln for ln in self.FN))}]
        self.assertEqual(tokdiff.strong_spans(files), [({}, {1, 2, 3}), ({}, {1, 2, 3})])

    def test_statement_moved_out_of_its_if_is_strong(self):
        spans, _ = one("a.ts", " function f() {", " if (x) {", "-  audit.write(user.id);", " }",
                       "+audit.write(user.id);", " }")
        self.assertEqual(sorted(spans), [3, 5])

    def test_statements_swapped_in_one_scope_are_strong(self):
        spans, _ = one("a.ts", " async function f() {", "-  await save(order, now);", "   notify(order);",
                       "+  await save(order, now);", " }")
        self.assertEqual(sorted(spans), [2, 4])


class ModelTests(unittest.TestCase):
    def test_review_model_fills_spans_and_skips_generated_files(self):
        files = diffmod.parse_diff(helpers.DIFF, [r"/generated/"])
        cfg = {"generated": [r"/generated/"], "ai_name": "AI"}
        with mock.patch.object(models.git, "generated_paths", return_value=set()):
            m = models.review_model(cfg, helpers.make_pr(), helpers.DIFF, None, "none", "me")
        widget, util, gen = m["files"]
        self.assertEqual(widget["spans"], {2: [[12, 13]], 3: [[12, 13]], 4: [[2, 14]]})
        self.assertEqual(util["quiet"], [])
        self.assertEqual((gen["spans"], gen["quiet"]), ({}, []))
        self.assertEqual(len(files), 3)


if __name__ == "__main__":
    unittest.main()
