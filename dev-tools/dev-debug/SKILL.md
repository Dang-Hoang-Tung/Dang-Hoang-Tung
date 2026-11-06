---
name: dev-debug
description: Playbook for finding the cause of a bug. Use when something is broken or behaving oddly, e.g. "why is this failing", an error or a bug report. Shipping the fix is team-devit's job.
---

@~/.claude/skills/universal/subagent.md

# Debugging

Method: follow the `superpowers:systematic-debugging` skill (reproduce, isolate, find the root cause, then fix). This playbook adds where to look in our stack.

You're my debug assistant. Help me find and fix the issue.

## Find context

Sources: @~/.claude/skills/universal/sources.md

For bugs, usually:

- Tracker: the related project and tickets
- Chat: threads about the issue
- Observability: traces, logs and metrics for the feature
- Analytics: usage

## Get data

Stack access: @~/.claude/skills/workspace/stack.md

- **Local or sandbox**: if `team-pe` is running, ask it where your branch is deployed. Otherwise hit the sandbox API (see the stack file).
- **Production**: query it read-only (see the stack file). Check logs in the observability tool.
- Local DB and API: `universal/scripts/db.py` and `api.py`.

## Next

Once you know the cause: fix it with `/dev-code` and check it with `/dev-qa`. If it was found outside a project, hand it to `team-devit` through buddy.
