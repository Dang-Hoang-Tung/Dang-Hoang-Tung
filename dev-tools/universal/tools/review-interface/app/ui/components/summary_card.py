from app.ui.markdown import md_block, md_list


def card_html(summary, has_insights):
    if has_insights:
        questions = summary.get("questions")
        return (f'<h3>Summary</h3>{md_list(summary.get("tldr") or [])}'
                + (f"<h3>Questions for the author</h3>{md_list(questions)}" if questions else ""))
    body = md_block(summary.get("description") or "")
    return f'<h3>About this PR</h3><div class="desc">{body or "<p class=muted>No description.</p>"}</div>'


def render(summary):
    return f'<section class="summary">{card_html(summary, summary["has_insights"])}</section>'
