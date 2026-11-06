import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config.json"
DEFAULTS = {
    "data_dir": "~/.claude/agent-files/shared/team-reviewer/review-ui",
    "port": 47615,
    "idle_hours": 2,
    "keep_days": 14,
    "ai_name": "AI",
    "user_name": "",
    "sources": [],
    "generated": [r"(^|/)generated/", r"[Gg]enerated[A-Z.]", r"\.gen\.", r"(^|/)paths\.ts$", r"atlas\.sum$", r"lock\.ya?ml$", r"package-lock\.json$"],
    "adapters": {},
    "teams": [],
    "teams_file": "",
}


def read_team_lines(path):
    path = Path(path).expanduser()
    if not path.exists():
        return []
    return [l.strip() for l in path.read_text().splitlines() if l.strip() and not l.startswith("#")]


def load_config(path=None):
    path = Path(path or os.environ.get("REVIEW_CONFIG") or DEFAULT_CONFIG).expanduser()
    if not path.exists():
        raise SystemExit(f"No config at {path}. Copy config.example.json to config.json and fill it in.")
    cfg = {**DEFAULTS, **json.loads(path.read_text())}
    cfg["config_path"] = str(path)
    cfg["data_dir"] = Path(cfg["data_dir"]).expanduser()
    for s in cfg["sources"]:
        if s.get("clone"):
            s["clone"] = str(Path(s["clone"]).expanduser())
    cfg["adapters"] = {k: str(Path(v).expanduser()) for k, v in cfg.get("adapters", {}).items()}
    teams = list(cfg["teams"])
    if cfg["teams_file"]:
        teams += read_team_lines(cfg["teams_file"])
    cfg["team_slugs"] = {t.split("/")[-1] for t in teams}
    return cfg


def dirs(cfg):
    root = cfg["data_dir"]
    d = {k: root / k for k in ("pages", "state", "insights", "diffs")}
    for p in d.values():
        p.mkdir(parents=True, exist_ok=True)
    d["root"] = root
    return d


def slug(repo, pr):
    owner, name = repo.split("/")
    return f"{owner}-{name}-{int(pr)}"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
