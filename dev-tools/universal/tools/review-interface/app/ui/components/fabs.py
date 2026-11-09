from app.ui.components import icons


def render():
    return (
        '<div class="fabs" id="fabs"><div class="fabmenu" id="fabmenu" role="menu" hidden>'
        f'<button type="button" class="fab" role="menuitem" id="briefbtn">{icons.BRIEF}<span>AI Brief</span></button>'
        f'<button type="button" class="fab" role="menuitem" id="commentsbtn">{icons.COMMENTS}<span>PR comments</span></button>'
        f'<button type="button" class="fab" role="menuitem" id="treebtn">{icons.TREE}<span>Code tree</span></button>'
        f'<button type="button" class="fab" role="menuitem" id="mapbtn">{icons.MAP}<span>Treemap</span></button></div>'
        '<button type="button" class="fab fabtoggle" id="fabtoggle" aria-haspopup="menu" aria-expanded="false" aria-controls="fabmenu">'
        f'{icons.OVERVIEW}<span>Overview</span><span class="fabchev">{icons.CHEVRON_DOWN}</span></button></div>'
    )


def comment_button():
    return '<button id="cbtn" type="button" hidden>Comment</button>'
