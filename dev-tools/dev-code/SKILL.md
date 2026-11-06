---
name: dev-code
description: Playbook for writing code: how to approach it and the coding principles to follow. Use directly for "write this code" or "implement this", or through dev-auto.
---

@~/.claude/skills/universal/subagent.md

# Writing code

## Before coding

- Read the ticket and its acceptance criteria. Light mode skips `/dev-plan`, so don't skip this.
- State your assumptions. If unsure, ask.
- If there's a simpler approach, say so. Push back when it's warranted.
- If something is unclear, stop, name what's confusing, and ask.
- Define what success looks like.

## Finishing

- Keep going until success is verified.
- Add or update tests with the change (`~/.claude/skills/universal/code/tests.md`).
- For multi-step tasks, list the steps as a numbered list and do them one by one.

## Principles

Follow the shared coding principles. Reviews check code against the same rules.

@~/.claude/skills/universal/code/README.md

- @~/.claude/skills/universal/code/architecture.md
- @~/.claude/skills/universal/code/style.md
