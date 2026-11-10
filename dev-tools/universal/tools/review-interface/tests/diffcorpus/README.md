# Diff highlighter regression corpus

Each folder holds `old.<ext>`, `new.<ext>` and `case.json`. Git decides which lines changed; the engine decides which tokens on those lines get a strong highlight.

## case.json

- `strong_must`: `{side, line, text}`. `text` must lie inside a strong span on that line (1-based, line numbers into old/new).
- `strong_must_not`: `{side, line}`. The line must have no strong span.
- `quiet`: the subset of `strong_must_not` lines that are pure noise (re-indent, reflow, comma, moved with scope kept). Lines that mix noise with a real change are only in `strong_must_not` when the noise part is the whole line, never in `quiet`.
- Every must / must_not line is a line `git diff --no-index --histogram` marks as changed (checked at build time). A line git leaves unchanged is never listed.
- Line endings and trailing newline are exactly as stored: `s30` has a CRLF `new` file, `s31` and `s32` lack a final newline, `s44` has an empty `old`.
- Single-file pairs only: cross-file moves (function extracted to another file) cannot be expressed, so they are not covered.

## Prefixes

| Prefix | Count | Origin |
|---|---|---|
| `b` | 16 | Adapted from the difftastic manual "Tricky Cases" page (own words, own code) |
| `o` | 20 | Excerpts adapted and renamed from merged PRs of public MIT repos (`source` has the PR URL) |
| `s` | 40 | Synthetic edge cases written for this corpus, no external source (whitespace, encodings, tokenizer traps, JSX/format noise that is rare in the OSS sample) |

## Pattern tally (public PR diffs)

Sample: the 12 most recent merged PRs of each of vercel/swr, pmndrs/zustand, TanStack/query, colinhacks/zod, pmndrs/jotai, react-hook-form/react-hook-form, radix-ui/primitives (96 PRs, 183 .ts/.tsx files, 451 change blocks). Read via `gh api repos/<repo>/pulls/<n>/files`. Classification is a regex heuristic: counts overlap (a block can match several rows) and are approximate (confidence: MEDIUM). Library repos are light on JSX; the app-style JSX patterns (provider wrap, props) are therefore covered by `s` cases.

| Pattern | Blocks | Cases |
|---|---|---|
| Modified block (lines changed in place) | 259 | most `o`, `s` |
| Added-only block | 186 | o02, o03, o06, o10, o11, o12, o14, o19, o20, b10, b19, s04, s18, s19, s44 |
| Multi-line rewrite (line count changes) | 120 | o01, o04, o08, o09, o12, o13, o17, o18, s07, s08, s22, s40 |
| Single-token swap or rename | 92 | o16, s14, s17, s25, s28, s33, s46, b02, b05, b14 |
| Type annotation change | 84 | o04, o07, o14, o15, s17, s43 |
| Test case added | 62 | o19, o20 |
| Import added or changed | 33 | o01, o03, o11, o16, o17, s11, s12 |
| Guard clause or early return added | 31 | s19, s20, o05, o13, s41 |
| Call statement added | 29 | o02, o06, o12, s36 |
| Comment edit | 28 | b14, b15, o13, o18 |
| String literal change | 15 | s25, s26, s46, b17 |
| JSX edit | 7 | s01-s04, s06, s39, s40, o20 |
| Deleted-only block | 6 | s35, o13 |
| Optional chaining added | 6 | none (a synthetic case was dropped for size; tokenizer treats `?.` like any operator) |
| Async/await change | 4 | s36 |
| Whitespace or reflow only | 1 | s09, s40, o15 |
| Comma or semicolon only | 1 | s09, b08 |

Patterns that are rare in the sample but dangerous (reviewer would miss a real change), covered by design: whitespace inside strings (s25, s26), `return x` split by newline (s20), statement moved out of an if (s21), JSX moved to another parent (s02), swapped function order (s23), moved function with a one-token edit (s24), reflow hiding a value change (s08, o04, o08), trailing comma only (s09, b08), CRLF (s30), no final newline (s31, s32), unicode before a change (s33), very long line (s34), tabs (s29), regex vs division (s28), JSX apostrophes (s06), nested templates (s27), type-only change (s17), deleted-only and added-only blocks (s35, o10), invalid syntax (b20), generic tokenizer files (.js s45, .json s46, .py b09 b17, .css s47, .md s49).

## Benchmarks looked at

| Benchmark | Verdict |
|---|---|
| difftastic manual, Tricky Cases, https://difftastic.wilfred.me.uk/tricky_cases.html | Used. 16 cases `b01`-`b20` (subset), rewritten in TS/JS/Python with neutral names; expectations are ours, the page names the shapes. |
| Alikhanifard and Tsantalis, refactoring-aware AST diff benchmark (arXiv 2403.05939; Defects4J commits plus Refactoring Oracle) | Skipped. Java only, large commits, node-mapping oracle not token highlights. |
| Frick et al., Iterative Java Matcher (2018) and the AST mapping differential-testing study (arXiv 2103.00141) | Skipped. Java projects, no per-token ground truth we can reuse. |
| GumTree ASE 2014 evaluation (jQuery 1.8.0 to 1.9.0) | Skipped. Single-project case study, not a published oracle; would need downloading code. |
| RefactoringMiner oracle | Skipped. Java refactorings; method-level moves across files do not fit a single-file pair format. |

No public JS/TS ground-truth oracle for token-level diff quality was found. Nothing was downloaded or run.

## Known uncertain expectations

Judgement calls, revisit if the engine disagrees: b03 (array dissolved: only the bracket is required), b12 (which old line pairs with the new call is ambiguous, only the removed `if` is required), o08 (old line treated as pure reflow), o13 and s41 (added or removed braces are always strong: dropping braces around 2+ statements changes behaviour), s02 and s21 (moving a line to another parent or out of an if counts as a real change), s20 (`return` newline: the new bare `return` is required), s39 (`&&` to ternary).

## Rule audit cases (r01–r09)

Added to pin the engine's noise rules to the zero-miss goal:

- r01: no-semicolon style, a line starting with `(` `[` `` ` `` `+` `-` `/` joins the line above (ASI), so newline and `;` changes there are strong.
- r02: two statements swapped in the same block change execution order, so a move within one scope is strong unless both are declarations.
- r03: a side-effect import (`import './x'`) moving changes load order.
- r04: in JSX text, a same-line whitespace change next to `{expr}` or a tag changes rendered output.
- r05, r06: indentation is meaning in Python and YAML (and Makefile tabs), so indentation-only changes there are strong.
- r07, r08: a trailing comma is meaningful in Python (tuple) and JSON (invalid), so the trailing-comma rule is JS/TS only.
- r09: a quote-style change with the same string value is formatting, so it can be quiet.
