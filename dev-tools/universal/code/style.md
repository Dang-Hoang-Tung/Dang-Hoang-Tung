# Code style

## Naming

- Follow the existing convention, or the newest pattern we're moving to, for functions, variables, files and folders.
- Pick simple, obvious names over clever ones.

## Less is more

- Write the least code that solves the problem. Remove redundant code.
- No abstractions for single-use code.
- No flexibility or config that nobody asked for.
- Use existing libraries, tools and shared code before building your own.
- Keep logic readable and idiomatic for the language.

## Comments

- Don't write a comment unless you can justify it. Code should explain itself.
- Remove redundant comments. Keep the rest as short as possible.

## Files

- Keep files under 500 lines, but don't split out a file for one tiny function.
- When a file grows, group helpers and split by domain layer.
