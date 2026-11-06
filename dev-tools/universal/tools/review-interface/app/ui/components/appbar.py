import re

from app.ui.components import icons
from app.ui.html import esc


def _ci_chip(ci):
    css = "ok" if ci == "passing" else "bad" if ci == "failing" else ""
    return f'<span class="chip {css}"><span class="dotc"></span>CI {esc(ci)}</span>'


NAVCHIP = (
    '<div class="navchip" id="navchip"><button type="button" id="navprev" aria-label="Previous note or comment">‹</button>'
    '<span id="navcount"></span><button type="button" id="navnext" aria-label="Next note or comment">›</button></div>'
)


def short_verdict(verdict):
    return re.split(r"\(|\.| - ", verdict, maxsplit=1)[0].strip() or verdict


def verdict_chip(verdict):
    if not verdict:
        return ""
    return f'<span class="chip verdict" title="{esc(verdict)}">{esc(short_verdict(verdict))}</span>'


def size_chip(totals):
    return (
        f'<span class="chip" id="leftchip" title="Lines and files you haven\'t marked as viewed"><span class="a">+{totals["added_all"]:,}</span><span class="d">−{totals["deleted_all"]:,}</span>'
        f'<span class="left-files">· {totals["files"]} files</span><span class="topprog"><b id="pbar"></b></span></span>'
    )


def _ci(ci):
    if ci == "none":
        return ""
    css = "ok" if ci == "passing" else "bad" if ci == "failing" else ""
    return f'<span class="ci {css}"><span class="dotc"></span>CI {esc(ci)}</span>'


def meta_line(pr):
    parts = [
        f'<span class="author">{esc(pr["author"])}</span>',
        f'<a class="prlink" href="{esc(pr["url"])}" target="_blank" rel="noopener" title="Open pull request on GitHub">#{esc(pr["number"])}</a>',
        f'<span class="mono sha" title="Commit under review">{esc(pr["head_sha"][:7])}</span>',
        _ci(pr["ci"]),
    ]
    return '<div class="meta">' + "".join(p for p in parts if p) + "</div>"


def _tools(pr):
    return (
        '<div class="tools">'
        '<div class="overflow" id="overflow"><button type="button" class="iconbtn" id="morebtn" aria-label="More options" aria-haspopup="true" aria-expanded="false" title="More">⋯</button>'
        '<div class="menu ovmenu" id="overflowmenu" hidden>'
        '<label class="switch"><input type="checkbox" id="focus">Focused only</label>'
        '<label class="switch"><input type="checkbox" id="hidews">Hide whitespace changes</label>'
        '<div class="ovrow"><span>Theme</span><div class="picker"><button type="button" class="iconbtn sm" id="palettebtn" aria-label="Theme" aria-haspopup="true" aria-expanded="false" title="Theme">'
        f'{icons.PALETTE}</button><div class="menu" id="thememenu" hidden></div></div>'
        f'<button type="button" class="iconbtn sm" id="themebtn" aria-label="Switch light or dark">{icons.THEME_TOGGLE}</button></div></div></div>'
        '<div class="approve-wrap" id="approvewrap" hidden>'
        '<button type="button" class="approve-btn" id="approvebtn" aria-haspopup="true" aria-expanded="false">Approve</button>'
        '<form class="popover" id="approvepop" hidden><textarea id="approvetext" placeholder="Add a comment (optional)" aria-label="Add a comment (optional)"></textarea>'
        '<div class="perr" id="approveerr" role="alert" hidden></div>'
        '<div class="row"><button type="button" class="sm" id="approvecancel">Cancel</button>'
        '<button type="submit" class="approve-btn solid sm" id="approvego">Approve</button></div></form></div>'
        '</div>'
    )


def render(pr, totals, verdict):
    title = esc(pr["title"])
    return (
        f'<header class="appbar"><a class="back" href="index.html" title="Back to the review queue">{icons.BACK}Back</a>\n'
        f'<div class="brand"><h1 id="prtitle" tabindex="0" aria-label="{title}">{title}</h1>{meta_line(pr)}</div>\n'
        f'<div class="topleft">{size_chip(totals)}</div>\n'
        f'{verdict_chip(verdict)}\n'
        f'{NAVCHIP}\n'
        f'{_tools(pr)}</header>'
    )
