# Review reference — recurring, reviewer-catchable issues

Concrete things reviewers repeatedly flag on this codebase. Skim the section(s) matching the change and check each bullet against the diff.

## Frontend
- Don't override design-system component styles (margin/padding/gap/`textTransform`); use the component's defaults or a design-system component. If defaults don't match the design, raise it with design — don't hand-roll.
- Use theme colour tokens (`color="secondary"`), never hardcoded colour values.
- Omit `variant` on `TextField`/inputs — use the default.
- Manage form state/validation with formik (errors on touch/submit), not ad-hoc `useState` — consistent with the rest of the app.
- Keep the submit button enabled and validate on click; don't disable-until-valid.
- Surface constraints/limits in the UI; template counts from the constant, no magic numbers in copy.
- Drive conditional UI off the data (`count > 0`), not an unrelated prop (e.g. presence of `onEdit`).
- Extract shared components rather than copy logic (picker + its missing-item handling, etc.).
- Mark required fields with the standard required indicator (asterisk).
- Hide an empty tab/section entirely instead of rendering an empty state.
- Use `useTranslation(..., { keyPrefix })` instead of repeating the prefix on every key.
- MSW: put common handlers in the shared default mocks; `server.use(...)` per-test only for specifics. Prefer shared setup (jest-launchdarkly-mock, global MSW) over re-mocking.
- Never commit local editor config (`.vscode/settings.json`, themes) into a PR.
- Don't ship a FE that reads a new BE field before the BE ships (split deploys).

## Backend
- Guard malformed persisted/jsonb config: default missing fields (`policyIds = []`) so a bad row can't throw.
- Fail loud when required context can't be produced; don't silently proceed against missing/partial data.
- Keep an adapter change-coupled with the data it wraps (data owner owns the read + the provider); the consumer owns pulling ids out of its own config.
- Decouple services via structural typing at the wiring seam — don't import a consumer's types into a data-owner service (or vice versa); a provider declares its own return type referencing only shared vocabulary.
- One-layer dependency injection: build the full dependency object outside and pass it in; don't thread deps-of-deps.
- Use proper error constructors (`NotFoundError`, `UnknownServerError`), not `new Error`.
- Bound fan-out (cap counts) and dedupe expensive work (OCR/DB) within a call.
- Event/queue handlers must be idempotent under at-least-once delivery (guard replays: row lock / compare-and-set / idempotency check).
- Sensitivity/leak class: the producer labels it; the consumer enforces audience rules; never leak internal-only context to an external audience (e.g. suppliers).

## Database
- Filter `deleted_at IS NULL` (and terminal-state columns) on soft-deletable tables.
- Add a deterministic tie-breaker (e.g. `id`) after `ORDER BY` whenever using `LIMIT`/`limit(1)` or returning an ordered list.
- Migrations must be lock-safe (timeouts on backfills, FK `NOT VALID` then validate, `CONCURRENTLY`/`IF [NOT] EXISTS`); new org-scoped tables need RLS + a composite `(organisation_id, …)` index.

## API & contracts
- Assert authorization in the handler before doing work; scope every read/write by the owning id; never trust a client-supplied id.
- i18n: additive keys only — never edit an existing en-fallback value (Lokalise overrides it). Professional wording; match product vocabulary.
- Remove dead package exports (`yarn validate-exports`) — don't export what nothing imports across packages.
- Schema changes via declarative desired-state + codegen; regenerate OpenAPI on API change.

## Types & naming
- One noun per concept; avoid near-collision names (`ContextSlice` vs `SliceContext`).
- Enums: use standard, ordered vocabularies (e.g. `PUBLIC | INTERNAL | RESTRICTED`); rename values 1:1 and update every consumer (incl. other teams' code that reads the shared enum).
- Prefer a generic type parameter over baking a specific consumer's shape into a shared type.
- Keep a classification/flag static and declared where a consumer can read it *before* acting (input gating), not only in the output.
- Functions should return values honestly — don't throw inner state the caller must collapse into a value.

## Tests
- Add a regression test when fixing a bug (cover the missing business case).
- Reuse fixtures/seeders; don't inline large literals; don't assert loggers; test business behaviour, not implementation.
- `await` async UI actions (formik submit) via `findBy*`/`waitFor` — never assert synchronously right after an async action.

## Git / PR hygiene
- Keep the PR description current: naming, stacking, removed flags, behaviour.
- After a base PR squash-merges, rebase `--onto main <old-base> <branch>`, keeping only that branch's own commits; retarget the PR base.
- Keep local/editor files and unrelated churn out of the diff.
