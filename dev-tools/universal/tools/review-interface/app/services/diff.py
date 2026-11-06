import difflib
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from app.domain import LAYERS  # noqa: F401
from app.services.shell import FAILURES, run

HUNK = re.compile(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def parse_file_rows(lines):
    rows, old, new, a, d = [], 0, 0, 0, 0
    for ln in lines:
        h = HUNK.match(ln)
        if h:
            old, new = int(h.group(1)), int(h.group(2))
            rows.append(("hunk", None, None, ln))
        elif not rows or ln.startswith("\\"):
            continue
        elif ln.startswith("+"):
            rows.append(("add", None, new, ln[1:]))
            new, a = new + 1, a + 1
        elif ln.startswith("-"):
            rows.append(("del", old, None, ln[1:]))
            old, d = old + 1, d + 1
        else:
            rows.append(("ctx", old, new, ln[1:]))
            old, new = old + 1, new + 1
    return rows, a, d


ESCAPES = {"n": 10, "t": 9, "r": 13, "a": 7, "b": 8, "f": 12, "v": 11, "\\": 92, '"': 34}


def unquote(p):
    """Undo git's C-style quoting of paths with special or non-ASCII characters."""
    if not (len(p) >= 2 and p[0] == '"' and p[-1] == '"'):
        return p
    raw, out, i = p[1:-1], bytearray(), 0
    while i < len(raw):
        if raw[i] == "\\" and i + 1 < len(raw):
            m = re.match(r"[0-7]{1,3}", raw[i + 1:])
            if m:
                out.append(int(m.group(0), 8) & 255)
                i += 1 + len(m.group(0))
            else:
                out.append(ESCAPES.get(raw[i + 1], ord(raw[i + 1]) & 255))
                i += 2
        else:
            out += raw[i].encode()
            i += 1
    return out.decode("utf-8", "replace")


def side_path(text, prefix):
    p = unquote(text[:-1] if text.endswith("\t") else text)
    return p[2:] if p.startswith(prefix) else None


def header_info(first, lines):
    """File path and binary flag, from the lines before the first hunk."""
    path, rename, old, binary = None, None, None, False
    for ln in lines:
        if ln.startswith("@@"):
            break
        if ln.startswith("+++ "):
            path = side_path(ln[4:], "b/")
        elif ln.startswith("--- "):
            old = side_path(ln[4:], "a/")
        elif ln.startswith("rename to "):
            rename = unquote(ln[10:])
        elif ln.startswith("GIT binary patch") or (ln.startswith("Binary files ") and ln.endswith(" differ")):
            binary = True
    if not path:
        path = rename or old
    if not path:
        m = re.match(r"a/(.+) b/\1$", first)
        path = m.group(1) if m else None
    return path, binary


SIMILAR_ENOUGH = 0.4


def _changed_ranges(matcher, side):
    """Character ranges on one side ('a' = old, 'b' = new) that the matcher marks as changed."""
    out = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        start, end = (i1, i2) if side == "a" else (j1, j2)
        if tag != "equal" and end > start:
            out.append([start, end])
    return out


def inline_spans(rows):
    """{row index: [[start, end], ...]} for removed/added lines that pair up as edits of each other."""
    spans, i = {}, 0
    while i < len(rows):
        if rows[i][0] != "del":
            i += 1
            continue
        dels = []
        while i < len(rows) and rows[i][0] == "del":
            dels.append(i); i += 1
        adds = []
        while i < len(rows) and rows[i][0] == "add":
            adds.append(i); i += 1
        for d, a in zip(dels, adds):
            m = difflib.SequenceMatcher(None, rows[d][3], rows[a][3], autojunk=False)
            if m.ratio() >= SIMILAR_ENOUGH:
                spans[d], spans[a] = _changed_ranges(m, "a"), _changed_ranges(m, "b")
    return spans


def _char_col(text, byte_col):
    return len(text.encode()[:byte_col].decode(errors="ignore"))


def _merged(ranges):
    out = []
    for start, end in sorted(ranges):
        if end <= start:
            continue
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def difft_spans(rows, data):
    """Same shape as inline_spans, from difftastic's JSON. None when difftastic fell back to plain text."""
    if str(data.get("language", "Text")).startswith("Text"):
        return None
    changes = {"lhs": {}, "rhs": {}}
    for chunk in data.get("chunks", []):
        for entry in chunk:
            for side, line in entry.items():
                changes[side].setdefault(line["line_number"], []).extend(line["changes"])
    spans = {}
    for i, (kind, old, new, text) in enumerate(rows):
        if kind == "del":
            found = changes["lhs"].get(old - 1)
        elif kind == "add":
            found = changes["rhs"].get(new - 1)
        else:
            continue
        ranges = _merged([_char_col(text, c["start"]), _char_col(text, c["end"])] for c in found or [])
        unchanged = list(text)
        for start, end in ranges:
            unchanged[start:end] = " " * (end - start)
        if ranges and "".join(unchanged).strip():
            spans[i] = ranges
    return spans


def run_difft(old, new, name, timeout=10):
    """difftastic's JSON for two file contents, or None if it is missing, fails or times out."""
    base = Path(name).name
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for side, text in (("old", old), ("new", new)):
            Path(tmp, side).mkdir()
            path = Path(tmp, side, base)
            path.write_text(text)
            paths.append(str(path))
        try:
            return json.loads(run("difft", "--display", "json", *paths, timeout=timeout, env={**os.environ, "DFT_UNSTABLE": "yes"}))
        except FAILURES + (OSError, ValueError):
            return None


def parse_diff(diff, generated):
    gen_re = [re.compile(p) for p in generated]
    files = []
    for chunk in re.split(r"(?m)^diff --git ", diff)[1:]:
        lines = chunk.split("\n")
        first, lines = lines[0], lines[1:]
        path, binary = header_info(first, lines)
        if not path:
            continue
        if lines and lines[-1] == "":
            lines.pop()
        rows, a, d = ([], 0, 0) if binary else parse_file_rows(lines)
        files.append({"idx": len(files), "path": path, "rows": rows, "spans": inline_spans(rows), "a": a, "d": d, "binary": binary,
                      "gen": any(r.search(path) for r in gen_re)})
    return files


def layer_of(f):
    p, name = f["path"], f["path"].split("/")[-1]
    if f["gen"]: return "Generated"
    if re.search(r"(\.|_)(test|spec)\.|/__tests__/|/tests?/", p): return "Tests"
    if re.search(r"/i18n/|/locales?/|\.po$", p): return "Copy"
    if re.match(r"use[A-Z]", name): return "Hooks"
    if re.search(r"/lambdas/|/handlers?/|/routes?/|/exports/|Schema\.ts$|/api/", p): return "API"
    if re.search(r"/db/|/data/|/migrations?/|atlas/|/repositor|\.sql$|schema-overrides", p): return "Data"
    if re.search(r"\.tsx$|/components?/|/frontend/", p): return "UI"
    if re.search(r"/libs/|/application/|/domain/|/universal/|/packages/", p): return "Domain"
    if re.search(r"\.(json|ya?ml|toml)$|/infra|sst\.|cdk|\.config\.", p): return "Config"
    return "Other"


def file_hash(rows):
    return hashlib.sha1("\n".join(f"{k}{t}" for k, _, _, t in rows).encode()).hexdigest()[:12]
