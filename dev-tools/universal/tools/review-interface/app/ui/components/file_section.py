import os

from app.ui.html import esc
from app.domain import SEVERITY_LABELS, worst

SIGNS = {"add": "+", "del": "−"}
LANGS = {
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript", ".tsx": "tsx",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript", ".jsx": "jsx",
    ".json": "json", ".css": "css", ".py": "python", ".sql": "sql", ".yml": "yaml", ".yaml": "yaml",
    ".md": "markdown", ".sh": "shellscript", ".bash": "shellscript", ".zsh": "shellscript",
}


def _num(value):
    return "" if value is None else value


def _index_notes(notes):
    hot = {}
    for note in notes:
        for row_id in note["rows"]:
            hot.setdefault(row_id, []).append(note)
    return hot


def _lang(path):
    return LANGS.get(os.path.splitext(path)[1].lower())


def _path_parts(path):
    directory = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
    return directory, path.split("/")[-1]


def _header(f):
    directory, name = _path_parts(f["path"])
    tags = (f'<span class="tag {f["kind"]}">{SEVERITY_LABELS[f["kind"]]}</span>' if f["kind"] else "") + ('<span class="tag gen">Generated</span>' if f["gen"] else "")
    return (
        '<div class="fh"><button type="button" class="fold" aria-expanded="true" aria-label="Collapse file"></button>'
        f'<span class="path" title="{esc(f["path"])}"><span class="dirpart">{esc(directory)}</span>{esc(name)}</span>{tags}'
        f'<span class="stat"><span class="a">+{f["a"]}</span> <span class="d">−{f["d"]}</span></span>'
        f'<label class="viewed"><input type="checkbox" data-read="{f["idx"]}"><span>Viewed</span></label></div><div class="fbody">'
    )


def _moved_label(info):
    if info.get("file") is None or info.get("row") is None:
        return '<span class="mvlabel plain">moved</span>'
    name = _path_parts(info.get("path") or "")[1]
    verb = "to" if info["dir"] == "to" else "from"
    target = f'r{info["file"]}-{info["row"]}'
    line = f' L{esc(info["line"])}' if info.get("line") is not None else ""
    return (
        f'<button type="button" class="mvlabel" data-file="{esc(info["file"])}" data-target="{target}" '
        f'title="Go to {esc(info.get("path") or name)}">moved {verb} {esc(name)}{line}</button>'
    )


def _row_spans(f, index):
    spans = f.get("spans") or {}
    return spans.get(index) or spans.get(str(index))


def _code(text, ranges):
    if not ranges:
        return esc(text)
    out, pos = [], 0
    for start, end in ranges:
        out.append(esc(text[pos:start]) + f'<span class="hl">{esc(text[start:end])}</span>')
        pos = end
    return "".join(out) + esc(text[pos:])


def _row(f, index, row, hot):
    kind, old, new, text = row
    if kind == "hunk":
        return f'<tr class="hunk"><td colspan="3">{esc(text)}</td></tr>'
    row_id = f'r{f["idx"]}-{index}'
    hot_notes = hot.get(row_id, [])
    hot_class = " hot " + worst(n["kind"] for n in hot_notes) if hot_notes else ""
    info = (f.get("moved") or {}).get(str(index))
    moved_class = f" moved moved-{info['dir']}" if info else ""
    label = _moved_label(info) if info and info.get("start") else ""
    return (
        f'<tr id="{row_id}" data-f="{f["idx"]}" data-o="{_num(old)}" data-n="{_num(new)}" class="{kind}{moved_class}{hot_class}">'
        f'<td class="num">{_num(old)}</td><td class="num">{_num(new)}</td>'
        f'<td class="code"><span class="sign">{SIGNS.get(kind, " ")}</span><span class="t">{_code(text, _row_spans(f, index))}</span>{label}</td></tr>'
    )


def _table(f, notes):
    hot = _index_notes(notes)
    rows = "\n".join(_row(f, i, row, hot) for i, row in enumerate(f["rows"]))
    flag = ' data-spans="difft"' if f.get("spans") else ""
    return f'<div class="diffwrap"><table class="diff"{flag}><tbody>\n{rows}\n</tbody></table></div>'


def render(f, notes):
    classes = "file" + (" focused" if notes else "") + (" generated" if f["gen"] else "")
    lang = _lang(f["path"])
    lang_attr = f' data-lang="{lang}"' if lang else ""
    parts = [f'<section class="{classes}" id="f-{f["idx"]}" data-f="{f["idx"]}"{lang_attr}>', _header(f)]
    if f["gen"]:
        parts.append(f'<p class="gen-note">Generated file, {f["a"] + f["d"]} changed lines. Safe to skim.</p><template class="lazy">')
    parts.append(_table(f, notes))
    if f["gen"]:
        parts.append('</template><button type="button" class="expand">Show generated diff</button>')
    return "\n".join(parts) + "</div></section>"
