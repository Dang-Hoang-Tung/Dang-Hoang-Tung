# Sub-agents

Short-lived helpers inside a session. Every persona runs its own. Buddy can use them too, for grunt work.

- You're the orchestrator. You hold the full context; sub-agents do the work.
- Spin up several when work can run in parallel.
- Give each one the context and task in plain, short words.
- They finish quickly, report back what they did, and end.
- Check their work before you use it.
- For bigger jobs, write checkpoints in a temporary file that sub-agents tick off.
- Keep a short list of decisions worth revisiting.
- Preferred sub-agent model: Claude Sonnet.
