# Review views

Small tools that turn a PR into a picture, so you can see its shape before reading the diff. Each one writes a single HTML file you can open anywhere: no server, no state, Python 3.9+ stdlib only.

| Tool | Shows |
|---|---|
| `code_tree.py` | Where the change lands, folder by folder, with lines changed and notes per file. Pan, zoom, collapse folders. |
| `treemap.py` | Every file as a box sized by lines changed, coloured by its most serious note. |

Clicking a file opens it in the PR's diff on GitHub.

## How to use

```
python3 code_tree.py owner/repo#123 --open
python3 treemap.py https://github.com/owner/repo/pull/123 --open
python3 code_tree.py main...HEAD --repo ~/code/app -o tree.html
```

- **Source**: a PR (`owner/repo#123` or its URL, needs `gh` signed in) or a git range in a local repo (`--repo`, default the current folder).
- **`--notes FILE`**: colour files by review notes. JSON, either a list of `{"path", "severity", "title"}` or a review-insights file (`recommendations`). `severity` is `block`, `should`, `nit`, `question` or `look`. `path` can be a full path or a unique file name.
- **`-o FILE`**: where to write (default `code-tree.html` / `treemap.html`). **`--open`**: open it in the browser.

Lockfiles and other generated files are marked (dashed outline, striped box) and capped in the treemap, so they don't drown the real change.

## For agents

During a review, write the views next to the brief and link them:

```
python3 ~/.claude/skills/universal/review/code_tree.py owner/repo#123 --notes notes.json -o <briefs>/<repo>-<pr>-code-tree.html
```

Write `notes.json` from your verified findings, so the views show the same severities as the brief.

## Files

| File | What |
|---|---|
| `pr_files.py` | Loads the files a change touches (+/−, status, generated) and attaches notes |
| `page.py` | Shared HTML shell: colours (follows light or dark mode), legend, file icons, GitHub file links |
| `code_tree.py`, `treemap.py` | The views |
| `tests/` | `python3 -m unittest discover -s tests` |

Taken from the AI review app (github.com/Dang-Hoang-Tung/AI-review-app), which has the full interactive version.
