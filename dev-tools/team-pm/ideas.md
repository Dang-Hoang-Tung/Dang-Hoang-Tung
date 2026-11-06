# Idea mode

Goal: find and test new ideas that aren't part of a project yet. If an idea holds up, it becomes a project.

## Find opportunities

- **Product**: changes that improve capabilities, user experience or engagement, or drive revenue.
- **Technical**: changes that improve our dev cycle, cut tech debt, or improve performance.
- **Ways of working**: in a project's retro, ask me:
  - Were there any problems with how we worked?
  - Can any stage or process be improved?

## Retro

At the end of a project:

1. Ask me the ways-of-working questions above.
2. Sort `followups.md` (see Rules in `team-pm`).
3. Add 3–5 lessons to the project's `decisions.md`, under "Retro".

Aim for high impact. Rate each idea with `~/.claude/skills/team-pm/prioritise.md`

## Test ideas with data

Before we commit, check the idea against real data.

- Query production read-only, using the production tools in `~/.claude/skills/workspace/stack.md`. Count real customers only.
- Write scripts to measure the impact or test the assumption.
- Say what the data shows, with the query you used.

## Next step

For an idea worth pursuing, write the project brief with `~/.claude/skills/team-pm/explore.md`

It then moves to project mode.
