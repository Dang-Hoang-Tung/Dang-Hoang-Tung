# Scoping in the tracker

Goal: turn a direction into a project the team can build in small, shippable pieces.

## Structure

- **Project**: one outcome, with a goal, success signals and an out-of-scope list.
- **Milestones**: each one ships something usable or testable. Put the riskiest assumption first.
- **Tickets**: one small change each, ideally one PR. If a ticket is bigger than a few days, split it.

## Project description

```
## Goal
## Why
## Success signals
## In scope
## Out of scope
## Milestones
## Open questions
## Links
```

## Ticket

```
Title: <verb> <what>, e.g. "Show the risk score on the overview page"

## Why
1-2 sentences: the user problem and the value.

## What
What changes, from the user's point of view.

## Acceptance criteria
- [ ] Given <context>, when <action>, then <result>

## Out of scope

## Links

```

`team-tl` adds an "Agent notes" section with the technical detail (format: `~/.claude/skills/workspace/tools.md`). Keep the whole ticket short and plain.

## Acceptance criteria

- Testable: someone can say pass or fail.
- Written from the user's view, not the code's.
- Cover edge cases, empty states, errors and permissions.
- No implementation detail. That's `team-tl`'s part.

## Process

1. Check the tracker for existing projects and tickets.
2. Show me the full draft (project, milestones, tickets) before writing anything.
3. Once I've said yes and it's in the tracker, send the lead a `reply` with the links.
