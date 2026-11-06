# Backend

## Functions and errors

- Functions return values honestly. Don't throw inner state that the caller has to catch and turn back into a value.
- Use the codebase's typed errors, not a bare generic error.
- Fail loud when required context is missing. Don't carry on with partial data.
- Guard malformed stored config (e.g. JSON columns): default missing fields (`itemIds = []`) so a bad row can't throw.
- Handle real edge cases and failure modes. Skip handling for impossible ones.

## Dependencies

- Inject dependencies to avoid coupling, one layer deep: build the full dependency outside and pass it in. Don't pass dependencies of dependencies.

## Services

- The data owner owns the read and the adapter for its data. The consumer pulls ids out of its own config.
- Decouple services with structural typing at the wiring seam. Don't import a consumer's types into a data-owner service, or the reverse. A provider declares its own return type using only shared vocabulary.
- Sensitive data: the producer labels it, the consumer enforces audience rules. Never leak internal-only context to an external audience.

## Handlers

- Event and queue handlers must be idempotent under at-least-once delivery (row lock, compare-and-set, or an idempotency check).
- Cap fan-out and dedupe expensive work (external calls, DB) within a call.

## API

- Check authorization in the handler before doing any work. Scope every read and write by the owning id. Never trust a client-supplied id.
- Regenerate API specs and generated clients when the API changes.
- Remove dead package exports. Don't export what no other package imports.

Workspace conventions: `~/.claude/skills/workspace/code/backend.md`
