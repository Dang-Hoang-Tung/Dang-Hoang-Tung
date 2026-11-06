from app.domain import SEVERITIES
from app.ui.components import icons
from app.ui.components.summary_card import card_html
from app.ui.html import esc

FINDING_LABELS = {
    "block": ("blocking", "blocking"),
    "should": ("should fix", "should fix"),
    "nit": ("nit", "nits"),
    "look": ("look here", "look here"),
    "question": ("question", "questions"),
}


def comments_text(item):
    total, open_count = item["threads"], item["open_threads"]
    return f'{total} comment{"" if total == 1 else "s"}' + (f" · {open_count} open" if open_count else "")


def finding_pills(findings):
    out = []
    for kind in SEVERITIES:
        count = findings.get(kind)
        if count:
            one, many = FINDING_LABELS[kind]
            out.append(f'<span class="pill2"><span class="dot {kind}"></span>{count} {one if count == 1 else many}</span>')
    return out


def pills(item):
    out = []
    if item["verdict"]:
        out.append(f'<span class="pill2 verdict"><b>{esc(item["verdict"])}</b></span>')
    if item["risk"]:
        out.append(f'<span class="pill2 risk-{esc(item["risk"])}">Risk <b>{esc(item["risk"])}</b></span>')
    out.append(f'<span class="pill2">Effort <b>{esc(item["effort"])}</b> · +{item["added"]:,} −{item["deleted"]:,} · {item["files"]} files</span>')
    estimated = "" if item["minutes_source"] == "insights" else " (estimated)"
    out.append(f'<span class="pill2">Review <b>~{item["minutes"]} min</b>{estimated}</span>')
    if item["ci"] != "none":
        out.append(f'<span class="pill2 ci-{esc(item["ci"])}">CI <b>{esc(item["ci"])}</b></span>')
    if item["draft"]:
        out.append('<span class="pill2">Draft</span>')
    return out + finding_pills(item["findings"])


def data_attrs(item):
    search = esc(f'#{item["number"]} {item["title"]} {item["author"]}'.lower())
    return (f'data-search="{search}" data-author="{esc(item["author"])}" data-effort="{esc(item["effort"])}" '
            f'data-brief="{int(item["has_insights"])}" data-ci="{esc(item["ci"])}" data-draft="{int(item["draft"])}" data-min="{item["minutes"]}"')


def _row(item):
    href = f'{esc(item["slug"])}.html'
    button = "Brief" if item["has_insights"] else "Details"
    return (
        f'<a class="qrow" href="{href}"><span class="prnum">#{esc(item["number"])}</span>'
        f'<span class="t">{esc(item["title"])}</span>'
        f'<time class="chip hide-md" data-req datetime="{esc(item["requested_at"])}">{esc(item["requested_at"][:10])}</time>'
        f'<span class="chip mono">{esc(item["head_sha"][:7])}</span><span class="chip">{comments_text(item)}</span>'
        f'<button type="button" class="briefbtn" aria-expanded="false">{button}{icons.CHEVRON_DOWN}</button></a>'
    )


def _body(item):
    href = f'{esc(item["slug"])}.html'
    return (
        f'<div class="qbody"><div class="pills">{"".join(pills(item))}</div>{card_html(item["summary"], item["has_insights"])}'
        f'<div class="qactions"><a class="iconbtn open-review" href="{href}">Open review →</a></div></div>'
    )


def render(item):
    return f'<div class="qitem" {data_attrs(item)}>{_row(item)}{_body(item)}</div>'
