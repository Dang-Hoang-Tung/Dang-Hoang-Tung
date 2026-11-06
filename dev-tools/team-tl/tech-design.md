# Technical design

Goal: pick a technical approach we're confident in before we build.

## Steps

1. **Understand**: read the project brief in the project doc. Explore the code involved (step 2 of `dev-plan`). List the requirements, marked **[PRODUCT REQUIREMENT]** or **[TECHNICAL REQUIREMENT]**.
2. **Constraints**: what must stay true? Existing contracts, data, performance, security, deadlines.
3. **Options**: 2-3 approaches. Always include the simplest one that could work.
4. **Compare**: for each option, rate effort, risk, how it fits our architecture, and how hard it is to undo.
5. **Decide**: recommend one and say why. Call out the one-way doors.

## Check every design for

- Data model and migrations (`~/.claude/skills/universal/code/database.md`)
- API contracts and types (`~/.claude/skills/universal/code/types.md`)
- Boundaries between domain, application and infra
- Design system: ask your `<slug>-design` helper whether the design system (in the design tool and code) covers what we need. Raise big gaps early.
- Auth, permissions and data exposure
- Failure modes: retries, idempotency, partial failure
- Performance and scale: fan-out, heavy queries, async lag
- Observability: how we'll know it works in production
- Rollout: feature flags, backfills, backwards compatibility

## Output

A short technical design, added to the project doc:

- Context (link the project brief)
- Decision
- Options considered (table: option, effort, risk, fit, reversible?)
- Risks and how we reduce them
- Open questions
