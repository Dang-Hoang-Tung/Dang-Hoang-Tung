import json

from app.ui.html import esc

EFFORTS = ("", "Small", "Medium", "Large")
TOGGLES = (("brief", "Has brief"), ("failing", "CI failing"), ("nodraft", "Hide drafts"))


def author_label(login):
    is_app = login.startswith("app/")
    name = login[len("app/"):] if is_app else login
    is_bot = is_app or name.endswith("[bot]")
    base = name[: -len("[bot]")] if name.endswith("[bot]") else name
    return f"{base} (bot)" if is_bot else base


def author_options(buckets):
    return [{"value": "", "label": "All authors"}] + [
        {"value": b["author"], "label": author_label(b["author"]), "avatar": b["avatar"]} for b in buckets]


def _effort_buttons():
    return "".join(f'<button type="button" data-effort="{v}" aria-pressed="false">{v or "All"}</button>' for v in EFFORTS)


def _filters_menu():
    options = "".join(f'<label class="fopt"><input type="checkbox" data-tog="{k}">{label}</label>' for k, label in TOGGLES)
    return ('<div class="dd fmenu" id="qf"><button type="button" class="dd-btn fbtn" aria-haspopup="true" aria-expanded="false">'
            'Filters<span class="fcount" hidden></span><svg class="dd-chev" viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg></button>'
            f'<div class="dd-menu fpanel" hidden>{options}<div class="frow"><button type="button" class="qclear" id="fclear">Clear</button></div></div></div>')


def render(buckets):
    options = esc(json.dumps(author_options(buckets)))
    return (
        '<div class="qbar"><input id="qs" class="qsearch" type="search" placeholder="Search title, number or author" aria-label="Search" autocomplete="off">'
        f'<div id="qa" data-options="{options}"></div>'
        f'<div class="seg" role="group" aria-label="Effort">{_effort_buttons()}</div>{_filters_menu()}'
        '<button type="button" class="qclear" id="qclear" hidden>Clear</button></div>'
    )


def empty_filtered():
    return ('<p class="empty qnone" id="qnone" hidden>No PRs match these filters.'
            '<button type="button" class="qclear">Clear</button></p>')
