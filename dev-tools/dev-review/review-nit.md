# Nit review

Go through the diff line by line.

## Rule check

- Read `~/.claude/skills/universal/code/style.md` and every principle file that matches the change, listed in `~/.claude/skills/universal/code/README.md`
- Check each rule against the diff. Flag every broken rule with a file and line.
- The principle files list concrete issues reviewers keep flagging on this codebase. Be thorough here.

## Style

- Names that could be clearer.
- Logic that could read more simply.
- Code that isn't idiomatic.
- Redundant code or comments. Comments that could be shorter.
- Files that are too big, or split too small.
