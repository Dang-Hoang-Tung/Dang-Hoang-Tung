import html


def esc(value):
    return "" if value is None else html.escape(str(value), quote=True)


def svg_icon(inner):
    return f'<svg viewBox="0 0 24 24">{inner}</svg>'
