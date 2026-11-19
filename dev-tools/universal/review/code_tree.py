"""Code tree: where a change lands, folder by folder, as one HTML file.

    python3 code_tree.py owner/repo#123 [--notes notes.json] [-o code-tree.html] [--open]
    python3 code_tree.py main...HEAD --repo ~/code/app
"""
import argparse
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import page  # noqa: E402
import pr_files  # noqa: E402

NODE_H, GAP_X, CHAR_W, PAD, ROW_GAP, ICON_W = 42, 40, 7.4, 24, 10, 18


def build_tree(paths, root_name, collapse=True):
    """Nested folders. With `collapse`, a folder with one sub-folder and no files merges into it (src/app/lib)."""
    root = {"name": root_name, "children": {}, "file": None}
    for p in paths:
        node = root
        for part in p.split("/"):
            node = node["children"].setdefault(part, {"name": part, "children": {}, "file": None})
        node["file"] = p

    def compress(n, is_root=False):
        kids = [compress(c) for c in n["children"].values()]
        while collapse and len(kids) == 1 and not kids[0]["file"] and not is_root and not n["file"]:
            n = {"name": n["name"] + "/" + kids[0]["name"], "file": None, "kids": kids[0]["kids"]}
            kids = n["kids"]
        return {"name": n["name"], "file": n["file"], "kids": sorted(kids, key=lambda k: (k["file"] is not None, k["name"].lower()))}

    return compress(root, True)


def _label(n):
    return n["name"] if len(n["name"]) <= 44 else n["name"][:20] + "…" + n["name"][-23:]


def _stats(n, by_path):
    if n["file"]:
        f = by_path[n["file"]]
        return f["a"], f["d"], list(f["notes"])
    a = d = 0
    notes = []
    for k in n["kids"]:
        ka, kd, kn = _stats(k, by_path)
        a, d, notes = a + ka, d + kd, notes + kn
    return a, d, notes


def _suffix(notes, gen):
    """What follows "+a −d" on a node: its note count, and whether it is generated."""
    count = len(notes)
    return (f" · {count} note" + ("s" if count != 1 else "") if count else "") + (" · generated" if gen else "")


def _measure(n, by_path):
    a, d, notes = _stats(n, by_path)
    gen = bool(n["file"] and by_path[n["file"]]["gen"])
    suffix = _suffix(notes, gen)
    n["stat"] = {"a": a, "d": d, "notes": notes, "gen": gen, "suffix": suffix}
    n["w"] = max(len(_label(n)) * CHAR_W + ICON_W, len(f"+{a} −{d}{suffix}") * 6.2) + PAD
    for k in n["kids"]:
        _measure(k, by_path)


def _place(n, x, y):
    """Left to right: a node shares a row with its first child, so rows read in folder order."""
    n["x"], n["y"] = x, y
    bottom = y
    for k in n["kids"]:
        bottom = _place(k, x + n["w"] + GAP_X, bottom)
    return max(bottom, y + NODE_H + ROW_GAP)


def _column_xs(root):
    widths = []

    def collect(n, depth):
        if depth == len(widths):
            widths.append(0)
        widths[depth] = max(widths[depth], n["w"])
        for k in n["kids"]:
            collect(k, depth + 1)
    collect(root, 0)
    xs, x = [], 0
    for w in widths:
        xs.append(x)
        x += w + GAP_X
    return xs


def _place_aligned(n, xs, y, depth=0):
    """Like _place, but every node at a depth starts at the same x, so levels line up across branches."""
    n["x"], n["y"] = xs[depth], y
    bottom = y
    for k in n["kids"]:
        bottom = _place_aligned(k, xs, bottom, depth + 1)
    return max(bottom, y + NODE_H + ROW_GAP)


def layout(tree, by_path, aligned=False):
    root = copy.deepcopy(tree)
    _measure(root, by_path)
    if aligned:
        _place_aligned(root, _column_xs(root), 0)
    else:
        _place(root, 0, 0)
    nodes, edges = [], []

    def walk(n, role):
        nodes.append(dict(n, role=role, kind=pr_files.worst(x["severity"] for x in n["stat"]["notes"])))
        kids = n["kids"]
        if not kids:
            return
        mid = lambda m: m["y"] + NODE_H / 2  # noqa: E731
        bus = kids[0]["x"] - GAP_X / 2
        edges.append(f'M{n["x"] + n["w"]},{mid(n)} H{bus}')
        if len(kids) > 1:
            edges.append(f"M{bus},{mid(kids[0])} V{mid(kids[-1])}")
        for k in kids:
            edges.append(f'M{bus},{mid(k)} H{k["x"]}')
            walk(k, "leaf" if k["file"] else "dir")
    walk(root, "root")
    return {"width": max(n["x"] + n["w"] for n in nodes), "height": max(n["y"] + NODE_H for n in nodes), "nodes": nodes, "edges": edges}


