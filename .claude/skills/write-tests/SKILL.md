---
name: write-tests
description: Guides on writing tests for code. Use when the user asks "how do I write tests for this code?" or "how do I test this functionality?"
---

<!-- Reference Content -->

# Principles

- **Tests are product code**: They deserve thoughtfulness and care.
- **Fewer tests, better tests**: Not everything needs a unit test. Focus on leverage.
- **Fast feedback loops**: A good test runs quickly and fails clearly.
- **Architecture drives testability**: Code that’s hard to test is usually hard to change.
- **Test where it hurts**: Prioritise areas of complexity, churn, and risk.
- **Realism over mocking**: Integration tests are often more valuable than over-mocked units.

<!-- Task Content -->

# What type of test to write?

| Decision hint                             | Suggestion                                                                |
| ----------------------------------------- | ------------------------------------------------------------------------- |
| Testing business logic?                   | Write a **unit test** with real inputs/outputs                            |
| Testing side effects or IO boundaries?    | Write an **integration test** with real/fake adapters                     |
| Testing across DB/API/UI boundaries?      | Write an **E2E test** with realistic scenarios                            |
| Testing a single React component or hook? | Write an **integration-style RTL test**                                   |
| Writing a test with 5+ mocks?             | ❌ Consider you're over-mocking. Use fakes or test a higher layer instead |
| Testing "Does this system work?"          | ➡️ **E2E**                                                                |
| Testing "Does this logic work?"           | ➡️ **Unit/Integration**                                                   |

# Best practices

When writing any test:

- **Use existing patterns**: Follow established conventions and patterns in your codebase.
- **Arrange-Act-Assert**: Structure tests clearly with setup, execution, and verification phases.
- **One assertion per test**: Focus on one behavior per test for clarity and maintainability.

When writing integration tests:

- Create and clean up seed data for the test environment
- Use real implementations for as many dependencies as possible
- Test the public API of the module, not internal implementation details
- Focus on testing the "happy path" and key edge cases, not every possible branch
