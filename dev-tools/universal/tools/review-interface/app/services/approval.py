from app.config import now
from app.services import github
from app.services.posting import same_commit
from app.services.state import load_state, locked, save_state


class ApprovalConflict(ValueError):
    """The approval cannot go ahead now (409), as opposed to a bad request (400)."""


def check(data, meta, sha):
    if not same_commit(sha, meta["head_sha"]):
        raise ApprovalConflict("This PR has new commits since the page was built. Refresh, then approve.")
    done = data.get("approval")
    if done and same_commit(done.get("commit") or "", meta["head_sha"]):
        raise ApprovalConflict(f"Already approved at {meta['head_sha'][:7]}.")


def approve(cfg, meta, sha, body=None):
    if not isinstance(sha, str) or len(sha) < 7:
        raise ValueError("sha is required")
    if body is not None and not isinstance(body, str):
        raise ValueError("body must be text")
    body = (body or "").strip()
    s = meta["slug"]
    with locked(cfg, s):
        check(load_state(cfg, s), meta, sha)
    res = github.submit_approval(meta["repo"], meta["pr"], meta["head_sha"], body)
    record = {**res, "at": now(), "commit": meta["head_sha"], "body": body}
    with locked(cfg, s):
        data = load_state(cfg, s)
        data["approval"] = record
        save_state(cfg, s, data)
    return record
