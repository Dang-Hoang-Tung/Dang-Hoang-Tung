# Multi-agent comms

How our sessions and helpers talk to each other.

## Names

| Name                                       | Runner                     | Started by |
| ------------------------------------------ | -------------------------- | ---------- |
| `buddy`                                    | buddy                      | me         |
| `team-pe`, `team-reviewer`                 | team-pe, team-reviewer     | me         |
| `<slug>-tl`                                | team-tl, lead of a Medium or Large project | me, from buddy's prompt |
| `<slug>-devit`                             | team-devit, lead of a Small project | me, from buddy's prompt |
| `<slug>-pm`, `<slug>-design`, `<slug>-dev-<n>` | team-pm, team-designer, dev-auto helpers | the lead |
| `ideas-pm`, `health-tl`, `ds-design`       | team-pm (idea mode), team-tl (health), team-designer (design-system check) | me, from buddy's prompt |

A lead registers with buddy on start, and keeps its helpers' agent IDs in the project README.

## Messaging

- Use `SendMessage`. Find session names with `ListAgents`.
- To reply, copy the `from` of the message you got into `to`.
- A sent message isn't a read message. Don't treat silence as agreement.
- Message on events, not on a timer.

## Types

| Type            | From → to                               | Means |
| --------------- | --------------------------------------- | ----- |
| `register`      | lead → buddy                            | Started. Path to the project README. |
| `ask`           | any → any                               | Need context, or a check-in |
| `status`        | any → whoever asked                     | Reply to a check-in |
| `request`       | lead → helper, or any → a shared session | Do a piece of work. Say where to save the result. |
| `reply`         | any → whoever asked                     | Answer to an `ask` or `request` |
| `blocked`       | any → buddy                             | Stuck |
| `decision`      | any → buddy, and buddy → back           | Need my call. Buddy replies with my answer in Status. |
| `sandbox`       | buddy ↔ team-pe                         | My reservation and its end time, or a warning that it ends soon |
| `integrate`     | lead → team-pe                          | Need an environment for these branches |
| `queued`        | team-pe → lead                          | In the backlog, at position N |
| `update-branch` | team-pe → lead                          | Branch is behind or conflicts with main. Update it, then send `integrate` again. |
| `deploying`     | team-pe → leads included                | Deploy starting: what's in, and where |
| `deployed`      | team-pe → leads included                | Ready to test, with URLs |
| `failed`        | team-pe → leads included, buddy         | Deploy failed |
| `testing`       | lead → team-pe                          | Started testing |
| `tested`        | lead → team-pe                          | Finished testing: pass or fail |
| `done`          | lead → buddy, team-pe                   | Work merged or finished |

## Format

```
<type>: <one-line summary>
Status: <one line>
Blocker: <one line, or none>
Next: <one line>
Need: <what, from whom, or none>
```

Drop lines that say "none". Link to PRs, tickets and files instead of pasting them.
