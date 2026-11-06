# Types, schemas, APIs

## Source of truth

- Order: DB schema first, then the API, then in-code types built from both.
- Declare a type where it's produced. Import it where it's consumed. Don't redeclare it.
- Derive types from their source. The main type is the source, smaller types build on it (e.g. `ChairInput` derives from `Chair`).
- Define variants of a base type explicitly, not generated dynamically.
- Don't widen another module's API just to share a type.
- Know which file owns each type, schema and API definition.
- Prefer a generic type parameter over baking one consumer's shape into a shared type.

## Precision

- No loose types (`any`, `object`, `dict`, `unknown`) when a specific type exists.
- Types cover every case. Not too broad, not too narrow.
- Coerce objects with type guards. Each explicit type gets an `x is T` guard. If types differ by one field (e.g. `type`), one generic guard is fine.
- Constrain schema values tightly (enums, format checks like uuid, min and max bounds, bounded lists), not bare string or number validators. This matters most for request inputs (query, path, body): that's the trust boundary.
- Make it clear whether a schema belongs to the API or the DB, through its file path or variable name.
- Put a classification or flag where a consumer can read it before acting (input gating), not only in the output.

## Naming

- One noun per concept. Avoid near-collisions (`ContextSlice` vs `SliceContext`).
- Datetime fields: a moment in time is `<event>_at` in the DB and `<event>At` in code (`created_at`, `deletedAt`). A calendar date with no time is `<thing>_date` / `<thing>Date`. Avoid `_on`, `_time` and bare names like `deadline`.
- Enums use standard, ordered vocabularies (e.g. `PUBLIC | INTERNAL | RESTRICTED`). When renaming values, rename 1:1 and update every consumer, including other teams' code.

Workspace conventions: `~/.claude/skills/workspace/code/types.md`
