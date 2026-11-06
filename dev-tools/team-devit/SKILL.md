---
name: team-devit
description: Runner and lead for Small projects (light mode). Use to ship a small, clear change, like a bug fix or tweak, as one PR: code, review, polish, adding other stages only when needed. To find a bug's cause first, it uses the dev-debug playbook.
---

@~/.claude/skills/universal/comms.md
@~/.claude/skills/universal/multi-agent.md
@~/.claude/skills/universal/subagent.md

# Dev-it

You get small, clear work shipped fast. You lead it, in session `<slug>-devit`. The slug is usually the ticket ID, e.g. `ab123`.

## Start

1. **No ticket?** Draft one (short, plain, with acceptance criteria) and send it to buddy as a `decision`. Start once I've said yes.
2. Create the project bank: `python3 ~/.claude/skills/universal/scripts/project-new.py <slug> --lead <slug>-devit --size Small --goal "<one line>" --apply`. Send `register` to buddy.

## Light mode

Run dev-auto stages 2–4: `/dev-code` → `/dev-review` → `/dev-polish`.

Add a stage only when the work needs it:

| Stage             | Add it when                                                         |
| ----------------- | ------------------------------------------------------------------- |
| `/dev-debug`      | It's a bug and the cause isn't clear yet                            |
| 1. `/dev-plan`    | The code is unfamiliar, or there's more than one sensible approach  |
| 5. `/dev-qa`      | The change affects behaviour that tests don't cover. You send `integrate` to team-pe. |
| 7. Retro          | Something went wrong that's worth learning from                     |

I merge. You get the PR ready. Once it's merged, send `done` to buddy and team-pe.

## Too big?

If it needs more than one PR, or a technical design, stop and tell buddy (`blocked`). It becomes a Medium project for team-tl.
