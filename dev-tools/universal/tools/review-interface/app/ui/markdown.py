import re

from app.ui.html import esc


def md_inline(text):
    text = esc(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)


def _list(items):
    return "<ul>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + "</ul>"


def md_list(items):
    return _list(items) if items else ""


def md_block(text):
    text = re.sub(r"<!--.*?-->", "", text or "", flags=re.S)
    out, para, items, code = [], [], None, None

    def flush():
        nonlocal para, items
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para = []
        if items is not None:
            out.append(_list(items))
            items = None

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if code is None:
                flush()
                code = []
            else:
                out.append("<pre>" + esc("\n".join(code)) + "</pre>")
                code = None
            continue
        if code is not None:
            code.append(raw)
            continue
        if not line.strip():
            flush()
            continue
        heading = re.match(r"^#{1,6}\s+(.*)", line)
        bullet = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(?:\[[ xX]\]\s+)?(.*)", line)
        if heading:
            flush()
            out.append(f"<h4>{md_inline(heading.group(1))}</h4>")
        elif bullet:
            if para:
                flush()
            items = (items or []) + [bullet.group(1)]
        else:
            if items is not None:
                flush()
            para.append(line.strip())
    flush()
    if code is not None:
        out.append("<pre>" + esc("\n".join(code)) + "</pre>")
    return "".join(out)
