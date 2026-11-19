"""Shared HTML shell for the review views: colours (light and dark), fonts, legend, file icons."""
import hashlib
import html
import webbrowser
from pathlib import Path

TOKENS = """
:root{--bg:#f6f7f9;--surface:#fff;--text:#161b26;--accent:#2f6bff;--add:#1a7f37;--del:#cf2e2e;
--block:#d1242f;--should:#bf6a02;--nit:#6e56cf;--look:#0a8577;--question:#bf3989;--soft:12%;
--font:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--mono:ui-monospace,"SF Mono",Menlo,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#0b0e13;--surface:#11151c;--text:#e4e8ef;--accent:#7aa3ff;--add:#4cc77a;--del:#f26d68;
--block:#ff6e62;--should:#f0a443;--nit:#a998ff;--look:#46d0bb;--question:#f383c6;--soft:16%;color-scheme:dark}}
:root{--surface-2:color-mix(in srgb,var(--text) 3.5%,var(--surface));--surface-3:color-mix(in srgb,var(--text) 7%,var(--surface));
--line:color-mix(in srgb,var(--text) 8%,var(--surface));--line-strong:color-mix(in srgb,var(--text) 15%,var(--surface));
--text-2:color-mix(in srgb,var(--text) 85%,var(--surface));--text-3:color-mix(in srgb,var(--text) 65%,var(--surface));
--accent-soft:color-mix(in srgb,var(--accent) var(--soft),var(--surface));
--block-soft:color-mix(in srgb,var(--block) var(--soft),var(--surface));--should-soft:color-mix(in srgb,var(--should) var(--soft),var(--surface));
--nit-soft:color-mix(in srgb,var(--nit) var(--soft),var(--surface));--look-soft:color-mix(in srgb,var(--look) var(--soft),var(--surface));
--question-soft:color-mix(in srgb,var(--question) var(--soft),var(--surface))}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 var(--font);display:flex;flex-direction:column;height:100vh}
header{display:flex;align-items:center;gap:16px;justify-content:space-between;padding:12px 20px;border-bottom:1px solid var(--line);background:var(--surface)}
h1{margin:0;font-size:15px;font-weight:600}h1 a{color:inherit;text-decoration:none}h1 a:hover{text-decoration:underline}
.sub{color:var(--text-3);font-size:12.5px}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--text-3);padding:10px 20px;border-top:1px solid var(--line);background:var(--surface)}
.legend>span{display:inline-flex;align-items:center;gap:6px}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block}
.dot.block{background:var(--block)}.dot.should{background:var(--should)}.dot.nit{background:var(--nit)}.dot.look{background:var(--look)}.dot.question{background:var(--question)}
.dot.gen{border:1px dashed var(--text-3)}
.a{color:var(--add)}.d{color:var(--del)}
button{font:inherit;color:inherit;background:var(--surface-2);border:1px solid var(--line-strong);border-radius:8px;padding:4px 10px;cursor:pointer}
button:hover{background:var(--surface-3)}
"""

LABELS = {"block": "Blocking", "should": "Should fix", "nit": "Nit", "question": "Question", "look": "Look here"}

_DOT = 'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"'
_STATUS_MARKS = {
    "added": f'<path d="M8 5v6M5 8h6" {_DOT}/>',
    "deleted": f'<path d="M5 8h6" {_DOT}/>',
    "modified": f'<path d="M8 4.5v4M6 6.5h4M6 11h4" {_DOT}/>',
    "renamed": f'<path d="M4.75 8h6M8.5 5.5 11 8l-2.5 2.5" {_DOT}/>',
}


def esc(text):
    return html.escape(str(text), quote=True)


def status_icon(status, attrs=""):
    mark = _STATUS_MARKS.get(status, _STATUS_MARKS["modified"])
    return (f'<svg class="fstat {esc(status)}" viewBox="0 0 16 16" aria-hidden="true" {attrs}>'
            f'<rect x="1.75" y="1.75" width="12.5" height="12.5" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.4"/>{mark}</svg>')


def file_link(change, path):
    """GitHub's link to a file in the PR's diff, or None for a local range."""
    if not change.get("url"):
        return None
    return f'{change["url"]}/files#diff-{hashlib.sha256(path.encode()).hexdigest()}'


def legend():
    dots = "".join(f'<span><span class="dot {k}"></span>{v}</span>' for k, v in LABELS.items())
    return f'<div class="legend">{dots}<span><span class="dot gen"></span>Generated</span></div>'


def totals(change):
    a = sum(f["a"] for f in change["files"])
    d = sum(f["d"] for f in change["files"])
    return f'{len(change["files"])} files · <span class="a">+{a}</span> <span class="d">−{d}</span>'


def document(change, view, css, body, script=""):
    title = change["title"]
    link = f'<a href="{esc(change["url"])}">{esc(title)}</a>' if change.get("url") else esc(title)
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(view)} · {esc(title)}</title><style>{TOKENS}{css}</style></head><body>'
            f'<header><div><h1>{link}</h1><div class="sub">{esc(view)} · {totals(change)}</div></div>'
            f'<div class="tools" id="tools"></div></header>{body}{legend()}'
            f'{"<script>" + script + "</script>" if script else ""}</body></html>')


def write(text, out, open_it):
    out = Path(out).expanduser().resolve()
    out.write_text(text)
    print(out)
    if open_it:
        webbrowser.open(out.as_uri())
    return out
