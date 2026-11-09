# AI contract

The review interface runs on its own from PR diffs. An AI (or any script) can add to it through files. Nothing here is required.

Find every path with `python3 review.py paths`, or read `<data_dir>/manifest.json` after a build.

## Files

| File | Who writes it | What it's for |
|---|---|---|
| `events.jsonl` | the tool, on every build or Refresh | One line per rebuild: which PRs to re-check (`check`), new, moved (new commits) and gone PRs, and PRs whose insights are missing or stale |
| `inbox.jsonl` | the page server, when the reviewer writes | One line per new reviewer message. Watch it with `tail -F`; keeps the last 500 lines |
| `manifest.json` | the tool, on every build | Every PR in the queue with its page, state, insights and diff paths |
| `diffs/<slug>.diff` | the tool | The PR's unified diff (git's histogram algorithm, 12 lines of context), for reading |
| `insights/<slug>.json` | an AI, optional | Summary and recommendations shown on the page and in the queue |
| `state/<slug>.json` | the page and an AI | Comment threads, viewed files, checked recommendations |

`<slug>` is `<owner>-<repo>-<number>`, for example `acme-widgets-29627`.

After writing an insights file, run `review.py build` again (or `review.py build <number>`) so the page picks it up. State changes show up when the reviewer returns to the tab; no rebuild needed.

## Manifest entry

```json
{
  "slug": "acme-widgets-29627", "repo": "acme/widgets", "pr": 29627,
  "title": "...", "url": "https://github.com/...", "author": "login", "head_sha": "76689ab6…",
  "requested_at": "2026-11-05T13:28:17Z", "ci": "passing|failing|pending|none", "draft": false, "base": "main",
  "added": 773, "deleted": 336, "files": 26, "effort": "Small|Medium|Large", "minutes": 25,
  "minutes_source": "insights|estimate", "verdict": "Approve with nits", "risk": "Low|Medium|High|", "findings": {"should": 2, "nit": 1},
  "insights_status": "missing|current|stale|invalid: <reason>",
  "page": "…/pages/<slug>.html", "state_file": "…/state/<slug>.json",
  "insights_file": "…/insights/<slug>.json", "diff_file": "…/diffs/<slug>.diff",
  "threads": 3, "waiting_threads": 1, "approved": false
}
```

Fields: `requested_at` is when the review was last requested of you (ISO time). `minutes_source` says whether `minutes` came from the insights or is an estimate. `verdict` and `risk` come from the insights summary (empty without insights). `findings` counts recommendations per severity. `approved` is true when the reviewer has approved the PR's current head.

The manifest itself has `schema` (`review-manifest/1`), `generated_at`, `config`, `contract`, `dirs` (where pages, state, insights, diffs and the root live) and `prs` (the entries above).

`review.py build <n>` updates only that PR: other entries stay as they were, and the queue page is rebuilt from all entries. A PR whose diff cannot be fetched keeps its previous entry.

## Insights file (`review-insights/1`)

```json
{
  "schema": "review-insights/1",
  "repo": "acme/widgets",
  "pr": 29627,
  "head_sha": "76689ab",
  "summary": {
    "verdict": "Approve with nits",
    "risk": "Medium",
    "risk_note": "v2 is flagged, but the layout change is not",
    "minutes": 25,
    "tldr": ["What & why: …", "Risk: …"],
    "questions": ["Which ticket owns the request-page links?"]
  },
  "recommendations": [
    {
      "id": "auto-approve",
      "severity": "should",
      "title": "?action=approve can approve before the review loads",
      "body": "Markdown. **bold**, `code`, - bullets.",
      "path": "apps/frontend/…/ApprovalTaskView.tsx",
      "start_line": 100,
      "end_line": 117,
      "draft_comment": "Ready-to-post comment text."
    }
  ]
}
```

- `head_sha`: the commit you reviewed. Full or at least 7 characters (shorter never matches). If the PR has moved on, the page says the insights are out of date.
- `severity`: `block`, `should`, `nit`, `question` or `look`.
- `path`: full path, or a unique file name. Lines refer to the new side of the diff. Leave `path` out for a general note.
- `id`: optional but recommended. A stable id keeps the reviewer's ticks when you rewrite the file.
- Only `schema`, `repo`, `pr`, `head_sha` and each recommendation's `severity` and `title` are required. Anything else may be left out.
- `start_line` and `end_line` are whole numbers (or numeric strings) or null; anything else makes the file invalid.

## State file

The page writes this; an AI may add replies. Use `review.py ai reply`, or write the file atomically (write a temp file, then rename). `review.py` takes a per-PR lock (`state/<slug>.lock`, `flock`) around its own read-modify-write; take the same lock if you write the file yourself. A state file that is not valid JSON is moved to `state/<slug>.corrupt-<time>.json` and the PR starts empty.

