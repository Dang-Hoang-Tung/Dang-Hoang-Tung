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


def file_status(lines):
    """added, deleted, renamed or modified, plus the old path for a rename, from the lines before the first hunk."""
    status, old = "modified", None
    for ln in lines:
        if ln.startswith("@@"):
            break
        if ln.startswith("new file mode") or ln.startswith("copy to "):
            status = "added"
        elif ln.startswith("deleted file mode"):
            status = "deleted"
        elif ln.startswith("rename from "):
            status, old = "renamed", unquote(ln[12:])
    return status, old


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


def _bridged(ranges, text):
    out = []
    for start, end in ranges:
        if out and not text[out[-1][1]:start].strip():
            out[-1][1] = end
        else:
            out.append([start, end])
    return out


def difft_spans(rows, data):
    """{row index: [[start, end], ...]} for removed/added lines, from difftastic's JSON. None when difftastic fell back to plain text."""
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
        ranges = _bridged(_merged([_char_col(text, c["start"]), _char_col(text, c["end"])] for c in found or []), text)
        if ranges:
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
        status, old_path = file_status(lines)
        files.append({"idx": len(files), "path": path, "rows": rows, "a": a, "d": d, "binary": binary,
                      "status": status, "old_path": old_path,
                      "gen": any(r.search(path) for r in gen_re)})
    return files


ANSI = re.compile(r"\x1b\[[0-9;]*m")
OLD_MOVED, NEW_MOVED = "35", "36"
MAX_CANDIDATES = 50


def moved_lines(colored):
    """{path: {"old": set of old line numbers, "new": set of new line numbers}} for lines git coloured as moved."""
    out = {}
    for chunk in re.split(r"(?m)^(?:\x1b\[[0-9;]*m)*diff --git ", colored)[1:]:
        raw = chunk.split("\n")
        plain = [ANSI.sub("", ln) for ln in raw]
        path, binary = header_info(plain[0], plain[1:])
        if not path or binary:
            continue
        old, new, started = 0, 0, False
        hit = out.setdefault(path, {"old": set(), "new": set()})
        for ln, p in zip(raw[1:], plain[1:]):
            h = HUNK.match(p)
            if h:
                old, new, started = int(h.group(1)), int(h.group(2)), True
                continue
            if not started or not p or p[0] == "\\":
                continue
            color = re.match(r"\x1b\[(\d+)m", ln)
            color = color.group(1) if color else ""
            if p[0] == "-":
                if color == OLD_MOVED:
                    hit["old"].add(old)
                old += 1
            elif p[0] == "+":
                if color == NEW_MOVED:
                    hit["new"].add(new)
                new += 1
            else:
                old, new = old + 1, new + 1
    return out


def find_moves(files, colored=None):
    """Per file, {row index (str): {dir, file, row, path, line, start}} for rows git coloured as moved.

    `colored` is `git diff --color-moved` output. Runs of moved del rows are paired with moved add rows whose
    whitespace-stripped text matches in order; unpaired rows get null file, row, path and line.
    """
    moved = [{} for _ in files]
    if not colored:
        return moved
    flagged = moved_lines(colored)
    text = [[r[3].strip() for r in f["rows"]] for f in files]
    kinds = []
    for f in files:
        hit = flagged.get(f["path"], {"old": (), "new": ()})
        kinds.append([("del" if r[0] == "del" and r[1] in hit["old"] else "add" if r[0] == "add" and r[2] in hit["new"] else None)
                      for r in f["rows"]])
    adds = {}
    for fi in range(len(files)):
        for ri, k in enumerate(kinds[fi]):
            if k == "add":
                adds.setdefault(text[fi][ri], []).append((fi, ri))
    paired = [set() for _ in files]

    def extend(fi, i, fj, j):
        n = 0
        while (i + n < len(kinds[fi]) and j + n < len(kinds[fj]) and kinds[fi][i + n] == "del" and kinds[fj][j + n] == "add"
               and i + n not in paired[fi] and j + n not in paired[fj] and text[fi][i + n] == text[fj][j + n]):
            n += 1
        return n

    for fi, f in enumerate(files):
        i = 0
        while i < len(kinds[fi]):
            if kinds[fi][i] != "del" or i in paired[fi]:
                i += 1
                continue
            best, (fj, j) = 0, (0, 0)
            for cj, cr in adds.get(text[fi][i], [])[:MAX_CANDIDATES]:
                n = extend(fi, i, cj, cr)
                if n > best:
                    best, (fj, j) = n, (cj, cr)
            for k in range(best):
                paired[fi].add(i + k)
                paired[fj].add(j + k)
                moved[fi][str(i + k)] = {"dir": "to", "file": fj, "row": j, "path": files[fj]["path"],
                                         "line": files[fj]["rows"][j][2], "start": k == 0}
                moved[fj][str(j + k)] = {"dir": "from", "file": fi, "row": i, "path": f["path"],
                                         "line": f["rows"][i][1], "start": k == 0}
            i += max(best, 1)
    for fi in range(len(files)):
        for ri, k in enumerate(kinds[fi]):
            if k and ri not in paired[fi]:
                first = ri == 0 or kinds[fi][ri - 1] != k or (ri - 1) in paired[fi]
                moved[fi][str(ri)] = {"dir": "to" if k == "del" else "from", "file": None, "row": None, "path": None,
                                      "line": None, "start": first}
    return moved


def layer_of(f):
    p, name = f["path"], f["path"].split("/")[-1]
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
