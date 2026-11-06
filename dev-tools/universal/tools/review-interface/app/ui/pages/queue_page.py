from app.ui.components import queue_bucket, queue_controls
from app.ui.html import esc
from app.ui.pages import document

CSS = ["tokens.css", "base.css", "appbar.css", "cards.css", "dropdown.css", "queue.css"]
JS = ["shared/dom.js", "shared/time.js", "shared/dropdown.js", "queue/filters.js", "queue/refresh.js", "queue/main.js"]
REFRESH_ICON = '<svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"/></svg>'


def _count(model):
    return sum(len(b["items"]) for b in model["buckets"])


def _heading(model):
    return (
        f'<div class="qhead"><h1>Hello {esc(model["user"])}. Let\'s review!</h1>'
        f'<div class="qhead-side"><span class="sub" id="qsum">{_count(model)} PRs · ~{model["total_minutes"]} min</span>'
        f'<button type="button" class="qrefresh" id="qrefresh" hidden title="Fetch the latest PRs, diffs and briefs">{REFRESH_ICON}<span>Refresh</span></button></div></div>'
    )


def _content(model):
    if not model["buckets"]:
        return '<p class="empty">Nothing waiting for your review.</p>'
    buckets = "".join(queue_bucket.render(b) for b in model["buckets"])
    return queue_controls.render(model["buckets"]) + buckets + queue_controls.empty_filtered()


def render(model):
    body = f'<div class="queue">{_heading(model)}\n{_content(model)}</div>'
    return document.render("Review queue", CSS, body, JS)
