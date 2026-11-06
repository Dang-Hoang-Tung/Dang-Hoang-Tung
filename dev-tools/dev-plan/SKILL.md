---
name: dev-plan
description: Playbook for planning one ticket or PR: understand the task, explore the code, check the design, pick the approach. Used through dev-auto, by team-tl to explore code, or directly.
---

@~/.claude/skills/universal/subagent.md

# Planning

Plan one ticket or PR: understand the task, understand the code, decide the approach. Project-level technical design lives in `team-tl`.

## 1. Understand the task

- Read the ticket for the given ID.
- Check the project doc for a technical design and PR plan (see the glossary).
- Size it (see the glossary): **Small**, **Medium** or **Large**. Inside a planned project, a PR is just its piece of the PR plan.

## 2. Explore the code

Look at the code the ticket touches, in the relevant repos. Repos and stack: `~/.claude/skills/workspace/stack.md`

Summarise what matters for our goal. For a Small change, a few lines is enough:

- Entrypoints
- Layers and boundaries
- Data flows
- Patterns and design principles in use
- How it fits into the rest of the system, and how it integrates with the main repo (`repos.main` in `~/.claude/skills/workspace/config.json`)

For bigger changes, draw a simple, high-level Mermaid diagram of the services, data stores and how they interact. Group things if there are too many.

## 3. Check the design (UI changes)

Skip this if the project doc already has team-designer's review, unless this PR has UI it didn't cover. Otherwise follow `~/.claude/skills/universal/code/design-system.md`:

- Find the project design (usually linked on the ticket or project) and read it.
- List the design-system components, tokens and icons it needs.
- Check each one matches (see "Check it matches" in the design system).
- Raise big gaps with me **before** coding. Say whether the design tool or code looks wrong, and suggest the fix.

## 4. Decide the approach

- **Small**: propose the most suitable change. Keep it scoped to the ticket and lightweight. Raise any code smells for discussion.
- **Medium or Large, with a technical design**: follow it and the PR plan. Plan this PR's piece of it.
- **Medium or Large, no technical design yet**: stop and tell buddy (`blocked`). It needs `/team-tl`.
