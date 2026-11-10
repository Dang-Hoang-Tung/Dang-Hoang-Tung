# Review interface

Local pages for reviewing pull requests: a map of what changed, every file's diff with viewed tracking, line comments that post to GitHub, and a queue of everything waiting for you. It runs on its own from the PR diffs. An AI can add summaries, recommendations and replies through files (see `CONTRACT.md`), but nothing needs one.

## Run

```
python3 review.py                 # build the queue, start the local helper, open it
python3 review.py 29627           # one PR
python3 review.py build --no-open # build only
python3 review.py serve           # start the helper and print the link
```

Needs `gh` (signed in) and Python 3.9+. Changed lines keep git's red, green or purple (moved) tint; `app/services/tokdiff.py` adds the strong highlight on the tokens that changed, and marks lines whose only change is whitespace or formatting. Every command takes `--config PATH` first; the default is `config.json` next to `review.py`.

## Config

```json
{
  "data_dir": "~/.claude/agent-files/shared/team-reviewer/review-ui",
  "port": 47615,
  "ai_name": "Claude",
  "sources": [
    {"repo": "owner/repo", "clone": "~/code/repo", "search": "review-requested:@me -author:@me"}
  ],
  "teams_file": "~/.claude/skills/workspace/review-teams.txt",
  "adapters": {"team_reviewer_briefs": "~/.claude/agent-files/shared/team-reviewer/briefs"}
}
```

- `sources`: one entry per repo. `search` is a GitHub PR search. `limit` caps how many PRs the search returns (default 50). `clone` is optional; with it, diffs come from git (fetched into `refs/review/*`, your branches are never touched), otherwise from the GitHub API.
- `teams` or `teams_file`: teams whose review requests count as yours, for the "requested" time.
- `generated`: regexes for generated files (folded and greyed out). Has sensible defaults.
- `adapters.team_reviewer_briefs`: optional. Turns team-reviewer markdown briefs into insights files.
- `REVIEW_CONFIG` (environment): config path to use when `--config` is not given. `REVIEW_POST_DRY_RUN=1`: posting and approving record a fake result and never calls GitHub (for testing).
- Also: `idle_hours` (helper stops after this long idle, default 2; `0` keeps it running), `keep_days` (review state kept this long, default 14), `user_name`.

## How saving works

`review.py` starts the helper (`app/server/http.py`) if it isn't running and opens the queue through it. The helper listens on 127.0.0.1 only, needs the token from the link it opens, saves each PR's state (comments, viewed files, ticks) to `<data_dir>/state/`, posts comments marked for posting (`post: true`, or the legacy `post:` prefix) and submits the reviewer's approvals with `gh`. It stops after `idle_hours` without use (never, with `0`); run `review.py` again to restart it. The session token is saved in `<data_dir>/token`, so links survive restarts. State files are pruned `keep_days` after their last change. The queue page's **Refresh** button rebuilds everything through the helper and logs what changed to `<data_dir>/events.jsonl` (see CONTRACT.md). Pages opened straight from disk still display but don't save.

## Files

| Path | What |
|---|---|
| `review.py` | Entrypoint, calls `app.cli.main` |
| `app/cli.py` | Commands: build, serve, paths, and `ai list/reply/post` |
| `app/config.py` | Config, defaults, data dirs, `slug()` |
| `app/domain.py` | Shared vocabulary (severities, layers), pure data |
| `app/services/` | GitHub and git access (`github.py`, `git.py`, `shell.py`), diff and tree, insights, review state, posting, view models, manifest, build |
| `app/server/http.py` | The local helper |
| `app/ui/` | HTML components, pages and static CSS/JS (no I/O) |
| `CONTRACT.md` | How an AI reads and writes |
| `DESIGN.md` | Layout and view models |
| `tests/` | `python3 -m unittest discover -s tests` (`helpers.py` holds the shared fixtures) |
