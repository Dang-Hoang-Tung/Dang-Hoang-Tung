"""Treemap: each file is a box sized by lines changed, coloured by its most serious note. One HTML file.

    python3 treemap.py owner/repo#123 [--notes notes.json] [-o treemap.html] [--open]
    python3 treemap.py main...HEAD --repo ~/code/app
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import page  # noqa: E402
import pr_files  # noqa: E402

W, H = 1000.0, 600.0


def squarify(items, x, y, w, h):
    """Lay `items` ({"v": size, ...}, biggest first) into the rectangle, keeping boxes close to square."""
    items = [i for i in items if i["v"] > 0]
    if not items:
        return []
    out, total = [], sum(i["v"] for i in items)
    rest = [dict(i, area=i["v"] * w * h / total) for i in items]

    def ratio(row, side):
        s, mx, mn = sum(r["area"] for r in row), max(r["area"] for r in row), min(r["area"] for r in row)
        return max(side * side * mx / (s * s), s * s / (side * side * mn))

    while rest:
        side = min(w, h)
        row, i = [rest[0]], 1
        while i < len(rest) and ratio(row + [rest[i]], side) <= ratio(row, side):
            row.append(rest[i])
            i += 1
        rest = rest[i:]
        s = sum(r["area"] for r in row)
        if w >= h:
            cw, cy = s / h, y
            for r in row:
                out.append(dict(r, x=x, y=cy, w=cw, h=r["area"] / cw))
                cy += r["area"] / cw
            x, w = x + cw, w - cw
        else:
            rh, cx = s / w, x
            for r in row:
                out.append(dict(r, x=cx, y=y, w=r["area"] / rh, h=rh))
                cx += r["area"] / rh
            y, h = y + rh, h - rh
    return out


def boxes(files):
    """Generated files are capped at the biggest hand-written file, so a lockfile can't fill the map."""
    biggest = max([f["a"] + f["d"] for f in files if not f["gen"]] or [1])
    items = [{"f": f, "v": max(1, min(f["a"] + f["d"], biggest) if f["gen"] else f["a"] + f["d"])} for f in files]
    return squarify(sorted(items, key=lambda i: -i["v"]), 0, 0, W, H)


def _pct(v, whole):
    return f"{100 * v / whole:.3f}%"


def _cell(r, change):
    f = r["f"]
    kind = "gen" if f["gen"] else (pr_files.worst(n["severity"] for n in f["notes"]) or "none")
    style = f'left:{_pct(r["x"], W)};top:{_pct(r["y"], H)};width:{_pct(r["w"], W)};height:{_pct(r["h"], H)}'
    tip = f'{f["path"]}  +{f["a"]} −{f["d"]}' + "".join(f'\n{page.LABELS[n["severity"]]}: {n["title"]}' for n in f["notes"])
    inner = ""
    if r["w"] > 60 and r["h"] > 34:
        counts = [f'{sum(n["severity"] == k for n in f["notes"])} {page.LABELS[k].lower()}'
                  for k in pr_files.SEVERITIES if any(n["severity"] == k for n in f["notes"])]
        stat = f'+{f["a"]} −{f["d"]}' + (" · generated" if f["gen"] else "") + "".join(" · " + c for c in counts)
        inner = (f'<span class="tmn">{page.status_icon(f["status"])}{page.esc(f["path"].split("/")[-1])}</span>'
                 f'<span class="tms">{page.esc(stat)}</span>')
    href = page.file_link(change, f["path"])
    tag, link = ("a", f' href="{page.esc(href)}" target="_blank" rel="noopener"') if href else ("div", "")
    return f'<{tag} class="tm {kind}" style="{style}" title="{page.esc(tip)}"{link}>{inner}</{tag}>'


CSS = """
main{flex:1;min-height:0;padding:16px 20px;display:flex;align-items:center;justify-content:center}
.map{position:relative;width:min(100%,calc((100vh - 140px) * 5 / 3));aspect-ratio:5/3}
.tm{position:absolute;padding:8px 10px;border:2px solid var(--bg);background:var(--surface);box-shadow:inset 0 0 0 1px var(--line-strong);display:flex;flex-direction:column;
justify-content:space-between;overflow:hidden;color:var(--text);text-decoration:none}
a.tm:hover{z-index:1;box-shadow:inset 0 0 0 2px var(--accent)}
.tm.block{background:var(--block-soft);box-shadow:inset 0 0 0 1px var(--block)}.tm.should{background:var(--should-soft);box-shadow:inset 0 0 0 1px var(--should)}
.tm.nit{background:var(--nit-soft);box-shadow:inset 0 0 0 1px var(--nit)}.tm.look{background:var(--look-soft);box-shadow:inset 0 0 0 1px var(--look)}
.tm.question{background:var(--question-soft);box-shadow:inset 0 0 0 1px var(--question)}
.tm.gen{background:repeating-linear-gradient(135deg,var(--surface-2) 0 7px,var(--surface-3) 7px 14px);color:var(--text-3)}
.tmn{font:600 12px var(--mono);max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:flex;align-items:center;gap:6px}
.tms{font:500 11px var(--font);color:var(--text-2)}
.fstat{width:14px;height:14px;flex:none;color:var(--text-3)}.fstat.added{color:var(--add)}.fstat.deleted{color:var(--del)}
"""


def render(change):
    cells = "".join(_cell(r, change) for r in boxes(change["files"]))
    return page.document(change, "Treemap · size is lines changed, colour is the top note", CSS, f'<main><div class="map">{cells}</div></main>')


def main(argv=None):
    p = argparse.ArgumentParser(description="Treemap of a PR or git range, as one HTML file.")
    p.add_argument("source", help="owner/repo#123, a PR URL, or a git range like main...HEAD")
    p.add_argument("--repo", default=".", help="repo folder, for a git range")
    p.add_argument("--notes", help="JSON: a list of {path, severity, title}, or a review-insights file")
    p.add_argument("-o", "--out", default="treemap.html")
    p.add_argument("--open", action="store_true", help="open it in the browser")
    a = p.parse_args(argv)
    page.write(render(pr_files.load(a.source, a.repo, a.notes)), a.out, a.open)


if __name__ == "__main__":
    main()
