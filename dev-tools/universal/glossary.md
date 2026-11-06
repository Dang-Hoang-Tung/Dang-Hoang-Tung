# Glossary

Terms we use across the skills. Check here when a word is unclear.

## Work

| Term       | Means |
| ---------- | ----- |
| Slug       | Short name for a piece of work, e.g. `x2` or `ab123`. Every session, agent and file for that work starts with it. |
| Project    | Any piece of work with a slug, Small to Large. |
| Size       | **Small**: one clear change, one PR, no new design → team-devit in light mode. **Medium**: a few PRs, or needs a technical design → team-tl. **Large**: needs a product brief or new project design → team-tl with team-pm and team-designer. |
| Light mode | dev-auto stages 2–4 only (code, review, polish), adding others when needed. |
| Follow-up  | Work found along the way that's out of scope. Goes in the project's `followups.md`. team-pm owns them. |

## Who

| Term      | Means |
| --------- | ----- |
| Runner    | A team- persona or buddy. Runs work using the playbooks. |
| Playbook  | A dev- skill: how to do one kind of work (auto, plan, code, review, polish, QA, debug). Runners use them; I can also use them directly. |
| Session   | A long-running Claude Code session. Talks to other sessions (`multi-agent.md`). |
| Lead      | The session that runs a project and talks to other teams for it: `<slug>-tl` or `<slug>-devit`. |
| Helper    | An agent the lead starts for a phase: `<slug>-pm`, `<slug>-design`, `<slug>-dev-<n>`. Reports to the lead. Leaves a note when it finishes. |
| Sub-agent | A short-lived helper for grunt work. Reports back and ends (`subagent.md`). |

## Documents

| Term               | Means |
| ------------------ | ----- |
| Project bank       | The project's folder: `~/.claude/agent-files/projects/<slug>/` (see `comms.md`). |
| Project doc        | The brief, technical design and PR plan. `project-doc.md` in the bank; for Large projects, a docs page linked from the README. |
| Project brief      | team-pm's write-up: problem, users, evidence, options, recommendation. |
| Technical design   | team-tl's write-up: the chosen approach, options considered, risks. |
| PR plan            | team-tl's list of PRs, their order and dependencies. |
| Project design     | The designer's screens for a project or ticket, in the design tool. team-designer reviews them and drafts new ones. |
| Prototype / mockup | team-pm's quick, throwaway version of an idea, built from code. Not a project design. |
| Design system      | Our components, tokens and icons, in the design tool and in code. The design tool is the source of truth. Ours: `workspace/design-system.md`. |

## Code and deploys

| Term        | Means |
| ----------- | ----- |
| Sandbox     | A shared remote environment we deploy to for testing. Ours are in `workspace/stack.md`. |
| Tool roles  | Tracker, docs, design tool, chat, code host, observability, analytics. Which tool is which: `workspace/tools.md`. |
| Integrate   | team-pe combining project branches onto a morph branch, to deploy and test. |
| Morph branch | The throwaway branch team-pe builds each round: `<tag>/morph/<YYYY-MM-DD>-<n>`, main plus the requested branches. Under my own tag, so we never touch other people's branches. |
| Merge       | Merging a PR into main. Always me. |
