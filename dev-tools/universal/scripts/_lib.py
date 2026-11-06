"""Shared helpers for our scripts. JSON out, dry run by default, never print secrets."""
import json
import os
import pathlib
import subprocess
import sys

HOME = pathlib.Path.home()
SKILLS = HOME / ".claude" / "skills"
WORKSPACE = SKILLS / "workspace"
AGENT_FILES = HOME / ".claude" / "agent-files"
SCRIPTS = pathlib.Path(__file__).parent


def _config():
    path = WORKSPACE / "config.json"
    return json.loads(path.read_text()) if path.exists() else None


CONFIG = _config()


def require_config():
    """Call in scripts that need workspace values. Exits with a clear message if config is missing."""
    if CONFIG is None:
        print(json.dumps({"ok": False, "error": f"missing {WORKSPACE / 'config.json'}: copy universal/scripts/config.example.json there and fill it in"}))
        sys.exit(1)


_c = CONFIG or {"repos": {"main": ".", "worktrees": "."}, "user": {"branch_tag": "me"}, "local": {"db_container": ""}}
APP = pathlib.Path(os.path.expanduser(_c["repos"]["main"]))
WORKTREES = pathlib.Path(os.path.expanduser(_c["repos"]["worktrees"]))
BRANCH_TAG = _c["user"]["branch_tag"]
MORPH_PREFIX = f"{BRANCH_TAG}/morph/"
LOCAL = _c.get("local", {})
DB_CONTAINER = LOCAL.get("db_container")


def run(cmd, cwd=None, check=True, env=None):
    """Run a command, return stdout. Raise RuntimeError with stderr on failure."""
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if check and out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip() or f"{cmd[0]} exited {out.returncode}")
    return out.stdout.strip()


def code(cmd, cwd=None, env=None):
    """Run a command, return (exit code, stdout, stderr)."""
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    return out.returncode, out.stdout.strip(), out.stderr.strip()


def gh_json(*args, cwd=None):
    return json.loads(run(["gh", *args], cwd=cwd) or "null")


def git(*args, repo=APP, check=True):
    return run(["git", *args], cwd=repo, check=check)


def env_file(path):
    """Read KEY=value lines. Values stay in memory only."""
    values = {}
    for line in pathlib.Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.removeprefix("export ").split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def read_list(path):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    lines = (line.strip() for line in path.read_text().splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def out(obj):
    print(json.dumps(obj, separators=(",", ":"), default=str))


def fail(message, **extra):
    out({"ok": False, "error": message, **extra})
    sys.exit(1)


def apply_flag(argv=None):
    """Pop --apply from argv. Scripts that change things are a dry run without it."""
    argv = sys.argv if argv is None else argv
    if "--apply" in argv:
        argv.remove("--apply")
        return True
    return False
