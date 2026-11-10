import json

from app.domain import SEVERITIES, SEVERITY_LABELS
from app.ui.components import appbar, banner, chatbar, fabs, file_section, icons, left_panel, modals, popover, summary_card
from app.ui.pages import document

CSS = ["tokens.css", "base.css", "appbar.css", "left-panel.css", "canvas.css", "cards.css", "diff.css",
       "threads.css", "popover.css", "modals.css", "fullview.css", "timer.css", "chat.css", "layout.css"]
JS = ["shared/dom.js", "shared/markdown.js", "shared/time.js", "shared/theme.js",
      "review/data.js", "review/store.js", "review/read-state.js", "review/files.js", "review/left-panel.js",
      "review/scroll-spy.js", "review/tree-canvas.js", "review/modals.js", "review/treemap.js",
      "review/highlight.js", "review/titletip.js", "review/selection.js", "review/checks.js", "review/threads.js", "review/chat.js", "review/popover.js", "review/nav.js",
      "review/approve.js", "review/timer.js", "review/fullview.js", "review/comments.js", "review/resizers.js", "review/whitespace.js", "review/main.js"]


def _file_data(f):
    return {"i": f["idx"], "path": f["path"], "a": f["a"], "d": f["d"], "gen": f["gen"], "layer": f["layer"],
            "st": f.get("status", "modified"), "old": f.get("old_path"),
            "hash": f["hash"], "kind": f["kind"], "notes": list(f["notes"])}


def _note_data(n):
    keys = ("key", "kind", "title", "body", "comment", "file", "start", "end", "rows", "endRow")
    return {k: n[k] for k in keys}


def browser_data(model):
    pr = model["pr"]
    return {
        "pr": pr["number"], "repo": pr["repo"], "slug": pr["slug"], "sha": pr["head_sha"],
        "ai_name": model["ai_name"], "user": model["user"], "has_insights": model["summary"]["has_insights"],
        "layers": model["layers"], "severities": list(SEVERITIES), "severity_labels": dict(SEVERITY_LABELS), "order": model["order"], "tree": model["tree"],
        "status_icons": icons.FILE_STATUS, "status_labels": icons.STATUS_LABELS,
        "files": [_file_data(f) for f in model["files"]],
        "notes": [_note_data(n) for n in sorted(model["notes"], key=lambda n: SEVERITIES.index(n["kind"]))],
    }


def data_script(model):
    payload = json.dumps(browser_data(model)).replace("</", "<\\/")
    return f'<script type="application/json" id="data">{payload}</script>\n'


def _notes_for(model, f):
    return [n for n in model["notes"] if n["file"] == f["idx"]]


def _main(model):
    files = model["files"]
    sections = "\n".join(file_section.render(files[i], _notes_for(model, files[i])) for i in model["order"])
    return (
        "<main>\n"
        '<div class="store" id="store"></div>\n'
        f'{banner.render_all(model["banners"], model["ai_name"])}\n'
        f'{summary_card.render(model["summary"])}\n'
        f"{sections}\n</main>"
    )


def _body(model):
    return (
        f'{appbar.render(model["pr"], model["totals"], model["summary"].get("minutes"))}\n'
        f'<div class="layout">\n{left_panel.render()}\n{_main(model)}\n</div>\n'
        f'{fabs.render()}\n{fabs.comment_button()}\n{popover.render()}\n{chatbar.render(model["ai_name"])}\n{modals.render(model["tree_layout"], model["summary"], model.get("tree_layout_full"))}'
    )


def render(model):
    title = f'Review #{model["pr"]["number"]}'
    return document.render(title, CSS, _body(model), JS, head_extra=data_script(model))
