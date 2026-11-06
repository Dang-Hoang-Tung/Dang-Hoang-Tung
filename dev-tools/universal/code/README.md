# Coding principles

The same rules apply when writing and reviewing code.

## Taste

Code follows the same taste as our language (`~/.claude/skills/universal/principles.md`):

- **Readable and intuitive first.** This beats everything else, including short or clever.
- Then simple, elegant and short wherever possible.
- If making it shorter makes it harder to read, keep it longer.

## Files

Read the files that match the change. Architecture and style apply to every change.

| File              | Covers                                                  |
| ----------------- | ------------------------------------------------------- |
| `~/.claude/skills/universal/code/architecture.md` | Layers, boundaries, ports and adapters                  |
| `~/.claude/skills/universal/code/style.md`        | Naming, simplicity, comments, file size                 |
| `~/.claude/skills/universal/code/types.md`        | Types, schemas, API contracts, naming of types          |
| `~/.claude/skills/universal/code/backend.md`      | Services, errors, DI, handlers, API security            |
| `~/.claude/skills/universal/code/database.md`     | Schema, migrations, queries                             |
| `~/.claude/skills/universal/code/frontend.md`     | UI structure, forms, translations                       |
| `~/.claude/skills/universal/code/design-system.md` | The design system in the design tool and code, checking designs, building components |
| `~/.claude/skills/universal/code/tests.md`        | What to test, which test type, test rules               |

Where an area has workspace conventions, its file ends with a pointer to `~/.claude/skills/workspace/code/`. Follow both.
