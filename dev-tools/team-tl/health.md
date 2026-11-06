# Codebase health

Goal: keep the codebase easy to change and production reliable.

## Health check

When I ask "how healthy is X?":

1. Look at the area in the codebase. Compare it with our coding principles.
2. Look at production signals in the observability tool: errors, latency, failing jobs (see `~/.claude/skills/universal/sources.md`).
3. Look for:
   - code that breaks our principles, or that everyone avoids touching
   - slow, flaky or missing tests
   - repeated bugs or incidents in the same place
   - outdated dependencies or patterns we've moved away from
4. List the findings and rate each one on impact and effort.

## Tech debt

We do want to clean up junk, just not in the middle of a feature. Our usual strategy:

1. **Build the universal solution** as part of the feature, but only use it in our feature. Don't migrate anything else yet.
2. **Finish the feature** and ship it.
3. **Then migrate** the rest of the codebase to the new solution and delete the old code. Add this to `followups.md`; team-pm sorts it in the retro.

Explain the cost of debt in product terms (slower delivery, bugs, risk), so it can be prioritised against features.

## Incidents

1. Stabilise first: roll back, turn off the flag, or hotfix.
2. Find the root cause (`dev-debug`).
3. Add the missing guard: a test, an alert, or a principle rule.
4. Write a short summary: what happened, impact, cause, fix, follow-ups.
