# Brief format

```
# PR #<n> — <title>
<link> · <author> · +<add>/−<del> in <files> files · CI: <passing|failing|pending>

## 30 seconds
- What & why: <one sentence>
- Verdict: Approve | Approve with nits | Request changes | Needs a conversation
- Time needed: ~<N> min — <why>
- Risk: Low | Medium | High — <what could break>

## Look here
1. `<file>:<lines>` — <why it needs a human>
Safe to skim: <generated files, renames, fixtures, lockfiles>

## Findings
🔴 Blocking · 🟡 Should fix · ⚪ Nits (max 5)
**<title>** — `<file>:<line>` · HIGH|MEDIUM
<what's wrong, and what triggers it>
> Comment: <polite, specific, ready to paste>

## Tests
<what's covered, what's missing, would they catch a regression?>

## Questions for the author
```

Write "None." for empty sections. Don't pad. One "Should fix" can still be "Approve with nits" if it's small and safe to fix after merging.
