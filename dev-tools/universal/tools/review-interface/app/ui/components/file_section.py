from app.ui.html import esc
from app.domain import SEVERITY_LABELS, worst

SIGNS = {"add": "+", "del": "−"}


def _num(value):
    return "" if value is None else value


def _index_notes(notes):
    ends, hot = {}, {}
    for note in notes:
        if note["endRow"]:
            ends.setdefault(note["endRow"], []).append(note)
        for row_id in note["rows"]:
            hot.setdefault(row_id, []).append(note)
    return ends, hot


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


def _marks(notes):
    return "".join(
        f'<button type="button" class="mk {n["kind"]}" data-note="{esc(n["key"])}" title="{esc(SEVERITY_LABELS[n["kind"]] + ": " + n["title"])}">{SEVERITY_LABELS[n["kind"]]}</button>'
        for n in notes
    )


def _row(f, index, row, ends, hot):
    kind, old, new, text = row
    if kind == "hunk":
        return f'<tr class="hunk"><td colspan="3">{esc(text)}</td></tr>'
    row_id = f'r{f["idx"]}-{index}'
    hot_notes = hot.get(row_id, [])
    hot_class = " hot " + worst(n["kind"] for n in hot_notes) if hot_notes else ""
    return (
        f'<tr id="{row_id}" data-f="{f["idx"]}" data-o="{_num(old)}" data-n="{_num(new)}" class="{kind}{hot_class}">'
        f'<td class="num">{_num(old)}</td><td class="num">{_num(new)}</td>'
        f'<td class="code"><span class="sign">{SIGNS.get(kind, " ")}</span>{esc(text)}{_marks(ends.get(row_id, []))}</td></tr>'
    )


def _table(f, notes):
    ends, hot = _index_notes(notes)
    rows = "\n".join(_row(f, i, row, ends, hot) for i, row in enumerate(f["rows"]))
    return f'<div class="diffwrap"><table class="diff"><tbody>\n{rows}\n</tbody></table></div>'


def render(f, notes):
    classes = "file" + (" focused" if notes else "") + (" generated" if f["gen"] else "")
    parts = [f'<section class="{classes}" id="f-{f["idx"]}" data-f="{f["idx"]}">', _header(f)]
    if f["gen"]:
        parts.append(f'<p class="gen-note">Generated file, {f["a"] + f["d"]} changed lines. Safe to skim.</p><template class="lazy">')
    parts.append(_table(f, notes))
    if f["gen"]:
        parts.append('</template><button type="button" class="expand">Show generated diff</button>')
    return "\n".join(parts) + "</div></section>"
