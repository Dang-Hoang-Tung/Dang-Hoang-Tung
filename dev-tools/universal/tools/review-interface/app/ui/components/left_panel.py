def render():
    return (
        '<aside class="left" aria-label="Files"><div class="resizer" data-side="left" title="Drag to resize · double-click to reset"></div>\n'
        '  <div class="tabs" role="tablist"><button type="button" role="tab" class="tab on" data-tab="files">Files</button>'
        '<button type="button" role="tab" class="tab" data-tab="layers">Layers</button></div>\n'
        '  <div class="tabpanes"><div class="pane on" id="pane-files"></div><div class="pane" id="pane-layers"></div></div>\n'
        '</aside>'
    )
