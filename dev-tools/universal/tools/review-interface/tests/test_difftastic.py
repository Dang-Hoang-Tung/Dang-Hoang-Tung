"""Inline highlights from difftastic."""
import shutil
import unittest
from unittest import mock

import helpers  # noqa: F401
from app.services import build as builder
from app.services import diff as diffmod
from app.services import git

OLD = 'const a = "héllo wörld"; let x = 1;\nfoo(1);\nconst z = 3;\n'
NEW = 'const a = "héllo wörld!"; let y = 1;\nfoo(1, 2);\nconst z = 3;\nconst w = 4;\n'

ROWS = [
    ("hunk", None, None, "@@ -1,3 +1,4 @@"),
    ("del", 1, None, 'const a = "héllo wörld"; let x = 1;'),
    ("del", 2, None, "foo(1);"),
    ("add", None, 1, 'const a = "héllo wörld!"; let y = 1;'),
    ("add", None, 2, "foo(1, 2);"),
    ("ctx", 3, 3, "const z = 3;"),
    ("add", None, 4, "const w = 4;"),
]

RECORDED = {
    "language": "TypeScript",
    "chunks": [[
        {"rhs": {"line_number": 3, "changes": [{"start": 0, "end": 5}, {"start": 6, "end": 7}, {"start": 8, "end": 9}, {"start": 10, "end": 11}, {"start": 11, "end": 12}]}},
        {"lhs": {"line_number": 0, "changes": [{"start": 10, "end": 11}, {"start": 11, "end": 17}, {"start": 17, "end": 18}, {"start": 18, "end": 24}, {"start": 24, "end": 25}, {"start": 31, "end": 32}]},
         "rhs": {"line_number": 0, "changes": [{"start": 10, "end": 11}, {"start": 11, "end": 17}, {"start": 17, "end": 18}, {"start": 18, "end": 24}, {"start": 24, "end": 25}, {"start": 25, "end": 26}, {"start": 32, "end": 33}]}},
        {"lhs": {"line_number": 1, "changes": []}, "rhs": {"line_number": 1, "changes": [{"start": 5, "end": 6}, {"start": 7, "end": 8}]}},
    ]],
}


class MappingTests(unittest.TestCase):
    def test_columns_are_bytes_converted_to_characters(self):
        spans = diffmod.difft_spans(ROWS, RECORDED)
        self.assertEqual(spans[1], [[10, 23], [29, 30]])
        self.assertEqual(spans[3], [[10, 24], [30, 31]])
        self.assertEqual(spans[4], [[5, 6], [7, 8]])

    def test_del_rows_use_lhs_and_add_rows_use_rhs(self):
        spans = diffmod.difft_spans(ROWS, RECORDED)
        self.assertNotIn(2, spans)
        self.assertEqual(sorted(spans), [1, 3, 4])

    def test_fully_new_lines_and_context_get_no_spans(self):
        spans = diffmod.difft_spans(ROWS, RECORDED)
        self.assertNotIn(6, spans)
        self.assertNotIn(5, spans)

    def test_text_fallback_returns_none(self):
        self.assertIsNone(diffmod.difft_spans(ROWS, {"language": "Text (1 TypeScript parse error)", "chunks": []}))


class FallbackTests(unittest.TestCase):
    def model(self):
        return {"files": [{"path": "a.ts", "binary": False, "rows": ROWS, "spans": {}, "moved": {"3": {}}}]}

    def pr(self):
        return {"number": 1, "source": {"clone": "/x"}}

    def test_no_difft_keeps_browser_spans(self):
        m = self.model()
        with mock.patch.object(git, "has_clone", return_value=True), mock.patch("shutil.which", return_value=None), \
                mock.patch.object(git, "merge_base") as mb:
            builder.refine_spans(self.pr(), m)
        mb.assert_not_called()
        self.assertEqual(m["files"][0]["spans"], {})

    def test_no_clone_keeps_browser_spans(self):
        m = self.model()
        with mock.patch.object(git, "has_clone", return_value=False), mock.patch("shutil.which", return_value="/bin/difft"):
            builder.refine_spans(self.pr(), m)
        self.assertEqual(m["files"][0]["spans"], {})

    def test_difft_failure_keeps_browser_spans(self):
        m = self.model()
        with mock.patch.object(git, "has_clone", return_value=True), mock.patch("shutil.which", return_value="/bin/difft"), \
                mock.patch.object(git, "merge_base", return_value="abc"), mock.patch.object(git, "file_pair", return_value=(OLD, NEW)), \
                mock.patch.object(diffmod, "run_difft", return_value=None):
            builder.refine_spans(self.pr(), m)
        self.assertEqual(m["files"][0]["spans"], {})

    def test_difft_result_fills_spans_but_skips_moved_rows(self):
        m = self.model()
        with mock.patch.object(git, "has_clone", return_value=True), mock.patch("shutil.which", return_value="/bin/difft"), \
                mock.patch.object(git, "merge_base", return_value="abc"), mock.patch.object(git, "file_pair", return_value=(OLD, NEW)), \
                mock.patch.object(diffmod, "run_difft", return_value=RECORDED):
            builder.refine_spans(self.pr(), m)
        self.assertEqual(sorted(m["files"][0]["spans"]), [1, 4])


@unittest.skipUnless(shutil.which("difft"), "difft not installed")
class RealRunTests(unittest.TestCase):
    def test_real_difft_matches_recorded_mapping(self):
        data = diffmod.run_difft(OLD, NEW, "src/b.ts")
        self.assertEqual(data["language"], "TypeScript")
        spans = diffmod.difft_spans(ROWS, data)
        self.assertEqual(spans[1], [[10, 23], [29, 30]])
        self.assertEqual(spans[3], [[10, 24], [30, 31]])
        self.assertEqual(spans[4], [[5, 6], [7, 8]])

    def test_missing_binary_returns_none(self):
        with mock.patch.object(diffmod, "run", side_effect=FileNotFoundError):
            self.assertIsNone(diffmod.run_difft("a", "b", "a.ts"))


if __name__ == "__main__":
    unittest.main()
