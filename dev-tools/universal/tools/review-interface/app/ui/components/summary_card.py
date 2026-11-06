from app.ui.html import esc
from app.ui.markdown import md_block, md_list


ICONS = {"block": "🔴", "should": "🟡", "nit": "⚪"}


def _where(c):
    if not c.get("path"):
        return ""
    return f' — <code>{esc(c["path"])}{":" + str(c["line"]) if c.get("line") else ""}</code>'


def brief_html(summary):
    if not summary["has_insights"]:
        return '<p class="muted">No brief yet.</p>'
    facts = [("Verdict", summary.get("verdict")), ("What", summary.get("what")), ("Risk", summary.get("risk_note") or summary.get("risk")),
             ("Time", f'{summary["minutes"]} min' if summary.get("minutes") else "")]
    lines = "".join(f"<li><b>{label}:</b> {esc(value)}</li>" for label, value in facts if value)
    questions = summary.get("questions")
    check = "".join(f'<li>{ICONS.get(c["severity"], "")} {esc(c["title"])}{_where(c)}</li>' for c in summary.get("check") or [])
    return (f'<ul class="brief-facts">{lines}</ul>'
            + (f"<h3>Check</h3><ol>{check}</ol>" if check else "")
            + (f"<h3>Ask the author</h3>{md_list(questions)}" if questions else ""))


def description_html(summary):
    body = md_block(summary.get("description") or "")
    return f'<h3>PR description</h3><div class="desc">{body or "<p class=muted>No description.</p>"}</div>'


def card_html(summary, has_insights):
    if has_insights:
        questions = summary.get("questions")
        return (f'<h3>Summary</h3>{md_list(summary.get("tldr") or [])}'
                + (f"<h3>Questions for the author</h3>{md_list(questions)}" if questions else ""))
    return description_html(summary)


def render(summary):
    desc = description_html(summary)
    return f'<section class="summary">{desc}<div class="notes-list" id="notelist"></div></section>'
