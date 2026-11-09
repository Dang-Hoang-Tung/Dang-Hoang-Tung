from app.ui.components import icons, summary_card, tree_svg


def _close_button():
    return f'<button type="button" class="iconbtn" data-close aria-label="Close">{icons.CLOSE}</button>'


def _modal(modal_id, title, body):
    return (f'<dialog class="modal" id="{modal_id}"><div class="modal-head"><h2>{title}</h2>{_close_button()}</div>'
            f'<div class="modal-body">{body}</div></dialog>')


def _tree_modal(layout):
    zoom = (
        '<div class="zoom"><button type="button" class="iconbtn sm" data-zoom="out" aria-label="Zoom out">−</button>'
        '<button type="button" class="iconbtn sm wide" data-zoom="fit" aria-label="Fit to view">Fit</button>'
        '<button type="button" class="iconbtn sm" data-zoom="in" aria-label="Zoom in">+</button></div>'
    )
    return (
        '<dialog class="modal tree" id="treemodal"><div class="modal-head"><h2>Where this change lands</h2>'
        f'<div class="head-tools">{zoom}{_close_button()}</div></div>'
        f'<div class="modal-body">{tree_svg.canvas(layout)}</div>'
        f'<div class="modal-foot">{tree_svg.legend()}</div></dialog>'
    )


def render(layout, summary):
    tree = _tree_modal(layout)
    treemap = _modal("mapmodal", "Treemap · size is lines changed, colour is the top finding", '<div class="treemap" id="treemap"></div>')
    brief = _modal("briefmodal", "AI Brief", summary_card.brief_html(summary))
    comments = _modal("commentsmodal", "PR comments", '<div class="clist" id="clist"></div>')
    full = ('<div class="fullview" id="fullview" role="dialog" aria-modal="true" aria-labelledby="fvtitle" hidden>'
            '<div class="fv-card"><div class="modal-head"><div class="fv-nav">'
            '<button type="button" class="iconbtn sm" id="fvback" aria-label="Back" disabled>←</button>'
            '<button type="button" class="iconbtn sm" id="fvfwd" aria-label="Forward" disabled>→</button></div>'
            '<h2 id="fvtitle"></h2><span class="fv-tag" id="fvtag" hidden>Not changed in this PR</span>'
            '<span class="fv-note" id="fvnote" role="status" hidden></span><div class="head-tools">'
            '<div class="fv-seg" role="group" aria-label="View"><button type="button" data-mode="preview" aria-pressed="false">Changes</button>'
            '<button type="button" data-mode="full" aria-pressed="false">Full file</button></div>'
            f'{_close_button()}</div></div>'
            '<div class="fv-body" id="fvbody"></div></div></div>')
    return f"{tree}\n{treemap}\n{brief}\n{comments}\n{full}"
