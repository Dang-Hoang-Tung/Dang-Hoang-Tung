from app.services.tree import CHAR_W, ICON_W
from app.ui.components import icons
from app.ui.html import esc


def _n(value):
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _notes_text(count):
    return f" · {count} note" + ("" if count == 1 else "s") if count else ""


def _edge(path):
    return f'<path class="edge" d="{esc(path)}"/>'


FOLDER = ('<svg class="ficon" viewBox="0 0 16 16" aria-hidden="true"><path d="M1.75 4.25c0-.83.67-1.5 1.5-1.5h3l1.5 1.75h5c.83 0 1.5.67 1.5 1.5v6c0 .83-.67 1.5-1.5 1.5H3.25c-.83 0-1.5-.67-1.5-1.5z" '
          'fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round"/></svg>')


def _is_file(node):
    return node.get("file") is not None


def _node_classes(node):
    if not _is_file(node):
        return f'node folder {node["role"]}'
    return " ".join(c for c in ("node file", node["kind"], "gen" if node["gen"] else "") if c)


def _label_x(node):
    return node["cx"] + ICON_W / 2


def _icon(node, y):
    icon = icons.FILE_STATUS.get(node.get("status") or "modified", icons.FILE_STATUS["modified"]) if _is_file(node) else FOLDER
    left = _label_x(node) - len(node["label"]) * CHAR_W / 2 - ICON_W + 2
    return icon.replace("<svg ", f'<svg x="{_n(left)}" y="{_n(y + 7)}" width="13" height="13" ', 1)


def _node_body(node):
    x, y, cx = node["x"], node["y"], node["cx"]
    return (
        f'<rect class="{_node_classes(node)}" x="{_n(x)}" y="{_n(y)}" width="{_n(node["w"])}" height="{_n(node["h"])}" rx="{_n(7 if _is_file(node) else node["h"] / 2)}"/>'
        f'<text class="nlabel" x="{_n(_label_x(node))}" y="{_n(y + 18)}">{esc(node["label"])}</text>'
        f'<text class="nstat" x="{_n(cx)}" y="{_n(y + 33)}"><tspan class="a">+{node["a"]}</tspan> <tspan class="d">−{node["d"]}</tspan>'
        f'{_notes_text(node["notes"])}{" · generated" if node["gen"] else ""}</text>'
        f'{_icon(node, y)}<title>{esc(node["title"])}</title>'
    )


def render_node(node):
    body = _node_body(node)
    if node["file"] is None:
        return f"<g>{body}</g>"
    return f'<a class="tlink" data-file="{node["file"]}" tabindex="0" role="link">{body}</a>'


def render(layout, mode="collapsed", hidden=False):
    width, height = layout["width"] + 4, layout["height"] + 4
    edges = "".join(_edge(p) for p in layout["edges"])
    nodes = "".join(render_node(n) for n in layout["nodes"])
    return (f'<svg class="tree" data-mode="{mode}"{" hidden" if hidden else ""} width="{_n(width)}" height="{_n(height)}" '
            f'viewBox="-2 -2 {_n(width)} {_n(height)}">{edges}{nodes}</svg>')


def canvas(layout, full=None):
    """Both trees go on the page; "Collapse folders" picks which one shows. The full one shows by default."""
    svgs = render(layout, "collapsed", hidden=full is not None) + (render(full, "full") if full is not None else "")
    return f'<div class="canvas" id="treecanvas"><div class="stage">{svgs}</div></div>'


def legend():
    return (
        '<div class="legend"><span><span class="dot should"></span>Should fix</span><span><span class="dot nit"></span>Nit</span>'
        '<span><span class="dot look"></span>Look here</span><span><span class="dot question"></span>Question</span>'
        '<span><span class="dot gen"></span>Generated</span></div>'
    )
