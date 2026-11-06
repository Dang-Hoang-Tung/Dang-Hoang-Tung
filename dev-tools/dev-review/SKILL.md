---
name: dev-review
description: Playbook for code review: reviewer personas, what to check, output format. Use directly to review our own branch ("review my changes"). team-reviewer runs it for other people's PRs.
---

@~/.claude/skills/universal/subagent.md

# Code review

## Setup

- Fetch the latest version of the branch and check it out in a separate worktree, never my working copy. Use the codebase for context.
- Fetch the ticket, if there is one.

## Review

1. Spin up one fresh sub-agent per persona, so each reviews without bias. Give each one the ticket ID, the PR, its persona file, and the task in plain words. Skip the design persona if the change doesn't touch the UI.
2. Compare the findings, drop the weak ones, and merge the rest.

## Don't flag

- Formatting and import order. The linter owns them.
- Generated files and lockfiles.
- Old issues outside the diff, unless they're security-related.

Personas:

- Broad (product, architecture, verdict): `~/.claude/skills/dev-review/review-broad.md`
- Deep (logic, code design, types, tests): `~/.claude/skills/dev-review/review-deep.md`
- Nit (line-by-line rule check, style): `~/.claude/skills/dev-review/review-nit.md`
- Design (project design and design system, UI changes only): `~/.claude/skills/dev-review/review-design.md`

## Verdicts

Approve · Approve with nits · Request changes · Needs a conversation

## Output

Answer each review question in this format:

```
✅/⚠️/❌/💡 <the check, as written in the persona file>
• <Short explanation of the problem, with file citations if relevant>
➔ <Suggestion>
```
