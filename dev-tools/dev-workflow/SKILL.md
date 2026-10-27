---
name: dev-workflow
description: Guides on the whole development cycle - always refer to this file whenever developing.
---

# IMPORTANT: How we work together

## Our working language

As we go through the dev cycle, you should explain things in a simple and plain language. Avoid long explanations or complex jargon. You can use this file as a reference for the language style we want to use. In general, explain things in as little words as possible. Remove all mannered prose. I prefer a paragraph over an essay, and a sentence over a paragraph where applicable.

## Work visibility

I hate not knowing what you're doing, always ensure:

1. You tell me what you're about to do before you do it, especially before writing code, so I can correct you if necessary (you don't have to wait for my approval)
2. You always summarise what you did after you finish a task, and link to the code files you modified.
3. Output a standalone PRs section (related to the current chat) as a numbered list at the end of every message. The format is `1. [#1](<PR link>) - <branch name>`.

Do these things as concisely as possible.

# Workflow process

Start a development cycle, here's the order in which we will apply our skills, in stages:

- Stage 1. Understand the task: /dev-plan and /dev-explore
- Stage 2. Implement the code: /dev-code
- Stage 3. Review the code: /dev-review
- Stage 4. Polish the PR: /dev-polish
- Stage 5. Help me QA: /dev-qa
- Stage 6. Incremental merge: /dev-merge
- Stage 7. Follow-up opportunities: /dev-opportunities

Only load skills when we start each stage.
Keep a running decisions log - this should be very minimal.
At the end of each stage, run /compact skill.

Not all dev cycles will need stage 5, if it's a minor change and our tests have covered sufficiently, we can skip.

You have 2 modes:

- Auto mode (default): after stage 1, run through the stages automatically from stage 2 to stage 4, and I will only intervene if I need to. Stage 5 and 6 will always require my attention.
- Manual mode: I will tell you when to move to the next stage, and you will wait for my instructions.

# Agent orchestration

- For all stages, you act as the orchestrator, having all the context for the entire dev cycle. You will coordinate Sonnet sub-agents to do the work for you.
- Stay quick and nimble, spin up multiple agents if the work can be parallel.
- Provide the context and task to sub-agents in a simple and efficient manner.
- You lightly check the code written by sub-agents to ensure quality. (we have review stage, so no need for deep reviews unless we're in review stage)
- For every decision that seems worth a revisit, keep in a short list as extra context for the review stage.

IMPORTANT REGARDING USAGE LIMITS:

- Never run "monitor" or "watch" tasks, don't keep anything alive for extended periods.

# Development core principles

- Minimal changes: Be ruthlessly minimal about what we're doing, contain changes to only what's necessary.
- Any tangental changes should be raised with the user and most likely added to a Linear ticket as follow-up work.

# Git strategy

When working on a Linear ticket, the git branch name should be `{user tag}/{ticket ID}/{title}/{subpart (optional)}`. Examples:

- tonyd/ar-1234/example-feature
- tonyd/ar-5678/example-feature/frontend (subpart)
- tonyd/ar-5678/example-feature/backend (subpart)

IMPORTANT: Prefer to make multiple small PRs with easy-to-digest changes rather than big PRs.

When rebasing PR stacks, use `rebase --onto` to move the commits cleanly.
You are allowed to force-push PRs after rebasing/resetting.

# PR guide

At any point from /dev-code stage forward, you can start to open PRs. Guidelines:

- Name the PR concisely, open as "ready for review"
- Do not tag any reviewers yourself
- "Overview" section: Write one simple paragraph of description for the PR, explaining the changes and the reasoning behind them (same working language style).
- "Links" section: list Linear tickets, Figma designs, Notion docs, Slack threads, related PRs, or any other links
- "Show Us" section: Leave this blank as I will fill it
