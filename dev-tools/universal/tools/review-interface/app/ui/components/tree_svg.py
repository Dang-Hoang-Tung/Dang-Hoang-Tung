from app.ui.html import esc


def _n(value):
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _notes_text(count):
    return f" · {count} note" + ("" if count == 1 else "s") if count else ""


def _edge(path):
    return f'<path class="edge" d="{esc(path)}"/>'


def _node_classes(node):
    kind = node["kind"] or ""
    return f'node {node["role"]} {kind}{" gen" if node["gen"] else ""}'


def _node_body(node):
    x, y, cx = node["x"], node["y"], node["cx"]
    return (
        f'<rect class="{_node_classes(node)}" x="{_n(x)}" y="{_n(y)}" width="{_n(node["w"])}" height="{_n(node["h"])}" rx="7"/>'
        f'<text class="nlabel" x="{_n(cx)}" y="{_n(y + 18)}">{esc(node["label"])}</text>'
        f'<text class="nstat" x="{_n(cx)}" y="{_n(y + 33)}"><tspan class="a">+{node["a"]}</tspan> <tspan class="d">−{node["d"]}</tspan>'
        f'{_notes_text(node["notes"])}{" · generated" if node["gen"] else ""}</text>'
        f'<title>{esc(node["title"])}</title>'
    )


def render_node(node):
    body = _node_body(node)
    if node["file"] is None:
        return f"<g>{body}</g>"
    return f'<a class="tlink" data-file="{node["file"]}" tabindex="0" role="link">{body}</a>'


def render(layout):
    width, height = layout["width"] + 4, layout["height"] + 4
    edges = "".join(_edge(p) for p in layout["edges"])
    nodes = "".join(render_node(n) for n in layout["nodes"])
    return f'<svg class="tree" width="{_n(width)}" height="{_n(height)}" viewBox="-2 -2 {_n(width)} {_n(height)}">{edges}{nodes}</svg>'


def card(layout):
    return (
        '<section class="canvas-card" id="treecard"><div class="card-head"><h2>Where this change lands</h2><div class="zoom">'
        '<button type="button" class="iconbtn sm wide" id="treetoggle" aria-expanded="false" aria-label="Expand code tree">Expand</button>'
        '<button type="button" class="iconbtn sm" data-zoom="out" aria-label="Zoom out">−</button>'
        '<button type="button" class="iconbtn sm wide" data-zoom="fit" aria-label="Fit to view">Fit</button>'
        '<button type="button" class="iconbtn sm" data-zoom="in" aria-label="Zoom in">+</button></div></div>\n'
        f'<div class="canvas" id="treecanvas"><div class="stage">{render(layout)}</div></div>\n'
        '<div class="legend"><span><span class="dot should"></span>Should fix</span><span><span class="dot nit"></span>Nit</span>'
        '<span><span class="dot look"></span>Look here</span><span><span class="dot question"></span>Question</span>'
        '<span class="muted">Drag to pan · ⌘-scroll to zoom · click a file to jump</span></div></section>'
    )
