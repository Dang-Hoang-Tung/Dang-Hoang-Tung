from app.ui.components import icons, summary_card, tree_svg


def _close_button():
    return f'<button type="button" class="iconbtn" data-close aria-label="Close">{icons.CLOSE}</button>'


NAV = ('<div class="fv-nav vnav"><button type="button" class="iconbtn sm" data-dir="-1" aria-label="Back" disabled>←</button>'
       '<button type="button" class="iconbtn sm" data-dir="1" aria-label="Forward" disabled>→</button></div>')


def _modal(modal_id, title, body, size="lg", nav=False):
    """size is one of the width steps: sm, md, lg, xl."""
    return (f'<dialog class="modal w-{size}" id="{modal_id}"><div class="modal-head">{NAV if nav else ""}<h2>{title}</h2>{_close_button()}</div>'
            f'<div class="modal-body">{body}</div></dialog>')


TREE_TITLE = "Where this change lands"
ZOOM = (
    '<div class="zoom"><button type="button" class="iconbtn sm" data-zoom="out" aria-label="Zoom out">−</button>'
    '<button type="button" class="iconbtn sm wide" data-zoom="fit" aria-label="Fit to view">Fit</button>'
    '<button type="button" class="iconbtn sm" data-zoom="in" aria-label="Zoom in">+</button></div>'
)


def _collapse_toggle():
    return '<label class="switch treecollapse"><input type="checkbox" data-treecollapse>Collapse folders</label>'


def tree_block(layout, full=None):
    """The code tree on the page, under the description. Opening the tree modal moves this canvas into it."""
    return (
        f'<section class="treeblock" id="treeblock"><div class="treeblock-head"><h3>{TREE_TITLE}</h3>'
        f'<div class="head-tools">{_collapse_toggle() if full else ""}{ZOOM}'
        '<button type="button" class="iconbtn sm wide" id="treeexpand" aria-label="Open the code tree full size">Expand</button></div></div>'
        f'<div class="treeblock-body" id="treehome">{tree_svg.canvas(layout, full)}</div>'
        f'<div class="treeblock-foot">{tree_svg.legend()}</div></section>'
    )


def _tree_modal(full=None):
    return (
        f'<dialog class="modal tree w-xl" id="treemodal"><div class="modal-head"><h2>{TREE_TITLE}</h2>'
        f'<div class="head-tools">{_collapse_toggle() if full else ""}{ZOOM}{_close_button()}</div></div>'
        '<div class="modal-body" id="treemodalbody"></div>'
        f'<div class="modal-foot">{tree_svg.legend()}</div></dialog>'
    )


def render(summary, full_layout=None):
    tree = _tree_modal(full_layout)
    treemap = _modal("mapmodal", "Treemap · size is lines changed, colour is the top finding", '<div class="treemap" id="treemap"></div>', "xl")
    brief = _modal("briefmodal", "AI Brief", summary_card.brief_html(summary), "lg", nav=True)
    comments = _modal("commentsmodal", "PR comments", '<div class="clist" id="clist"></div>', "lg", nav=True)
    full = ('<div class="fullview" id="fullview" role="dialog" aria-modal="true" aria-labelledby="fvtitle" hidden>'
            f'<div class="fv-card w-lg"><div class="modal-head">{NAV}'
            '<h2 id="fvtitle"></h2><span class="fv-tag" id="fvtag" hidden>Not changed in this PR</span>'
            '<span class="fv-note" id="fvnote" role="status" hidden></span><div class="head-tools">'
            '<div class="fv-seg" role="group" aria-label="View"><button type="button" data-mode="preview" aria-pressed="false">Changes</button>'
            '<button type="button" data-mode="full" aria-pressed="false">Full file</button></div>'
            f'{_close_button()}</div></div>'
            '<div class="fv-body" id="fvbody"></div></div></div>')
    return f"{tree}\n{treemap}\n{brief}\n{comments}\n{full}"
