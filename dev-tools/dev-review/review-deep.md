# Deep review

Read first:

- `~/.claude/skills/universal/code/architecture.md`
- `~/.claude/skills/universal/code/types.md`
- `~/.claude/skills/universal/code/tests.md`
- If the change touches them: `~/.claude/skills/universal/code/backend.md` `~/.claude/skills/universal/code/database.md` `~/.claude/skills/universal/code/frontend.md`

## Implementation

- Is the main logic correct?
- Are there edge cases or failure modes that aren't handled?
- Is it organised for testability and maintainability?
- Any tight coupling, tangled code, or leaky abstractions?
- Can the design be simpler? Could existing libraries, tools or shared code do the job?
- Could it be more modular, reusable or composable?
- Do functions return values honestly? Is DI used one layer deep? (backend principles)

## Types, contracts, schemas

- Does the change follow the types principles?
- Are types consistent, or duplicated and inconsistent?
- Are any types missing that would add clarity or safety?
- Any type safety or inference issues?

## Tests

- Does the change follow the test principles?
- Is the new code tested? If not, is there a good reason?
- Do the tests cover the important scenarios, edge cases and failure modes?
- Are the tests clear and maintainable?
- Are any tests redundant or trivial?
