from app.ui.components import queue_bucket, queue_controls
from app.ui.html import esc
from app.ui.pages import document

CSS = ["tokens.css", "base.css", "appbar.css", "cards.css", "dropdown.css", "queue.css"]
JS = ["shared/dom.js", "shared/time.js", "shared/dropdown.js", "queue/filters.js", "queue/main.js"]


def _count(model):
    return sum(len(b["items"]) for b in model["buckets"])


def _heading(model):
    return (
        f'<div class="qhead"><h1>Hello {esc(model["user"])}. Let\'s review!</h1>'
        f'<span class="sub" id="qsum">{_count(model)} PRs · ~{model["total_minutes"]} min</span></div>'
    )


def _content(model):
    if not model["buckets"]:
        return '<p class="empty">Nothing waiting for your review.</p>'
    buckets = "".join(queue_bucket.render(b) for b in model["buckets"])
    return queue_controls.render(model["buckets"]) + buckets + queue_controls.empty_filtered()


def render(model):
    body = f'<div class="queue">{_heading(model)}\n{_content(model)}</div>'
    return document.render("Review queue", CSS, body, JS if model["buckets"] else None)
