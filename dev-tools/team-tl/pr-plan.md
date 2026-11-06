# PR plan

Goal: turn a project into small, safe PRs that dev-auto can run one by one, or in parallel with dev helpers.

## Steps

1. Start from the project's tickets and acceptance criteria. Don't change scope. If something doesn't fit, ask your `<slug>-pm` helper (start one if needed), then raise it with buddy.
2. Split the work into PRs. Each PR:
   - does one thing and is easy to review
   - leaves main working (behind a flag if needed)
   - has its own tests
3. Order the PRs so risky and foundational work goes first: schema, then contracts, then backend, then frontend.
4. Mark which PRs depend on each other, and which can be built in parallel by `<slug>-dev-<n>` helpers.
5. Flag risks, unknowns and anything that needs a spike first.

## Output

| # | PR | Depends on | Size (S/M/L) | Risk |
| - | -- | ---------- | ------------ | ---- |

Then the risks and open questions. Add it to the project doc.

## Tracker

- Add an "Agent notes" section to each ticket: approach, files, gotchas. Keep it short and plain. Format: `~/.claude/skills/workspace/tools.md` (Tracker).
