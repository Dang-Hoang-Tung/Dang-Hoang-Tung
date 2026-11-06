from app.ui.components import icons


def _close_button():
    return f'<button type="button" class="iconbtn" data-close aria-label="Close">{icons.CLOSE}</button>'


def _modal(modal_id, title, body):
    return (f'<dialog class="modal" id="{modal_id}"><div class="modal-head"><h2>{title}</h2>{_close_button()}</div>'
            f'<div class="modal-body">{body}</div></dialog>')


def render():
    tree = _modal("treemodal", "Where this change lands", "")
    treemap = _modal("mapmodal", "Treemap · size is lines changed, colour is the top finding", '<div class="treemap" id="treemap"></div>')
    return f"{tree}\n{treemap}"
