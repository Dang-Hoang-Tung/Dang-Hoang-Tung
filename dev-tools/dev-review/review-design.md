# Design review

Only for changes that touch the UI. `team-designer` can run this.

Read first: `~/.claude/skills/universal/code/design-system.md`

## Against the design

- Find the project design (usually linked on the ticket or project). If there isn't one, say so.
- Compare the UI with it: layout, spacing, typography, colours, icons, copy.
- Are all states covered: empty, loading, error, disabled?
- If the app is running, compare screenshots. Otherwise compare the code with the design's frames.

## Against the design system

- Check every component, token and icon used or added (see "Check it matches" in the design system).
- Any overridden component styles, hardcoded values or global `data-…` styles?
- Are new components open and composable, or locked down?

## Gaps

- Small differences: list them.
- Big gaps: say which side looks wrong, the design tool or code, and suggest the fix (see "Check it matches" in the design system).
