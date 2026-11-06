---
name: dev-polish
description: Playbook for getting a PR ready to merge (CI, review comments), and preparing each PR in a stack for me to merge. Use for "polish this PR" or "address the review comments".
---

@~/.claude/skills/universal/subagent.md

# Polishing a PR

Clean up the small problems and get the PR ready for production.

## Steps

1. Make sure you're on the right branch.
2. Check CI: `python3 ~/.claude/skills/universal/scripts/pr-ci.py <pr>`. Fix failures if you can. Checks to ignore are in `~/.claude/skills/workspace/ignore-checks.txt`.
3. Fetch all unresolved review threads: `python3 ~/.claude/skills/universal/scripts/pr-threads.py <pr>`.
4. Check each one is a real issue in our codebase. For bot reviews, check the claim is practical and significant.
5. Handle each one:
   - **Clear fix**: just do it.
   - **About a past decision**: summarise the decision in a line, with pros and cons of our approach vs the suggestion.
   - **Needs my decision**: summarise the problem, with pros and cons of each option.
6. Replies:
   - **Bot reviews** (the review bots in `~/.claude/skills/workspace/tools.md`): reply in the thread and resolve it.
   - **Human reviews**: I'll reply. Suggest what I could say, in a sentence.
7. Keep a short numbered list of the issues and how we're resolving each one.

Fix in a new commit on top (unless reverting), so reviewers see only what changed since their review.

# PR stacks

Bigger work usually ends with a stack of PRs to merge into main.

- I merge one PR at a time, from the bottom up. Keep fixing until I've merged it, then move to the next one.
- Don't restack the PRs above until the current one is settled, so its decisions are final before they flow up.
  - Exception: when we QA the whole branch at the tip, restack everything first.
- If the direction changes, note it so we can align the PRs above as we go.
- Rebase stacks with `python3 ~/.claude/skills/dev-polish/restack.py <new-base> <branch-1> <branch-2> ... --repo <worktree>` (dry run first, then `--apply`).
- You can force push PRs after rebasing or resetting.

# After I merge

1. Move the ticket to Done.
2. If you're a helper, tell your lead. If you're the lead and this was the last PR, send `done` to buddy and team-pe.
3. Remove the worktree and the local branch: `python3 ~/.claude/skills/dev-polish/post-merge.py <branch> --apply`.
