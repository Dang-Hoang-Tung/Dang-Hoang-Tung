import json

from app.config import dirs, slug
from app.domain import SEVERITIES

SCHEMA = "review-insights/1"
RISKS = ("Low", "Medium", "High")
MIN_SHA = 7


def line_number(i, name, value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value)
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1:
        return value
    raise ValueError(f"recommendations[{i}].{name} must be a line number or null")


def require_object(value, name):
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def validate_recommendation(i, r):
    require_object(r, f"recommendations[{i}]")
    if r.get("severity") not in SEVERITIES:
        raise ValueError(f"recommendations[{i}].severity must be one of {', '.join(SEVERITIES)}")
    if not r.get("title"):
        raise ValueError(f"recommendations[{i}].title is required")
    start, end = line_number(i, "start_line", r.get("start_line")), line_number(i, "end_line", r.get("end_line"))
    return {
        "id": str(r.get("id") or ""), "severity": r["severity"], "title": r["title"], "body": r.get("body") or "",
        "path": r.get("path") or None, "start_line": start, "end_line": end or start,
        "draft_comment": r.get("draft_comment") or "",
    }


def validate(obj):
    require_object(obj, "insights")
    if obj.get("schema") != SCHEMA:
        raise ValueError(f'schema must be "{SCHEMA}"')
    for key in ("repo", "pr", "head_sha"):
        if not obj.get(key):
            raise ValueError(f"{key} is required")
    if not isinstance(obj["head_sha"], str):
        raise ValueError("head_sha must be a string")
    summ = obj.get("summary") or {}
    require_object(summ, "summary")
    if summ.get("risk") and summ["risk"] not in RISKS:
        raise ValueError("summary.risk must be Low, Medium or High")
    recs = [validate_recommendation(i, r) for i, r in enumerate(obj.get("recommendations") or [])]
    return {**obj, "summary": summ, "recommendations": recs}


def is_current(head_sha, insights_sha):
    sha = insights_sha.strip().lower()
    return len(sha) >= MIN_SHA and head_sha.lower().startswith(sha)


def load(cfg, repo, pr, head_sha):
    f = dirs(cfg)["insights"] / f"{slug(repo, pr)}.json"
    if not f.exists():
        return None, "missing"
    try:
        ins = validate(json.loads(f.read_text()))
    except ValueError as e:
        return None, f"invalid: {e}"
    return ins, ("current" if is_current(head_sha, ins["head_sha"]) else "stale")
