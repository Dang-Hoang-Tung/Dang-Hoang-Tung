from app.ui.components import icons
from app.ui.html import esc


def _ci_chip(ci):
    css = "ok" if ci == "passing" else "bad" if ci == "failing" else ""
    return f'<span class="chip {css}"><span class="dotc"></span>CI {esc(ci)}</span>'


NAVCHIP = (
    '<div class="navchip" id="navchip"><button type="button" id="navprev" aria-label="Previous note or comment">‹</button>'
    '<span id="navcount"></span><button type="button" id="navnext" aria-label="Next note or comment">›</button></div>'
)


def timer_chip(minutes):
    secs = max(1, int(minutes or 10)) * 60
    return (
        f'<div class="timer" id="timer" data-default="{secs}">'
        '<button type="button" class="chip timerchip" id="timerbtn" aria-haspopup="true" aria-expanded="false" title="Review timer: click to set">'
        f'<span class="tico" aria-hidden="true">⏱</span><span id="timerval">{secs // 60}:00</span></button>'
        '<button type="button" class="timerplay" id="timerplay" aria-label="Start timer" title="Start">▶</button>'
        '<form class="popover timerpop" id="timerpop" hidden><div class="trow">'
        '<label>Min<input type="number" id="timermin" min="0" max="180" inputmode="numeric"></label>'
        '<label>Sec<input type="number" id="timersec" min="0" max="59" inputmode="numeric"></label></div>'
        '<div class="row"><button type="button" class="sm" id="timerreset">Reset</button>'
        '<button type="submit" class="sm solid" id="timerset">Set &amp; start</button></div></form>'
        '<div class="timeup" id="timeup" role="alertdialog" aria-labelledby="timeupmsg" hidden>'
        '<button type="button" class="timeupx" id="timeupclose" aria-label="Close">×</button>'
        '<p id="timeupmsg">⏰ Time\'s up! You used all the time you allocated to this review.</p>'
        '<div class="timeupbtns"><button type="button" data-add="1">Just a minute!</button>'
        '<button type="button" data-add="5">Give me 5 more mins</button>'
        '<button type="button" data-add="10">I need a solid 10 mins</button></div></div>'
        '</div>'
    )


def size_chip(totals):
    return (
        '<div class="progtop" id="leftchip" title="Files you have marked as viewed. The lines are what is left to read.">'
        f'<span class="plines"><span class="a">+{totals["added_all"]:,}</span><span class="d">−{totals["deleted_all"]:,}</span></span>'
        '<span class="pwrap"><span class="ptrack"><b id="pbar"></b></span><span class="pfx" id="pfx" aria-hidden="true"></span></span>'
        f'<span class="left-files">0/{totals["files"]} · 0%</span></div>'
    )


def _ci(ci):
    if ci == "none":
        return ""
    css = "ok" if ci == "passing" else "bad" if ci == "failing" else ""
    return f'<span class="ci {css}" role="img" data-tip="CI {esc(ci)}" aria-label="CI {esc(ci)}"><span class="dotc"></span></span>'


def _branches(pr):
    """Head branch on the meta line, its base on the line below it."""
    sha = esc(pr["head_sha"][:7])
    if not (pr.get("base") and pr.get("head")):
        return f'<span class="mono sha" data-tip="Commit under review">{sha}</span>'
    base, head = esc(pr["base"]), esc(pr["head"])
    stacked = pr.get("stacked")
    base_tip = f"Base: {base}" + (" (stacked on another branch)" if stacked else "")
    return (
        f'<span class="branch head" data-tip="Head: {head} · commit {sha}"><span class="bname">{head}</span>'
        f'<button type="button" class="bcopy" data-copy="{head}" aria-label="Copy branch name" data-tip="Copy branch name">{icons.COPY}</button></span>'
        f'<span class="baserow"><span class="elbow" aria-hidden="true"></span>'
        f'<span class="branch base{" stacked" if stacked else ""}" data-tip="{base_tip}">{base}</span></span>'
    )


def meta_line(pr):
    parts = [
        f'<span class="author" role="img" data-tip="Author: {esc(pr["author"])}" aria-label="Author: {esc(pr["author"])}">{esc((pr["author"] or "?")[:1].upper())}</span>',
        f'<a class="prlink" href="{esc(pr["url"])}" target="_blank" rel="noopener" data-tip="Open pull request on GitHub">#{esc(pr["number"])}</a>',
        _ci(pr["ci"]),
        _branches(pr),
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


def render(pr, totals, minutes=None):
    title = esc(pr["title"])
    return (
        f'<header class="appbar"><div class="topstart"><a class="back" href="index.html" title="Back to the review queue">{icons.BACK}Back</a>\n'
        f'<div class="brand"><h1 id="prtitle" tabindex="0" aria-label="{title}">{title}</h1>{meta_line(pr)}</div></div>\n'
        f'<div class="topleft">{size_chip(totals)}</div>\n'
        f'<div class="topright">{timer_chip(minutes)}\n'
        f'{NAVCHIP}\n'
        f'{_tools(pr)}</div></header>'
    )