def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") or "0"


FOLDER = ('<svg class="ficon" viewBox="0 0 16 16" aria-hidden="true" {attrs}><path d="M1.75 4.25c0-.83.67-1.5 1.5-1.5h3l1.5 1.75h5c.83 0 1.5.67 1.5 1.5v6c0 .83-.67 1.5-1.5 1.5H3.25c-.83 0-1.5-.67-1.5-1.5z" '
          'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>')


def _node(n, change, by_path):
    x, y, w, st = n["x"], n["y"], n["w"], n["stat"]
    cx = x + w / 2
    label_x = cx + ICON_W / 2
    is_file = n["file"] is not None
    cls = " ".join(c for c in ("node file", n["kind"] or "", "gen" if st["gen"] else "") if c) if is_file else f'node folder {n["role"]}'
    icon_at = f'x="{_n(label_x - len(_label(n)) * CHAR_W / 2 - ICON_W + 2)}" y="{_n(y + 7)}" width="13" height="13"'
    icon = page.status_icon(by_path[n["file"]]["status"], icon_at) if is_file else FOLDER.format(attrs=icon_at)
    tip = n["file"] or n["name"]
    if st["notes"] and is_file:
        tip += "".join(f'\n{page.LABELS[x["severity"]]}: {x["title"]}' for x in st["notes"])
    body = (f'<rect class="{cls}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{NODE_H}" rx="{_n(7 if is_file else NODE_H / 2)}"/>'
            f'<text class="nlabel" x="{_n(label_x)}" y="{_n(y + 18)}">{page.esc(_label(n))}</text>'
            f'<text class="nstat" x="{_n(cx)}" y="{_n(y + 33)}"><tspan class="a">+{st["a"]}</tspan> <tspan class="d">−{st["d"]}</tspan>'
            f'{page.esc(st["suffix"])}</text>'
            f'{icon}<title>{page.esc(tip)}</title>')
    href = page.file_link(change, n["file"]) if is_file else None
    if href:
        return f'<a class="tlink" href="{page.esc(href)}" target="_blank" rel="noopener">{body}</a>'
    return f"<g>{body}</g>"


def svg(lay, change, by_path, mode, hidden=False):
    w, h = lay["width"] + 4, lay["height"] + 4
    edges = "".join(f'<path class="edge" d="{e}"/>' for e in lay["edges"])
    nodes = "".join(_node(n, change, by_path) for n in lay["nodes"])
    return (f'<svg class="tree" data-mode="{mode}"{" hidden" if hidden else ""} width="{_n(w)}" height="{_n(h)}" '
            f'viewBox="-2 -2 {_n(w)} {_n(h)}">{edges}{nodes}</svg>')


CSS = """
.canvas{position:relative;overflow:hidden;flex:1;min-height:0;cursor:grab;touch-action:none;
background:radial-gradient(circle at 1px 1px,var(--line) 1px,transparent 0) 0 0/18px 18px,var(--surface-2)}
.canvas.dragging{cursor:grabbing}.canvas.dragging *{pointer-events:none}
.stage{position:absolute;left:0;top:0;transform-origin:0 0}
.tools{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--text-2)}
.tools label{display:inline-flex;align-items:center;gap:6px;margin-right:8px;cursor:pointer}
svg.tree{display:block}svg.tree[hidden]{display:none}
svg.tree .edge{fill:none;stroke:var(--line-strong);stroke-width:1.3}
svg.tree .node{fill:var(--surface);stroke:var(--line-strong);stroke-width:1}
svg.tree .node.folder{fill:var(--surface-3);stroke:none}svg.tree .node.folder.root{fill:var(--accent-soft)}
svg.tree g:has(.folder) .nlabel{font-weight:500;fill:var(--text-2)}
svg.tree .ficon,svg.tree .fstat{color:var(--text-3)}svg.tree g:has(.root) .ficon{color:var(--accent)}
svg.tree .fstat.added{color:var(--add)}svg.tree .fstat.deleted{color:var(--del)}
svg.tree .node.gen{stroke-dasharray:4 3}
svg.tree .node.block{fill:var(--block-soft);stroke:var(--block);stroke-width:1.6}
svg.tree .node.should{fill:var(--should-soft);stroke:var(--should);stroke-width:1.6}
svg.tree .node.nit{fill:var(--nit-soft);stroke:var(--nit);stroke-width:1.4}
svg.tree .node.look{fill:var(--look-soft);stroke:var(--look);stroke-width:1.4}
svg.tree .node.question{fill:var(--question-soft);stroke:var(--question);stroke-width:1.4}
svg.tree .nlabel{font:600 12px var(--mono);fill:var(--text);text-anchor:middle}
svg.tree .nstat{font:500 11px var(--font);fill:var(--text-3);text-anchor:middle}
svg.tree .a{fill:var(--add)}svg.tree .d{fill:var(--del)}
svg.tree a{cursor:pointer}svg.tree a:hover .node,svg.tree a:focus .node{stroke:var(--accent);stroke-width:2}
"""

