# Brief format

```
# #<n> <title>
<author> · +<add> −<del> · <files> files · CI <passing|failing|pending>

Verdict: Approve | Approve with nits | Request changes | Needs a conversation. <one short reason or condition>
What: <one sentence, what it does and why>
Risk: Low | Medium | High. <what could break, one phrase>
Time: ~<N> min

## Check
1. 🔴|🟡|⚪ <title> — `<file>:<line>`
   <one or two plain lines: what's wrong, what triggers it>
   > <ready-to-paste comment, 2 sentences max>

## Ask the author
- <question>
```

Rules:

- About 15 lines, 25 max. Cut, don't pad.
- Use my language rules: plain, simple words, as few as possible, no jargon.
- Check: 5 items max, worst first. 🔴 blocking, 🟡 should fix, ⚪ nit. Nits only if 3 or fewer, else one line "+N nits".
- Only verified findings. No confidence labels. Guesses go under "Ask the author".
- Ask the author: 3 max.
- Empty section: write "None.".
- One small 🟡 can still be "Approve with nits" if it's safe to fix after merging.
