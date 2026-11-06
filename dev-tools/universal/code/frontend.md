# Frontend

## Structure

- State and data flow top down.
- Props passed through components that don't use them are a sign you need a shared context.
- Components render props and wire events. No domain logic in components, effects or event handlers.
- Data fetching and side effects go in hooks (or the framework's equivalent) or services. Use them for complex queries or reuse.
- Use plain stateless functions for complex data changes or shared logic.
- Extract shared components instead of copying logic (e.g. a picker and its missing-item handling).
- Drive conditional UI off the data (`count > 0`), not an unrelated prop (e.g. whether `onEdit` exists).

## Styling

Follow the design system: `~/.claude/skills/universal/code/design-system.md`

## Forms

- Manage form state and validation with the codebase's form library (errors on touch or submit), not ad-hoc state.
- Keep the submit button enabled and validate on click. Don't disable it until valid.
- Mark required fields with the standard required marker.
- Show constraints and limits in the UI. Pull counts from the constant, no magic numbers in copy.

## Content

- Hide an empty tab or section entirely instead of showing an empty state.
- Translations: only add keys. Never edit an existing fallback value. Use professional wording that matches product vocabulary.

Workspace conventions: `~/.claude/skills/workspace/code/frontend.md`
