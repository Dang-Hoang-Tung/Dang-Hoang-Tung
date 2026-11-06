from app.ui.components import queue_controls, queue_item
from app.ui.html import esc


def render(bucket):
    items = "".join(queue_item.render(i) for i in bucket["items"])
    return (
        f'<section class="qbucket"><div class="qbhead"><img src="{esc(bucket["avatar"])}" alt="">'
        f'<span>{esc(queue_controls.author_label(bucket["author"]))}</span><span class="n">{len(bucket["items"])}</span></div>{items}</section>'
    )
