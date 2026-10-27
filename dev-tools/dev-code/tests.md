# Testing principles

The architecture of a system _dictates_ how testable it is. Well-structured systems aren’t just easier to test - they’re easier to evolve, scale, and trust. We aim to build **testable systems by design**, not by accident or cleanup. This means designing **with boundaries**, **for clarity**, and **against entanglement**.

- **Fewer tests, better tests**: Not everything needs a unit test. Focus on leverage.
- **Fast feedback loops**: A good test runs quickly and fails clearly.
- **Architecture drives testability**: Code that’s hard to test is usually hard to change.
- **Test where it hurts**: Prioritise areas of complexity, churn, and risk.
- **Realism over mocking**: Integration tests are often more valuable than over-mocked units.

## What type of test to write?

| Decision hint                             | Suggestion                                                                |
| ----------------------------------------- | ------------------------------------------------------------------------- |
| Testing business logic?                   | Write a **unit test** with real inputs/outputs                            |
| Testing side effects or IO boundaries?    | Write an **integration test** with real/fake adapters                     |
| Testing across DB/API/UI boundaries?      | Write an **E2E test** with realistic scenarios                            |
| Testing a single React component or hook? | Write an **integration-style RTL test**                                   |
| Writing a test with 5+ mocks?             | ❌ Consider you're over-mocking. Use fakes or test a higher layer instead |
| Testing "Does this system work?"          | ➡️ **E2E**                                                                |
| Testing "Does this logic work?"           | ➡️ **Unit/Integration**                                                   |

## Best practices

All tests:

- **Use existing patterns**: Follow established conventions and patterns in your codebase.
- **Arrange-Act-Assert**: Structure tests clearly with setup, execution, and verification phases.
- **One assertion per test**: Focus on one behavior per test for clarity and maintainability.
- Use test doubles or fakes via the same port interface.
- Avoid mocking internals - test real flows.
- Use the standard testing library for your language/framework (e.g. Jest, Pytest, JUnit).

Unit tests:

- Unit test domain services and models using realistic inputs/outputs - no mocks needed.
- Use in-memory fakes for unit tests.
- Test pure logic directly and cheaply.

Integration tests:

- Create and clean up seed data for the test environment
- Use real implementations for as many dependencies as possible
- Test the public API of the module, not internal implementation details
- Focus on testing the "happy path" and key edge cases, not every possible branch
- Use real adapters in integration/E2E tests (e.g. MSW, Docker DBs).
- Integration test use cases like “approve vendor” with real domain and fake ports.
- Assert on behavior, not internal calls.
- Validate effects with adapter tests or E2Es.

UI tests:

- Test logic separately from UI.
- Use RTL for behavioural tests, not implementation details.
