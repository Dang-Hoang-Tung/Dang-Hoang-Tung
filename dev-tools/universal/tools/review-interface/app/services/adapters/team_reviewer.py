import json
import re
from pathlib import Path

from app.config import dirs, slug
from app.services.insights import SCHEMA


def _section(md, name):
    m = re.search(rf"(?ms)^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", md)
    return m.group(1).strip() if m else ""


def _bullets(text):
    return [re.sub(r"^(\s*[-*]|\d+\.)\s*", "", l).strip() for l in text.split("\n") if l.strip() and not l.strip() == "None."]


def _loc(text):
    for span in re.findall(r"`([^`]+)`", text):
        m = re.match(r"([\w./@…\[\]-]+\.\w+)(?::~?(\d+)(?:[-–,](\d+))?)?", span)
        if m:
            start = int(m.group(2)) if m.group(2) else None
            end = int(m.group(3)) if m.group(3) and int(m.group(3)) >= (start or 0) else start
            return m.group(1).replace("…/", "").replace(".../", ""), start, end
    return None, None, None


def _field(bullets, name):
    for b in bullets:
        if b.lower().startswith(name.lower() + ":"):
            return re.sub(r"[*`]", "", b.split(":", 1)[1]).strip()
    return ""


def _finding(kind, title, rest):
    path, s, e = _loc(rest)
    return {"severity": kind, "title": title, "body": "", "path": path, "start_line": s, "end_line": e, "draft_comment": ""}


def _findings(md):
    recs, kind, cur = [], "should", None
    for ln in _section(md, "Findings").split("\n"):
        if ln.startswith("🔴"): kind = "block"
        elif ln.startswith("🟡"): kind = "should"
        elif ln.startswith("⚪"): kind = "nit"
        m = re.match(r"^(?:🔴|🟡|⚪)?\s*\*\*(.+?)\*\*\s*[—-]\s*(.*)$", ln)
        if m:
            cur = _finding(kind, m.group(1), m.group(2))
            recs.append(cur)
        elif cur and ln.startswith(">"):
            cur["draft_comment"] += re.sub(r"^>\s*(Comment:)?\s*", "", ln) + "\n"
        elif cur and ln.strip() and not re.match(r"^(🔴|🟡|⚪|None\.)", ln):
            cur["body"] += ln.strip() + "\n"
    return recs


_SEV = {"🔴": "block", "🟡": "should", "⚪": "nit"}


def _check(md):
    recs, cur = [], None
    for ln in _section(md, "Check").split("\n"):
        m = re.match(r"^\d+\.\s*(🔴|🟡|⚪)\s*(.*)$", ln)
        if m:
            head = m.group(2)
            title, sep, rest = head.rpartition(" — ")
            if not sep:
                title, rest = head, head
            cur = _finding(_SEV[m.group(1)], re.sub(r"\s*`[^`]*`\s*$", "", title).strip() or title, rest)
            recs.append(cur)
        elif re.match(r"^\s*\+\d+\s+nits?\b", ln):
            cur = None
        elif cur and ln.strip().startswith(">"):
            cur["draft_comment"] += re.sub(r"^\s*>\s*", "", ln) + "\n"
        elif cur and ln.strip() and ln.strip() != "None.":
            cur["body"] += ln.strip() + "\n"
    return recs


def _top_lines(md):
    head = re.split(r"(?m)^## ", md, maxsplit=1)[0]
    return [l.strip() for l in head.split("\n") if re.match(r"^(Verdict|What|Risk|Time):", l.strip())]


def _look_here(md):
    recs = []
    for ln in _section(md, "Look here").split("\n"):
        m = re.match(r"^\d+\.\s+(`[^`]+`.*?)\s+[—-]\s+(.*)$", ln)
        if not m:
            continue
        path, s, e = _loc(m.group(1))
        if path:
            recs.append({"severity": "look", "title": m.group(2)[:140], "body": m.group(2) if len(m.group(2)) > 140 else "",
                         "path": path, "start_line": s, "end_line": e, "draft_comment": ""})
    return recs


def brief_to_insights(md, repo, pr, head_sha):
    tldr = _top_lines(md) or _bullets(_section(md, "30 seconds"))
    risk_full = _field(tldr, "Risk")
    risk = next((r for r in ("High", "Medium", "Low") if risk_full.startswith(r)), "")
    tm = re.search(r"(\d+)\s*min", (_field(tldr, "Time needed") or _field(tldr, "Time")))
    recs = _findings(md) + _look_here(md) + _check(md)
    questions = _bullets(_section(md, "Ask the author")) + _bullets(_section(md, "Questions for the author"))
    for r in recs:
        r["body"], r["draft_comment"] = r["body"].strip(), r["draft_comment"].strip()
    return {
        "schema": SCHEMA, "repo": repo, "pr": pr, "head_sha": head_sha, "source": "team-reviewer-brief",
        "summary": {"verdict": _field(tldr, "Verdict"), "what": _field(tldr, "What"), "risk": risk, "risk_note": risk_full, "minutes": int(tm.group(1)) if tm else None,
                    "tldr": tldr, "questions": questions},
        "recommendations": recs,
    }


def _newest_brief(briefs_dir, pr):
    name = pr["repo"].split("/")[1]
    briefs = sorted(Path(briefs_dir).glob(f"{name}-{pr['number']}-*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    exact = [b for b in briefs if pr["headRefOid"].startswith(b.stem.rsplit("-", 1)[-1])]
    return (exact or briefs or [None])[0]


def _keep_existing(target, brief):
    if not target.exists():
        return False
    try:
        existing = json.loads(target.read_text())
    except ValueError:
        existing = {}
    source = existing.get("source") if isinstance(existing, dict) else None
    return source != "team-reviewer-brief" or target.stat().st_mtime >= brief.stat().st_mtime


def sync_briefs(cfg, prs):
    briefs_dir = cfg["adapters"].get("team_reviewer_briefs")
    if not briefs_dir or not Path(briefs_dir).is_dir():
        return
    out = dirs(cfg)["insights"]
    for pr in prs:
        brief = _newest_brief(briefs_dir, pr)
        if not brief:
            continue
        target = out / f"{slug(pr['repo'], pr['number'])}.json"
        if _keep_existing(target, brief):
            continue
        ins = brief_to_insights(brief.read_text(), pr["repo"], pr["number"], brief.stem.rsplit("-", 1)[-1])
        target.write_text(json.dumps(ins, indent=2))
