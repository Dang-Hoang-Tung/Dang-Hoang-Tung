---
name: dev-qa
description: Playbook for interactive QA of a change through the real product: frontend, backend or end to end. Use for "QA this ticket", "test this PR", "check it works".
---

@~/.claude/skills/universal/subagent.md
@~/.claude/skills/workspace/stack.md

# QA

Goal: prove the change works through the real product, the way a user would hit it.

## 1. Set up

Only team-pe deploys.

- Your lead sends team-pe `integrate` with your branch (if you're the lead, you send it). Say if you need the local backend; team-pe decides.
- Wait for `deployed`. Reply `testing`, then test. When you're done, send `tested` with pass or fail.
- team-pe not running? Ask buddy (`blocked`) to get it started.

## 2. Agree the scope

Confirm with me:

- What are we testing? (a ticket, a PR, or the whole branch)
- Frontend, backend, or end to end?
- Do we have the data, or do we need to create it?
- Which scenarios? Usually every happy path, plus the most likely unhappy paths and edge cases.

## 3. Test

1. Map where each part runs, and which datastore or service it reads and writes.
2. Find the exact state the feature needs, including auth, ownership and indirect dependencies.
3. Create that state where the system reads it from. Prefer, in order:
   - reuse and tweak existing data
   - create it through the product UI
   - seed it directly: `python3 ~/.claude/skills/universal/scripts/db.py "<sql>" --apply`, or give me the query
4. Get credentials (see Auth in the stack file). Check the identity and role match the path you're testing.
5. Test cheap, predictable paths first, then expensive or unpredictable ones.
6. Use low-level access (DB, API) for setup and checks. Assert through the real interface.
7. Note what the interface can't show (logs, internal state) and check it another way.

## By type

| Type         | Run                     | How                                                                 | Check                       |
| ------------ | ----------------------- | ------------------------------------------------------------------- | --------------------------- |
| Frontend     | Full stack              | Find the flow and its page. Drive a browser with the browser-automation tool.        | The UI behaves correctly, and screenshots match the design |
| Backend      | Backend services        | Find the endpoints and handlers. Send an example payload (cURL).     | Response, and DB records    |
| End to end   | Full stack              | Trigger the flow through the UI.                                    | UI, and DB records          |

API calls: `python3 ~/.claude/skills/universal/scripts/api.py <METHOD> <service> <path>`. DB checks: `python3 ~/.claude/skills/universal/scripts/db.py "<select>"`.

## 4. Wrap up

1. Summarise what passed, what failed, and what we couldn't check. Send `tested` to team-pe.
2. Decide on cleanup of test data with me.
3. If the whole flow works, offer a **demo snapshot** (see below).

## Demo snapshot

Freezes the working code so I can demo it later. Only if I say yes.

- Create an annotated tag on the branch tip: `git tag -a <name> -m "<what this captures>" <branch-tip>`. It won't move on rebase, and its commits won't be garbage-collected.
- For a PR stack, tag the **top** branch's tip. It already contains the whole stack.
- Keep it local. Push (`git push origin <tag>`) only if I want to share it.
- Restore with `git checkout <tag>` or `git checkout -b demo/<x> <tag>`.
- A tag captures code only. Also note what else the demo needs: sandbox or stage, feature flags, changes in other repos, seeded data.
