# Tests

Testable code comes from good design, not cleanup afterwards. Build with clear boundaries and no tangled dependencies.

## Mindset

- Fewer, better tests. Not everything needs a unit test.
- Tests run fast and fail clearly.
- Hard-to-test code is hard-to-change code. Fix the design, see `~/.claude/skills/universal/code/architecture.md`
- Test where it hurts: complex, often-changed and risky areas.
- Prefer real code over mocks. Integration tests often beat over-mocked unit tests.

## Which test to write

| You're testing                 | Write                                           |
| ------------------------------ | ----------------------------------------------- |
| Business logic                 | **Unit** test with real inputs and outputs      |
| Side effects or I/O boundaries | **Integration** test with real or fake adapters |
| Across DB, API and UI          | **E2E** test with realistic scenarios           |
| One UI component               | **Integration-style** component test            |
| "Does the system work?"        | **E2E**                                         |
| "Does this logic work?"        | **Unit** or **integration**                     |

5+ mocks in one test means you're over-mocking. Use fakes or test a higher layer.

## All tests

- Follow existing test patterns and the stack's standard test library.
- Structure as Arrange, Act, Assert.
- One behaviour per test.
- Test business behaviour, not implementation. Assert on results, not internal calls.
- Fakes and test doubles implement the same port interface as the real thing.
- Reuse fixtures and seeders. Don't inline large literals.
- Don't assert on loggers.
- When fixing a bug, add a regression test for the missed business case.
- Cover new code, its edge cases and failure modes. Drop redundant or trivial tests.

## Unit tests

- Test domain services and models directly with realistic inputs and outputs. No mocks.
- Use in-memory fakes where a dependency is needed.

## Integration tests

- Test the module's public API through a real use case (e.g. "approve an order") with real domain code and fake or real ports.
- Use real implementations for as many dependencies as possible (e.g. a mocked network layer, a database in Docker).
- Create and clean up seed data.
- Cover the happy path and key edge cases, not every branch.

## UI tests

- Test logic separately from the UI.
- Test behaviour the user sees, not implementation details.
- Put common network mocks in shared defaults. Override per test only for specifics.
- Wait for async UI actions to settle before asserting. Never assert right after an async action.

Workspace conventions: `~/.claude/skills/workspace/code/tests.md`
