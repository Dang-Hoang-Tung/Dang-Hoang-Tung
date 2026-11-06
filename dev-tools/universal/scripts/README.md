# Scripts

Deterministic helpers. Run them instead of doing the steps by hand. All print compact JSON.

- **Read-only** scripts just run.
- Scripts that **change things** are a dry run unless you pass `--apply`.
- None of them print secrets. Tokens and passwords stay in files or in memory.

## Setup

The scripts are general. They read workspace values (repos, branch tag, database, deploys) from `~/.claude/skills/workspace/config.json`. To set up a new workspace, copy `config.example.json` there and fill it in.

`api.py` reads a session token from `~/.claude/agent-files/shared/qa/token`. Each workspace provides its own script to write it (ours: `workspace/scripts/`).

## Scripts

| Script | Does | Changes things? |
| ------ | ---- | --------------- |
| `universal/scripts/project-new.py` | Create a project bank | Local files (`--apply`) |
| `universal/scripts/pr-threads.py` | Unresolved review threads on a PR | No |
| `universal/scripts/pr-ci.py` | Failing CI checks with log tails, minus `workspace/ignore-checks.txt` | No |
| `universal/scripts/api.py` | Call the local or sandbox API with a saved token | Non-GET needs `--apply` |
| `universal/scripts/db.py` | SQL on the local Postgres database | Writes need `--apply` |
| `team-pe/integrate-check.py` | Branches vs main: behind, conflicts, migrations, shared files | No |
| `team-pe/build-morph-branch.py` | Build `<tag>/morph/<date>-<n>` from main + branches | Pushes (`--apply`) |
| `team-pe/deploy-status.py` | Latest deploy run for a branch, with URLs | No |
| `team-pe/cleanup-morph-branches.py` | Delete our old `<tag>/morph/` branches | Yes (`--apply`) |
| `team-reviewer/review-queue.py` | PRs waiting on my or my teams' review | No |
| `buddy/buddy-start.py` | Today's log and active projects | Local file (`--apply`) |
| `dev-polish/post-merge.py` | Remove the worktree and local branch after a merge | Yes (`--apply`) |
| `dev-polish/restack.py` | Rebase a PR stack, in a worktree, no push | Yes (`--apply`) |

Paths are relative to `~/.claude/skills/`. Workspace-only scripts (e.g. minting tokens, production queries) live in `workspace/scripts/`.
