# Comms

How our agents work together. Same taste as our language: short, plain, only what the reader needs.

Unclear term? See `~/.claude/skills/universal/glossary.md`. Which tool fills each role (tracker, docs, design tool, chat, code host): `~/.claude/skills/workspace/tools.md`.

## Who talks to whom

```
me ── buddy ──┬── <slug>-tl ──────┬── <slug>-pm        (planning, retro)
              │                   ├── <slug>-design    (planning)
              │                   └── <slug>-dev-<n>   (building)
              ├── <slug>-devit
              ├── team-pe
              └── team-reviewer
```

- Each project works in its own namespace: its slug, its sessions, its project bank. It doesn't touch other projects.
- Shared sessions (buddy, team-pe, team-reviewer) talk only to a project's lead.
- Helpers and sub-agents report to whoever started them.
- Everything reaches me through buddy, unless I'm talking to a session directly.
- How sessions message: `multi-agent.md`. How sub-agents work: `subagent.md`.

## Ground rules

For every persona:

- **Decide inside your role.** Log straightforward decisions in the project's `decisions.md`. Raise unclear ones: send `decision` to buddy. Big product or technical calls are always mine.
- **Waiting on me?** Send `decision` or `blocked` to buddy. I may not be watching your session.
- **Ask the other side.** A product question in a technical role, or the reverse, gets the other persona's view first.
- **Writing outside:**

  | Fine without asking                                     | Ask me first, showing the exact content |
  | ------------------------------------------------------- | --------------------------------------- |
  | Open PRs, push our own branches                         | Create or edit tracker tickets and projects |
  | Reply to and resolve bot review threads                 | Docs pages                              |
  | team-pe's `<tag>/morph/` branches                              | Comments on other people's PRs          |
  | Agent notes on our tickets; move our tickets to Done after merge | Anything in chat               |
  | New draft files in the design tool                      | Editing existing design files           |

- **Cite sources.** Say where a fact came from. Mark guesses as guesses.
- **Stay in scope.** Follow-ups go to the project's `followups.md`. Ideas outside any project go to buddy's `ideas.md`.

## Files

```
~/.claude/agent-files/
├── projects/<slug>/
│   ├── README.md        registry: goal, size, lead, helpers (with agent IDs), branches, links
│   ├── project-doc.md   brief, technical design, PR plan (Large: link to the docs page)
│   ├── decisions.md     - YYYY-MM-DD <decision> — <why> (<who>)
│   ├── followups.md
│   ├── handoffs/        <from>-to-<to>-<topic>.md
│   └── notes/<role>.md  each helper's note to itself
└── shared/
    ├── buddy/           daily logs (YYYY-MM-DD.md), ideas.md
    ├── team-pe/         state.md
    └── team-reviewer/   briefs/
```

- Work only in your own project's folder. Shared sessions can read any project, and write to `shared/` and to a project's `handoffs/`.
- Create folders when they're missing. Send paths as plain text.
- Keep files short and current.

## Efficiency

- Send summaries, not transcripts. Link instead of pasting.
- Load only what you need, when you need it.
- Waking a finished helper reloads its whole context. Batch what you send it.
