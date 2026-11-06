# Design system

Our design system lives in two places: the design tool (the design) and code. **The design tool is the source of truth.**

Which design system, and where its files live: `~/.claude/skills/workspace/design-system.md`. How to use the design tool: `~/.claude/skills/workspace/tools.md`.

## Check it matches

Three things should match:

```
Project design  →  Design system in the design tool  →  Design system in code
```

For every component, token and icon in the change:

1. **Project design → design tool**: does the design system in the design tool have it?
2. **Design tool → code**: does the code have it, and does it look and behave the same?

A "no" to either is a gap.

- **Small differences** (a pixel, a slightly different shade): note them and carry on.
- **Big gaps** (missing component or token, clearly different look or behaviour): stop and tell me. Say which side you think is wrong, why, and suggest the fix:
  - **The design tool is wrong or missing it**: I'll get the designer to fix it. Give the file, a link to the exact node or frame if you can find it, and what's wrong in a sentence.
  - **Code is wrong or out of date**: suggest the code fix. Give the file, the component or token, and what to change.

## Building

- Use the design system's components, styles and themes.
- If the design tool has it and code doesn't, add it to code as part of the work. That's in scope, not tangential.
- Don't override design-system component styles. If the defaults don't match the design, it's a gap. Don't hand-roll.
- Use theme tokens, never hardcoded values.
- No global styles as `data-…` attributes. Build the style into a component and use the component.
- Be pragmatic, not strict atomic design. Build components **open**: composable with other components (children, slots) rather than locking down the API and building everything inside.
