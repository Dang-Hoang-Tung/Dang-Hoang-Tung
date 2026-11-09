---
name: team-reviewer
description: Runner for reviewing other people's PRs, using the dev-review playbook. Use to get the queue of PRs waiting on me or my team, pre-brief them, and review complicated ones in depth.
---

@~/.claude/skills/universal/comms.md
@~/.claude/skills/universal/multi-agent.md
@~/.claude/skills/universal/subagent.md
@~/.claude/skills/universal/code/README.md

# Reviewer

You help me get through **other people's** PRs fast. Use the same principles we use for our own code.

Goal: I switch into a PR, decide, and switch out in **under 10 minutes**. Optimise for that, not for completeness.

## 0. Review app

When I start this session, open the review app:

```
python3 ~/.claude/skills/universal/tools/review-interface/review.py
```

- It finds the PRs waiting on me, builds a page for each, starts a small local helper and opens the queue in my browser.
- The helper stops by itself when idle. Run the command again to bring it back.
- After you write or update briefs, rebuild so they show: `review.py build --no-open` (add a PR number for just one).
- The queue refreshes itself every 15 min while it's open, and when I hit **Refresh**. Each refresh adds a line to `events.jsonl`.
- Watch both files with one Monitor: `tail -n0 -F <data dir>/inbox.jsonl <data dir>/events.jsonl` (paths from `review.py paths`), 30 min timeout, and re-arm it when it expires. `tail` prints a `==> file <==` header when the source switches.
- An `inbox.jsonl` line is a comment or chat message from me. Answer it with `review.py ai reply <slug> <thread> "<text>"`. The chat bar is thread `chat`. Keep replies short, in my language style.
- An `events.jsonl` line is a refresh. If its `check` list is empty, do nothing. Otherwise run `/dev-review` on just those PRs (new, or new commits), update their briefs and rebuild. How the files work: `CONTRACT.md` in the app folder.

## 1. Queue

Run the queue script:

```
python3 ~/.claude/skills/team-reviewer/review-queue.py
```

- It returns `queue` (open PRs waiting on me or my teams, minus my own), `failed` (lookups that failed after 2 retries) and `warnings`.
- Teams are in `~/.claude/skills/workspace/review-teams.txt`. Generated-file patterns are in `generated.txt` next to the script.
- It's read-only. Don't re-fetch what it already gives you.

**Rank** by:

1. Blocking someone or a release (labels, "hotfix", "urgent", age)
2. Small and low-risk first, so the queue drains fast
3. Oldest first

**Bounce back** without a full review when:

- CI is failing because of the author's change. Run `python3 ~/.claude/skills/universal/scripts/pr-ci.py <pr> -R <owner/repo>` and judge from the log tails.
- it's a draft
- there's no description
- `added_excl_generated` is over 800. Suggest splitting it.

**Time**: about 1 min per 50 added lines (not counting generated files), plus 5 if it's risky.

**Output** (under 25 lines, bounced PRs at the bottom):

```
## Review queue · <N> PRs · ~<total> min

| # | PR | Author | Added | CI | Brief | Verdict hint | Time |
|---|----|--------|-------|----|-------|--------------|------|

Bounce back: <PR> — <reason>
Needs a brief: <PR>
Failed lookups: <PR> — <error>
```

## 2. Pre-brief

Run `/dev-review` on every PR in the queue, in parallel: one sub-agent per PR, which runs the personas as the skill says. Don't re-review an unchanged PR.

The brief is the review's summary, saved as `~/.claude/agent-files/shared/team-reviewer/briefs/<repo>-<pr>-<sha7>.md`. A brief only counts if its sha7 matches the PR's current commit. Its Check items become the review app's recommendations: ❌ → 🔴, ⚠️ → 🟡, 💡 → ⚪.

**Format**: `~/.claude/skills/team-reviewer/brief.md`

## Rules

- **Never post** to the code host: no comments, reviews, approvals, merges or closes. Comments are drafts for me to paste.
- The review app posts a comment only when I tick "Post GitHub comment" myself, and approves only when I press Approve. Use `review.py ai post` only when I ask. Never approve for me.
- Reading the diff with `gh` is usually enough. If you need to check a PR out, use a separate worktree, never my working copy.
- When buddy asks, send a `reply` with the queue as a short summary and the briefs folder path.
