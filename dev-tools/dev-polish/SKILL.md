---
name: dev-polish
description: Guides on getting a PR ready for merging
---

This is a guide to polishing a PR so that we clean up nitty problems and bring it to a ready state for production.

Steps:

- Make sure you are on the correct git branch
- Check CI status for any failures, resolve if you can (ignore things like Meticulous)
- Fetch all unresolved PR reviews
- Check if they are valid issues against our codebase. Especially for bot reviews, check if the claim is actually practical and significant
- If the issues relate to past decisions, summarise the decision very concisely for me, and identify the pros and cons of our approach vs the suggestion
- If the fix is clear, go ahead and implement
- If you need a decision from me, summarise the problem, and identify the pros and cons of each option
- For bot reviews (Cursor, Cubic, Copilot), you can respond to the comment directly in each review thread and then resolve it.
- For human reviews, let me respond, you can suggest very concisely what I should say
- Always list out the issues and how we're resolving them in a concise numbered list that we can keep track of
- When fixing issues, do it in a new commit on top of the existing code (unless reverting). Then you can still force push and restack other PRs if needed.
