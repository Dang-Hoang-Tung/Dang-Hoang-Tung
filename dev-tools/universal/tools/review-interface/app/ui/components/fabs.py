from app.ui.components import icons


def render():
    return (
        f'<div class="fabs"><button type="button" class="fab" id="briefbtn">{icons.BRIEF}<span>AI Brief</span></button>'
        f'<button type="button" class="fab" id="treebtn">{icons.TREE}<span>Code tree</span></button>'
        f'<button type="button" class="fab" id="mapbtn">{icons.MAP}<span>Treemap</span></button></div>'
    )


def comment_button():
    return '<button id="cbtn" type="button" hidden>Comment</button>'
