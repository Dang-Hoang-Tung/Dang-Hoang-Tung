def render():
    return (
        '<aside class="right" aria-label="Review"><div class="resizer" data-side="right" title="Drag to resize · double-click to reset"></div>\n'
        '  <details class="rsec" id="checksec" open><summary><span>Check these</span><span class="count" id="checkcount"></span></summary><div id="checks"></div></details>\n'
        '  <section class="rsec threads-sec"><div class="rhead"><span>Comments</span>'
        '<label class="switch sm"><input type="checkbox" id="fileonly">This file only</label></div>\n'
        '  <div class="store" id="store"></div><div id="list"></div></section>\n'
        '</aside>'
    )
