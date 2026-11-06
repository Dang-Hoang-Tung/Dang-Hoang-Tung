# Design

A local PR review app. Python 3.9 stdlib on the server side, vanilla JS and CSS in the browser, no build tooling.

## Rule

- **Logic** (`app/services`, `app/server`, `app/cli.py`, `app/config.py`) never produces HTML.
- **UI** (`app/ui`) never touches GitHub, git, the network or state files. It turns **view models** (plain dicts, below) into markup, plus static CSS/JS.
- `app/services/build.py` is the only place that joins the two: it gathers data, builds view models, calls the UI, and writes files.

## Layout

```
review.py                       entrypoint: from app.cli import main
config.json
app/
  config.py                     load_config, defaults, data dirs, slug()
  domain.py                     SEVERITIES, SEVERITY_LABELS, LAYERS, worst(): shared by logic and UI, pure data
  cli.py                        build | serve | paths | ai list/reply/post
  services/
    shell.py                    run(): subprocess with a timeout; the only place gh and git are spawned
    github.py                   list_pending, requested_at, ci_state, fetch_api_diff, post_comment (all gh calls)
    git.py                      fetch PR refs into refs/review/*, diff base...head
    diff.py                     parse_diff, generated detection, layer_of, file hash
    tree.py                     build_tree (nested), layout(tree, stats) -> geometry (no SVG)
    insights.py                 schema, validate, load (missing/current/stale/invalid)
    adapters/team_reviewer.py   markdown brief -> insights; sync_briefs
    state.py                    load/save (atomic), per-slug file lock, merge (validated), waiting_threads
    posting.py                  post_body, post_thread (posting marker, per-message idempotency; uses github.post_comment)
    models.py                   review_model(), queue_model(): build view models from data
    manifest.py                 write/read manifest.json
    build.py                    orchestrates a build; a partial build merges into the existing manifest
  server/
    http.py                     local helper: auth, static pages, state API, post API, idle stop
  ui/
    html.py                     esc, attrs helpers, svg_icon
    markdown.py                 md_inline, md_block, md_list (escape first)
    assets.py                   bundle(css_files), bundle(js_files): concatenates static files in order
    components/
      appbar.py  banner.py  tree_svg.py  summary_card.py  file_section.py  icons.py
      left_panel.py  right_panel.py  modals.py  fabs.py
      queue_controls.py  queue_bucket.py  queue_item.py
    pages/
      review_page.py            render(model) -> html
      queue_page.py             render(model) -> html
    static/
      themes.js                 theme families (loaded in <head>)
      css/   tokens.css base.css appbar.css layout.css left-panel.css canvas.css diff.css
             cards.css dropdown.css right-panel.css threads.css modals.css queue.css
      js/    shared/dom.js shared/markdown.js shared/time.js shared/theme.js shared/dropdown.js
             review/data.js review/store.js review/read-state.js review/files.js review/left-panel.js
             review/scroll-spy.js review/tree-canvas.js review/modals.js review/treemap.js
             review/selection.js review/checks.js review/threads.js review/resizers.js review/main.js
             queue/filters.js queue/main.js
tests/
```

JS files for a page are concatenated in the listed order and wrapped in one IIFE, inlined into the page. They share that scope; only `main.js` runs boot code. Pages work opened from disk (read-only) or through the helper (saving).

## View models

### Review page (`models.review_model`)

```python
{
  "pr": {"repo", "number", "slug", "title", "url", "author", "head_sha", "base", "draft": bool, "ci": "passing|failing|pending|none"},
  "user": "Tony", "ai_name": "Claude",
  "layers": [layer names, from domain.LAYERS],
  "files": [{"idx", "path", "a", "d", "gen": bool, "binary": bool, "layer", "hash", "kind": "block|should|nit|question|look|None",
             "notes": [note keys], "rows": [[kind, old_no|None, new_no|None, text], ...]}],   # kind: hunk|add|del|ctx
  "order": [file idx in display order],
  "tree": [{"name", "file": idx|None, "kids": [...]}],          # top-level nodes under the repo root, for the left panel
  "tree_layout": {"width", "height",
                  "nodes": [{"x", "y", "w", "h", "cx", "label", "title", "file": idx|None, "role": "root|dir|leaf",
                             "kind": str|None, "gen": bool, "a", "d", "notes": int}],
                  "edges": ["M.. V.. H.." path strings]},
  "notes": [{"key", "kind", "title", "body", "comment", "file": idx|None, "start", "end", "rows": [row ids], "endRow"}],
  "summary": {"has_insights": bool, "verdict", "risk", "risk_note", "minutes", "minutes_source": "insights|estimate",
              "tldr": [md], "questions": [md], "description": md|None},
  "totals": {"added", "deleted", "files", "added_all", "deleted_all", "effort": "Small|Medium|Large"},
  "banners": [{"type": "draft"} | {"type": "stacked", "base"} | {"type": "stale", "from", "to"} | {"type": "invalid", "reason"}],
}
```
Row ids are `r{file idx}-{row index}`. A binary file has `binary: true` and no rows. `summary.verdict` is already shortened (first sentence, 40 characters); avatars come from `models.avatar_url`.

### Queue page (`models.queue_model`)

```python
{
  "user": "Tony",
  "total_minutes": int,
  "authors": ["alice", ...],                     # for the filter
  "buckets": [{"author", "avatar": url, "items": [item, ...]}],   # authors A-Z (case-insensitive), items oldest request first
}
item = {"slug", "number", "title", "url", "author", "requested_at": iso, "head_sha", "ci", "draft", "effort", "minutes",
        "minutes_source", "added", "deleted", "files", "verdict", "risk", "findings": {kind: n},
        "has_insights": bool, "threads": int, "open_threads": int,
        "summary": {"tldr", "questions", "description"}}
```

## Server API (helper)

- `GET /?t=<token>&next=<page>`: sets the session cookie, redirects.
- `GET /<page>.html`: pages from `<data_dir>/pages`.
- `GET|PUT /api/state/<slug>`: read; merge-and-save.
- `POST /api/post/<slug>` `{threadId, messageId?}`: post to GitHub, returns `{posted, state}`.
- `GET /api/ping`.
All but ping and the token link need the cookie; writes (PUT/POST) need `Origin` equal to `http://<Host>` and `Content-Type: application/json`; bodies over 2 MB get 413; Host must be 127.0.0.1/localhost. `POST /api/post` answers 409 for "already posting" and for a comment written on an older commit. Unexpected errors return JSON 500.
