---
name: dev-auto
description: Playbook for running a piece of work stage by stage (plan, code, review, polish, QA, merge, retro), Small to Large. Run by project leads: team-tl and its dev helpers, and team-devit (light mode).
---

@~/.claude/skills/universal/subagent.md

# Dev auto

How we run any piece of work: a small fix, a few tickets, or a whole project. Same stages, scaled to the size of the work.

## Stages

0. *(Medium or Large, no plan yet)* `/team-tl` plans it, with team-pm and team-designer helpers
1. Plan: `/dev-plan`
2. Write the code: `/dev-code`
3. Review the code: `/dev-review`
4. Polish the PR: `/dev-polish`
5. QA: `/dev-qa`
6. Merge: `/dev-polish` (PR stacks)
7. Retro and follow-ups: a `<slug>-pm` helper in idea mode

## Scale to the work

Sizes are in the glossary.

- **Small** (light mode, run by `team-devit`): stages 2 to 4. Add other stages only when needed.
- **Medium and Large** (run by `team-tl`):
  - Stage 0 gives the PR plan. Follow its order.
  - Run stages 1 to 4 for each PR. PRs that don't depend on each other can run in parallel with `<slug>-dev-<n>` helpers.
  - QA each PR, or the whole branch at the tip when the PRs only make sense together.
  - I merge the stack one PR at a time (see `/dev-polish`).
  - Run the retro once, at the end.

## How it runs

- After planning, run stages 2 to 4 on your own. I'll step in if I need to.
- QA and merge always need me. If I'm not around, send buddy a `decision`.
- Skip QA for small changes that our tests already cover.
- Load each skill only when its stage starts.
- Log decisions in the project's `decisions.md` (see the ground rules in `comms.md`).

## Scope

- Be ruthlessly minimal. Change only what's necessary.
- Raise anything tangential with me. It usually becomes a follow-up ticket.

## Git

- Branch name: `{user tag}/{ticket ID}/{title}/{subpart (optional)}`. Use this, not the name the tracker suggests. The user tag is in `~/.claude/skills/workspace/config.json`. E.g.
  - `me/ab-1234/example-feature`
  - `me/ab-5678/example-feature/frontend`
- Prefer several small, easy-to-review PRs over one big one. For rebasing stacks, see `/dev-polish`.

## PRs

You can open PRs from stage 2 onwards.

- Short name. Open as "ready for review".
- Don't tag reviewers.
- **Overview**: one simple paragraph on what changed and why.
- **Links**: tickets, designs, docs, chat threads, related PRs, anything else relevant.
- **Show Us**: leave blank. I'll fill it in.
