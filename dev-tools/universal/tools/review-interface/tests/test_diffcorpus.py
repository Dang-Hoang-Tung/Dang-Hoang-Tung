"""Runs every tests/diffcorpus case through real git and the strong-highlight engine, as the review page does."""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import helpers  # noqa: F401
from app.services import diff as diffmod
from app.services import git, tokdiff
from app.ui.components import file_section

CORPUS = Path(__file__).resolve().parent / "diffcorpus"


def git_diff(tmp, name, *args):
    cfg = [a for c in git.MOVED_COLORS for a in ("-c", c)]
    out = subprocess.run(["git", *cfg, "diff", "--no-index", *args, "old/" + name, "new/" + name],
                         cwd=tmp, capture_output=True)
    return out.stdout.decode("utf-8", "replace")


def run_case(case):
    """(rows, moved, spans, quiet, html) for one case folder."""
    old = next(case.glob("old.*"))
    name = "file" + old.suffix
    with tempfile.TemporaryDirectory() as tmp:
        for side in ("old", "new"):
            Path(tmp, side).mkdir()
            shutil.copyfile(case / (side + old.suffix), Path(tmp, side, name))
        files = diffmod.parse_diff(git_diff(tmp, name, "--histogram", "-U12"), [])
        moved = diffmod.find_moves(files, git_diff(tmp, name, *git.MOVED_ARGS))
    if not files:
        return [], {}, {}, set(), ""
    f = files[0]
    spans, quiet = tokdiff.strong_spans(files)[0]
    shown = {**f, "kind": None, "moved": moved[0], "spans": spans, "quiet": sorted(quiet)}
    return f["rows"], moved[0], spans, quiet, file_section.render(shown, [])


def row_at(rows, side, line):
    kind, col = ("del", 1) if side == "old" else ("add", 2)
    return next((i for i, r in enumerate(rows) if r[0] == kind and r[col] == line), None)


def covered(ranges, start, end):
    return all(any(s <= k < e for s, e in ranges) for k in range(start, end))


def problems(case):
    spec = json.loads((case / "case.json").read_text())
    rows, moved, spans, quiet, html = run_case(case)
    out = []
    for i, (kind, old, new, _) in enumerate(rows):
        if kind in ("del", "add"):
            cls = re.search(r'<tr id="r0-%d"[^>]* class="([^"]*)"' % i, html)
            want = {kind} | ({"moved"} if str(i) in moved else set())
            if not cls or not want <= set(cls.group(1).split()):
                out.append("light: %s row %s lost its tint" % (kind, old if kind == "del" else new))
    for item in spec.get("strong_must", []):
        i = row_at(rows, item["side"], item["line"])
        where = "%s:%d" % (item["side"], item["line"])
        if i is None:
            out.append("strong_must %s: git did not change this line" % where)
            continue
        text = rows[i][3]
        found = [m.start() for m in re.finditer(re.escape(item["text"]), text)]
        if not found:
            out.append("strong_must %s: %r is not on the line" % (where, item["text"]))
        elif not any(covered(spans.get(i, []), at, at + len(item["text"])) for at in found):
            out.append("strong_must %s: %r not strong in %r (spans %s)" % (where, item["text"], text, spans.get(i)))
    for item in spec.get("strong_must_not", []):
        i = row_at(rows, item["side"], item["line"])
        if i is not None and spans.get(i):
            out.append("strong_must_not %s:%d: %r has spans %s" % (item["side"], item["line"], rows[i][3], spans[i]))
    for item in spec.get("quiet", []):
        i = row_at(rows, item["side"], item["line"])
        if i is not None and i not in quiet:
            out.append("quiet %s:%d: %r is not quiet" % (item["side"], item["line"], rows[i][3]))
    return out


class DiffCorpusTests(unittest.TestCase):
    def test_every_case(self):
        cases = sorted(p for p in CORPUS.iterdir() if (p / "case.json").exists())
        self.assertTrue(cases)
        failed = {c.name: problems(c) for c in cases}
        failed = {k: v for k, v in failed.items() if v}
        report = "\n".join("%s\n  %s" % (k, "\n  ".join(v)) for k, v in failed.items())
        self.assertEqual(failed, {}, "%d of %d cases fail:\n%s" % (len(failed), len(cases), report))


if __name__ == "__main__":
    unittest.main()