```json
{
  "threads": [
    {
      "id": "lq3k2x9ab", "path": "apps/…/ApprovalTaskView.tsx", "side": "RIGHT", "start_line": 100, "line": 117,
      "noteKey": "auto-approve", "resolved": false, "resolvedAt": null,
      "commit": "76689ab6…",
      "posted": {"url": "https://github.com/…", "message_id": "…", "at": "…"},
      "posted_messages": {"m1": {"url": "https://github.com/…", "id": 123, "at": "…"}},
      "messages": [
        {"id": "m1", "who": "me", "text": "Does anything link here today?", "at": "2026-11-06T12:00:00.000Z"},
        {"id": "m2", "who": "ai", "text": "Only summary-approval emails.", "at": "2026-11-06T12:01:00.000Z"}
      ]
    }
  ],
  "read": {"<file path>": {"read": true, "hash": "…", "at": "…"}},
  "checked": {"<recommendation id>": {"on": true, "at": "…"}},
  "approval": {"url": "https://github.com/…", "id": 456, "at": "…", "commit": "76689ab6…", "body": "", "dry_run": false}
}
```

- `who` is `me` for the reviewer and `ai` for the AI. Message ids must be unique within a thread.
- A thread is waiting for the AI when it is open and its last message is from `me`. `review.py ai list` shows these.
- `commit`: the PR head the thread was written on (set by the page). Posting is refused if it differs from the PR's current head.
- `posted_messages` maps each posted message id to its GitHub comment; `posted` is the latest one, for the page. `posting` is a short-lived marker (`message_id`, `at`) set while a post is in flight; a second post of the same message within 2 minutes is refused. Do not write these by hand.
- A message may carry `"post": true`: the reviewer marked it to be posted to GitHub (see Posting). It must be a boolean.
- `approval` is written only by the helper when the reviewer approves the PR. **An AI must never approve a PR or write `approval`.** The page ignores `approval` sent in a state save.
- `who` also accepts the legacy value `claude`, read as `ai`.
- `noteKey` links a thread to a recommendation's `id`.
- Never delete or rewrite the reviewer's messages; only append.

## Inbox

Each new reviewer message adds one line to `inbox.jsonl`:

```json
{"at": "…", "slug": "acme-widgets-29627", "pr": 29627, "thread": "lq3k2x9ab", "kind": "comment", "path": "apps/…/X.tsx", "line": 117, "text": "…"}
```

`kind` is `chat` for the PR-wide chat, otherwise `comment`. The chat is a normal thread with id `chat` and no `path` or `line`; answer it with `review.py ai reply <slug> chat "text"`.

## Posting to GitHub

A reviewer message with `"post": true` is posted to the PR as written when the reviewer sends it (the legacy form, text starting with `post:`, is still accepted and the prefix is stripped): a line comment for a thread on lines, otherwise a conversation comment. An AI can post a thread's latest message marked for posting with `review.py ai post <slug> <thread>`. Posting is recorded per message in `posted_messages` (and in `posted`) and is never repeated for the same message.

## Thread types

- **Internal** (default): the AI replies; never posted to GitHub.
- **Synced** (`"synced": true`): posted to GitHub; GitHub people reply. **AI: never reply to synced threads.** `review.py ai list` and the inbox skip them.

The type is fixed once set. Posting into an internal thread that already has messages is refused (400 `internal thread`). The first post makes the thread synced and sets `gh_root` (id of the root GitHub review comment); later posts go as replies to it.

Fields: `synced`, `gh_root`; threads from GitHub also have id `gh-<root id>`, `path`, `line`, `side`, `commit` and `outdated: true` when GitHub no longer maps the comment to a line. GitHub messages: `{"id": "gh-<id>", "who": "github", "author", "text", "at", "gh_id", "url"}`; the reviewer's own comments made on github.com are stored with `who: "me"`.

`POST /api/sync/<slug>` pulls the PR's line-comment threads from GitHub (adds only; throttled to once per 30 s per slug) and returns `{"ok": true, "added": N}`. A build also syncs every PR.

## After a refresh

Clicking **Refresh** on the queue page, the queue's own refresh every 15 minutes while it is open, or running `review.py build` rebuilds every page and appends an event to `events.jsonl`. It only ever appends, so `tail -F` on it shows each new event once. `review.py ai changes` prints the latest one:

```json
{"type": "rebuild", "source": "refresh", "at": "…", "partial": false,
 "check": [29627, 29682],
 "new": [{"slug", "pr", "title", "head_sha"}], "moved": [{"slug", "pr", "title", "from", "to"}], "gone": ["<slug>"],
 "needs_insights": [{"slug", "pr", "title", "status": "missing|stale|invalid: …"}]}
```

`check` lists exactly the PRs that are new or have new commits since the previous build. Re-check your read on those (and rewrite their insights); the rest are unchanged.

## Commands for an AI

```
python3 review.py paths                      # where everything lives
python3 review.py ai list                    # threads waiting for a reply
python3 review.py ai changes                 # what changed in the latest rebuild or Refresh
python3 review.py ai reply <slug> <thread> "text"
python3 review.py ai post <slug> <thread>    # only when the reviewer asked for it; never approve
python3 review.py build --no-open [PR …]     # rebuild pages after writing insights
```
