# Database

## Schema

- Design clean, extensible schemas first. APIs and types follow from them, see `~/.claude/skills/universal/code/types.md`
- Change schemas through declarative desired state and codegen.
- New tenant-scoped tables need row-level security and a composite index that starts with the tenant id.

## Migrations

- Migrations must be lock-safe: timeouts on backfills, add constraints without a full lock and validate them after, build indexes without blocking, and make them safe to re-run.
- For data moves (not schema changes), the developer can also run SQL directly against the databases.

## Queries

- Filter out soft-deleted rows (and terminal states) on soft-deletable tables.
- Add a tie-breaker (e.g. `id`) after `ORDER BY` when using `LIMIT` or returning an ordered list.

Workspace conventions: `~/.claude/skills/workspace/code/database.md`