SCRIPT = """
const box = document.getElementById('canvas'), stage = box.querySelector('.stage');
document.getElementById('tools').innerHTML = '<label><input type="checkbox" id="collapse"> Collapse folders</label>'
  + '<button data-z="out" title="Zoom out">−</button><button data-z="fit">Fit</button><button data-z="in" title="Zoom in">+</button>';
const shown = () => stage.querySelector('svg.tree:not([hidden])');
let s = 1, x = 16, y = 16, drag = null, moved = false;
const apply = () => { stage.style.transform = `translate(${x}px,${y}px) scale(${s})`; };
const fit = () => { const g = shown(), W = +g.getAttribute('width'), H = +g.getAttribute('height');
  s = Math.min(2.5, (box.clientWidth - 32) / W, (box.clientHeight - 32) / H); x = (box.clientWidth - W * s) / 2; y = (box.clientHeight - H * s) / 2; apply(); };
const zoomAt = (f, cx, cy) => { const ns = Math.min(2.5, Math.max(0.15, s * f)); x = cx - ((cx - x) * ns) / s; y = cy - ((cy - y) * ns) / s; s = ns; apply(); };
box.addEventListener('wheel', e => { e.preventDefault();
  if (e.ctrlKey || e.metaKey) { const r = box.getBoundingClientRect(); zoomAt(Math.exp(-e.deltaY / 200), e.clientX - r.left, e.clientY - r.top); }
  else { x -= e.deltaX; y -= e.deltaY; apply(); } }, { passive: false });
box.addEventListener('pointerdown', e => { if (e.button === 0) { drag = { px: e.clientX, py: e.clientY, x, y }; moved = false; } });
addEventListener('pointermove', e => { if (!drag) return; const dx = e.clientX - drag.px, dy = e.clientY - drag.py;
  if (!moved && Math.hypot(dx, dy) > 4) { moved = true; box.classList.add('dragging'); } if (moved) { x = drag.x + dx; y = drag.y + dy; apply(); } });
addEventListener('pointerup', () => { drag = null; box.classList.remove('dragging'); });
box.addEventListener('click', e => { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
document.querySelectorAll('[data-z]').forEach(b => b.onclick = () => b.dataset.z === 'fit' ? fit()
  : zoomAt(b.dataset.z === 'in' ? 1.25 : 0.8, box.clientWidth / 2, box.clientHeight / 2));
document.getElementById('collapse').onchange = e => { stage.querySelectorAll('svg.tree').forEach(g =>
  g.toggleAttribute('hidden', g.dataset.mode !== (e.target.checked ? 'collapsed' : 'full'))); fit(); };
addEventListener('resize', fit); fit();
"""


def render(change):
    by_path = {f["path"]: f for f in change["files"]}
    paths = list(by_path)
    full = layout(build_tree(paths, change["root"], collapse=False), by_path, aligned=True)
    collapsed = layout(build_tree(paths, change["root"]), by_path)
    stage = svg(full, change, by_path, "full") + svg(collapsed, change, by_path, "collapsed", hidden=True)
    body = f'<div class="canvas" id="canvas"><div class="stage">{stage}</div></div>'
    return page.document(change, "Code tree", CSS, body, SCRIPT)


def main(argv=None):
    p = argparse.ArgumentParser(description="Code tree of a PR or git range, as one HTML file.")
    p.add_argument("source", help="owner/repo#123, a PR URL, or a git range like main...HEAD")
    p.add_argument("--repo", default=".", help="repo folder, for a git range")
    p.add_argument("--notes", help="JSON: a list of {path, severity, title}, or a review-insights file")
    p.add_argument("-o", "--out", default="code-tree.html")
    p.add_argument("--open", action="store_true", help="open it in the browser")
    a = p.parse_args(argv)
    page.write(render(pr_files.load(a.source, a.repo, a.notes)), a.out, a.open)


if __name__ == "__main__":
    main()
