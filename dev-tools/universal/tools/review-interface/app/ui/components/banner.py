from app.ui.html import esc


def message(banner, ai_name):
    kind = banner["type"]
    if kind == "draft":
        return "This PR is a draft."
    if kind == "stacked":
        return f"Stacked on <code>{esc(banner['base'])}</code>: the diff shows only this PR's own changes."
    if kind == "stale":
        return (f"{esc(ai_name)} insights were written for <b>{esc(banner['from'][:7])}</b>; "
                f"the PR is now at <b>{esc(banner['to'][:7])}</b>, so some notes may be out of date or on moved lines.")
    if kind == "invalid":
        return f"The insights file was ignored: {esc(banner['reason'])}."
    return ""


def render(banner, ai_name):
    return f'<div class="banner"><div class="banner-text">{message(banner, ai_name)}</div></div>'


def render_all(banners, ai_name):
    return "".join(render(b, ai_name) for b in banners)
