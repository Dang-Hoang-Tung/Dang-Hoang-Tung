from app.ui.components import icons
from app.ui.html import esc


def _ci_chip(ci):
    css = "ok" if ci == "passing" else "bad" if ci == "failing" else ""
    return f'<span class="chip {css}"><span class="dotc"></span>CI {esc(ci)}</span>'


def chips(pr, totals, verdict):
    out = [
        f'<span class="chip hide-md">{esc(pr["author"])}</span>',
        f'<span class="chip hide-md" id="leftchip" title="Lines and files you haven\'t marked as viewed"><span class="a">+{totals["added_all"]:,}</span><span class="d">−{totals["deleted_all"]:,}</span>'
        f'<span class="left-files">· {totals["files"]} files</span></span>',
    ]
    if pr["ci"] != "none":
        out.append(_ci_chip(pr["ci"]))
    if verdict:
        out.append(f'<span class="chip verdict">{esc(verdict)}</span>')
    out.append(f'<span class="chip hide-md mono" title="Commit under review">{esc(pr["head_sha"][:7])}</span>')
    return "".join(out)


def _tools(pr):
    return (
        '<div class="tools"><label class="switch"><input type="checkbox" id="focus">Focused only</label>'
        '<div class="picker"><button type="button" class="iconbtn" id="palettebtn" aria-label="Theme" aria-haspopup="true" aria-expanded="false" title="Theme">'
        f'{icons.PALETTE}</button><div class="menu" id="thememenu" hidden></div></div>'
        f'<button type="button" class="iconbtn" id="themebtn" aria-label="Switch light or dark">{icons.THEME_TOGGLE}</button>'
        f'<a class="iconbtn" href="{esc(pr["url"])}" target="_blank" rel="noopener" aria-label="Open on GitHub" title="Open on GitHub">{icons.EXTERNAL}</a></div>'
    )


def render(pr, totals, verdict):
    return (
        f'<header class="appbar"><a class="back" href="index.html" title="Back to the review queue">{icons.BACK}Back</a>\n'
        f'<div class="brand"><span class="prnum">#{esc(pr["number"])}</span><h1 title="{esc(pr["title"])}">{esc(pr["title"])}</h1></div>\n'
        f'<div class="chips">{chips(pr, totals, verdict)}</div>\n'
        f'{_tools(pr)}</header>'
    )
