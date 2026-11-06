import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.domain import LAYERS  # noqa: E402
from app.ui import assets  # noqa: E402
from app.ui.components import banner, queue_controls, tree_svg  # noqa: E402
from app.ui.markdown import md_block, md_inline, md_list  # noqa: E402
from app.ui.pages import queue_page, review_page  # noqa: E402

OUT_DIR = Path(tempfile.gettempdir()) / "review-interface-ui-test"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SHA = "a1b2c3d4e5f6a7b8c9d0"


def _node(label, role, x, y, w, **extra):
    node = {"x": x, "y": y, "w": w, "h": 42, "cx": x + w / 2, "label": label, "title": label, "file": None,
            "role": role, "kind": None, "gen": False, "a": 0, "d": 0, "notes": 0}
    node.update(extra)
    return node


def tree_layout():
    return {
        "width": 330, "height": 230,
        "nodes": [
            _node("widgets", "root", 125, 0, 90, a=17, d=3, notes=1, kind="should"),
            _node("src/components", "dir", 100, 98, 140, a=17, d=3, notes=1, kind="should"),
            _node("Button.tsx", "leaf", 134, 196, 80, file=0, a=12, d=3, notes=1, kind="should", title="src/components/Button.tsx"),
            _node("schema.ts", "leaf", 134, 248, 80, file=2, a=40, d=0, gen=True, title="src/gen/schema.ts"),
        ],
        "edges": ["M170,42 V70", "M170,70 V98", "M117,140 V217 H134"],
    }


def review_model(**over):
    rows0 = [["hunk", None, None, "@@ -1,4 +1,6 @@"], ["ctx", 1, 1, "import x"], ["del", 2, None, "old <b>line</b>"],
             ["add", None, 2, "new line"], ["add", None, 3, "another"], ["ctx", 3, 4, "end"]]
    files = [
        {"idx": 0, "path": "src/components/Button.tsx", "a": 12, "d": 3, "gen": False, "layer": "UI", "hash": "h0",
         "kind": "should", "notes": ["n1"], "rows": rows0},
        {"idx": 1, "path": "src/components/Button.test.tsx", "a": 5, "d": 0, "gen": False, "layer": "Tests", "hash": "h1",
         "kind": None, "notes": [], "rows": [["hunk", None, None, "@@ -0,0 +1 @@"], ["add", None, 1, "test"]]},
        {"idx": 2, "path": "src/gen/schema.ts", "a": 40, "d": 0, "gen": True, "layer": "Generated", "hash": "h2",
         "kind": None, "notes": [], "rows": [["hunk", None, None, "@@ -0,0 +1 @@"], ["add", None, 1, "gen"]]},
    ]
    model = {
        "pr": {"repo": "acme/widgets", "number": 42, "slug": "acme-widgets-42", "title": "Make the button <great>",
               "url": "https://github.com/acme/widgets/pull/42", "author": "alice", "head_sha": SHA, "base": "main",
               "draft": False, "ci": "passing"},
        "user": "Tony", "ai_name": "Claude", "layers": list(LAYERS), "files": files, "order": [0, 1, 2],
        "tree": [{"name": "src", "file": None, "kids": [
            {"name": "components", "file": None, "kids": [{"name": "Button.tsx", "file": 0, "kids": []},
                                                         {"name": "Button.test.tsx", "file": 1, "kids": []}]},
            {"name": "gen", "file": None, "kids": [{"name": "schema.ts", "file": 2, "kids": []}]}]}],
        "tree_layout": tree_layout(),
        "notes": [{"key": "n1", "kind": "should", "title": "Handle <empty> state", "body": "Use `x` and **bold**",
                   "comment": "Please handle empty.", "file": 0, "start": 2, "end": 3, "rows": ["r0-3", "r0-4"], "endRow": "r0-4"}],
        "summary": {"has_insights": True, "verdict": "Looks good. Minor nits.", "risk": "Low", "risk_note": "", "minutes": 12,
                    "minutes_source": "insights", "tldr": ["Adds a button", "Touches `Button.tsx`"], "questions": ["Why <script>?"],
                    "description": None},
        "totals": {"added": 17, "deleted": 3, "files": 3, "added_all": 57, "deleted_all": 3, "effort": "Small"},
        "banners": [],
    }
    model.update(over)
    return model


def queue_item(number, author, **over):
    item = {"slug": f"acme-widgets-{number}", "number": number, "title": f"Change number {number}", "url": "https://x",
            "author": author, "requested_at": "2026-11-01T10:00:00Z", "head_sha": SHA, "ci": "passing", "draft": False,
            "effort": "Small", "minutes": 8, "minutes_source": "insights", "added": 120, "deleted": 4, "files": 5,
            "verdict": "Looks good", "risk": "Low", "findings": {"should": 2, "nit": 1}, "has_insights": True,
            "threads": 2, "open_threads": 1,
            "summary": {"tldr": ["Does a thing"], "questions": [], "description": None}}
    item.update(over)
    return item


def queue_model():
    return {
        "user": "Tony", "total_minutes": 24, "authors": ["alice", "app/dependabot"],
        "buckets": [
            {"author": "alice", "avatar": "https://github.com/alice.png?size=48",
             "items": [queue_item(1, "alice"), queue_item(2, "alice", has_insights=False, ci="failing", draft=True,
                                                          verdict="", risk="", findings={}, minutes_source="estimate",
                                                          summary={"tldr": [], "questions": [], "description": "Plain <script>alert(1)</script> text"})]},
            {"author": "app/dependabot", "avatar": "https://github.com/dependabot.png?size=48",
             "items": [queue_item(3, "app/dependabot", effort="Large")]},
        ],
    }


def inline_scripts(page):
    return [s for s in re.findall(r"<script>(.*?)</script>", page, re.S)]


class MarkdownTests(unittest.TestCase):
    def test_script_is_escaped(self):
        for out in (md_inline("<script>alert(1)</script>"), md_block("<script>alert(1)</script>"), md_list(["<script>x</script>"])):
            self.assertNotIn("<script>", out)
            self.assertIn("&lt;script&gt;", out)

    def test_blocks(self):
        out = md_block("# Title\n\nA **bold** `code` [l](https://a.b)\n\n- one\n- two\n\n```\n<x>\n```")
        self.assertIn("<h4>Title</h4>", out)
        self.assertIn("<b>bold</b>", out)
        self.assertIn('<a href="https://a.b"', out)
        self.assertIn("<li>two</li>", out)
        self.assertIn("<pre>&lt;x&gt;</pre>", out)

    def test_escapes_html(self):
        out = md_block("hello <script>alert(1)</script> world")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_strips_comments(self):
        out = md_block("before <!-- secret\nmultiline --> after")
        self.assertNotIn("secret", out)
        self.assertIn("before", out)
        self.assertIn("after", out)

    def test_only_http_links(self):
        out = md_block("[ok](https://example.com/x) and [bad](javascript:alert(1)) and [mail](mailto:a@b.c)")
        self.assertIn('<a href="https://example.com/x"', out)
        self.assertNotIn('href="javascript', out)
        self.assertNotIn('href="mailto', out)

    def test_link_cannot_break_out_of_attribute(self):
        out = md_block('[x](https://e.com/"onmouseover="alert(1))')
        self.assertNotIn('"onmouseover', out)

    def test_lists_code_and_headings(self):
        out = md_block("# Title\n\n- one\n- [x] two\n\n```\n<b>raw</b>\n```\n\nSome `code` and **bold**")
        self.assertIn("<h4>Title</h4>", out)
        self.assertIn("<ul><li>one</li><li>two</li></ul>", out)
        self.assertIn("<pre>&lt;b&gt;raw&lt;/b&gt;</pre>", out)
        self.assertIn("<code>code</code>", out)
        self.assertIn("<b>bold</b>", out)

    def test_empty(self):
        self.assertEqual(md_block(None), "")
        self.assertEqual(md_list([]), "")


class BannerTests(unittest.TestCase):
    def test_no_double_spaces_or_space_before_punctuation(self):
        for b in ({"type": "draft"}, {"type": "stacked", "base": "x"}, {"type": "stale", "from": SHA, "to": "ffffffffff"}, {"type": "invalid", "reason": "bad"}):
            text = re.sub(r"<[^>]+>", "", banner.render(b, "Claude"))
            self.assertNotIn("  ", text)
            self.assertIsNone(re.search(r" [.,;:]", text), text)

    def test_wording(self):
        self.assertIn("This PR is a draft.", banner.render({"type": "draft"}, "Claude"))
        self.assertIn("Stacked on <code>feat/x</code>: the diff shows only this PR's own changes.",
                      banner.render({"type": "stacked", "base": "feat/x"}, "Claude"))
        stale = banner.render({"type": "stale", "from": "1234567890", "to": "abcdefabcdef"}, "Robo")
        self.assertIn("Robo insights were written for <b>1234567</b>; the PR is now at <b>abcdefa</b>", stale)
        self.assertIn("The insights file was ignored: bad json.", banner.render({"type": "invalid", "reason": "bad json"}, "Claude"))


class TreeTests(unittest.TestCase):
    def test_svg(self):
        svg = tree_svg.render(tree_layout())
        self.assertEqual(svg.count('class="tlink"'), 2)
        self.assertIn('data-file="0"', svg)
        self.assertIn('rect class="node root should"', svg)
        self.assertIn('node leaf  gen', svg)
        self.assertIn('class="nlabel"', svg)
        self.assertIn("<title>src/components/Button.tsx</title>", svg)
        self.assertIn('viewBox="-2 -2 334 234"', svg)


class DropdownOptionTests(unittest.TestCase):
    def test_bot_labels_and_avatars(self):
        options = queue_controls.author_options([{"author": "alice", "avatar": "A"}, {"author": "app/dependabot", "avatar": "https://github.com/dependabot.png?size=48"},
                                                 {"author": "renovate[bot]", "avatar": "R"}])
        self.assertEqual(options[0], {"value": "", "label": "All authors"})
        self.assertEqual(options[1]["label"], "alice")
        self.assertEqual(options[2]["label"], "dependabot (bot)")
        self.assertEqual(options[2]["value"], "app/dependabot")
        self.assertEqual(options[2]["avatar"], "https://github.com/dependabot.png?size=48")
        self.assertEqual(options[3]["label"], "renovate (bot)")


class ReviewPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = review_page.render(review_model())

    def test_structure(self):
        for needle in ('<header class="appbar">', 'id="treecard"', 'id="treecanvas"', 'id="pane-files"', 'id="pane-layers"',
                       'id="store"', 'id="pcard"', 'id="notelist"', 'id="treemodal"', 'id="mapmodal"', 'id="treemap"', 'id="cbtn"', 'id="treebtn"', 'id="mapbtn"',
                       'class="summary"', 'id="f-0"', 'id="f-2"', 'class="resizer" data-side="left"',
                       "<title>Review #42</title>", "fonts.googleapis.com", 'rel="icon"'):
            self.assertIn(needle, self.page, needle)

    def test_no_right_panel(self):
        for needle in ("aside.right", 'class="right"', 'data-side="right"', 'id="checksec"', 'id="fileonly"', 'id="list"'):
            self.assertNotIn(needle, self.page, needle)
        self.assertIn('<aside class="left"', self.page)
        self.assertNotIn("--right", self.page)

    def test_icons_cards_and_nav_scripts(self):
        js = assets.bundle_js(review_page.JS)
        for needle in ("el('button', 'ti '", "'n:' + n.key", "'t:' + t.id", "function openCard", "function closeCard", "CARD_DELAY",
                       "e.key === 'Escape' && cs.id", "Mark checked", "Use as comment", "Post GitHub comment", "addNoteReply",
                       "linkedNote(t)", "'#navcount'", "'#navprev'", "e.key !== 'n' && e.key !== 'p'", "textarea, select"):
            self.assertIn(needle, js, needle)

    def test_head_has_themes_before_style(self):
        self.assertLess(self.page.index("REVIEW_THEMES"), self.page.index("<style>"))
        self.assertIn("--surface-2:color-mix", self.page)
        self.assertIn(':root[data-theme="dark"]', self.page)

    def test_data_json(self):
        data = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', self.page, re.S).group(1))
        self.assertEqual((data["pr"], data["repo"], data["slug"], data["sha"]), (42, "acme/widgets", "acme-widgets-42", SHA))
        self.assertEqual((data["ai_name"], data["user"], data["has_insights"]), ("Claude", "Tony", True))
        self.assertEqual(data["order"], [0, 1, 2])
        self.assertEqual(data["files"][0]["i"], 0)
        self.assertNotIn("rows", data["files"][0])
        self.assertEqual(data["notes"][0]["endRow"], "r0-4")
        self.assertIn("Generated", data["layers"])
        self.assertEqual(data["severities"], ["block", "should", "nit", "question", "look"])
        self.assertEqual(data["severity_labels"]["should"], "Should fix")

    def test_posted_link_only_for_https(self):
        js = assets.bundle_js(review_page.JS)
        self.assertIn("startsWith('https://')", js)
        self.assertEqual(js.count("a.href = t.posted.url"), 1)

    def test_diff_rows_and_marks(self):
        self.assertIn('id="r0-3"', self.page)
        self.assertIn("hot should", self.page)
        self.assertNotIn('class="mk', self.page)
        self.assertIn("old &lt;b&gt;line&lt;/b&gt;", self.page)
        self.assertIn('<template class="lazy">', self.page)
        self.assertIn("Show generated diff", self.page)
        self.assertIn('class="file focused"', self.page)

    def test_tree_links_per_leaf(self):
        self.assertEqual(self.page.count('class="tlink"'), 2)

    def test_approve_button_and_popover(self):
        for needle in ('id="approvebtn"', 'id="approvepop"', 'id="approvetext"', 'Add a comment (optional)', 'id="approvecancel"', 'id="approvego"'):
            self.assertIn(needle, self.page, needle)
        js = assets.bundle_js(review_page.JS)
        self.assertIn("'/api/approve/' + D.slug", js)
        self.assertIn("JSON.stringify({ sha: D.sha, body", js)
        self.assertIn("startsWith('https://')", js)
        self.assertIn("done.href = a.url", js)

    def test_composer_checkbox_and_no_post_prefix(self):
        js = assets.bundle_js(review_page.JS)
        self.assertIn("Post GitHub comment", js)
        self.assertNotIn("start with post:", js)
        self.assertNotIn("isPost", js)
        self.assertIn("post: true", js)

    def test_drag_selection_present(self):
        js = assets.bundle_js(review_page.JS)
        for needle in ("'pointerdown'", "'pointermove'", "'pointerup'"):
            self.assertIn(needle, js)

    def test_appbar(self):
        self.assertIn("Make the button &lt;great&gt;", self.page)
        self.assertIn("CI passing", self.page)
        self.assertIn("Looks good", self.page)
        self.assertIn("+57", self.page)
        self.assertIn("a1b2c3d", self.page)

    def test_banners_render(self):
        page = review_page.render(review_model(banners=[{"type": "draft"}, {"type": "stale", "from": SHA, "to": "ffffffffff"}]))
        self.assertEqual(page.count('class="banner"'), 2)
        self.assertIn("Claude insights were written for", page)

    def test_no_insights_card_escapes_description(self):
        summary = dict(review_model()["summary"], has_insights=False, description="Hi <script>alert(1)</script>")
        page = review_page.render(review_model(summary=summary))
        self.assertIn("About this PR", page)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_indent_step(self):
        self.assertIn("var(--d,0) * 12px", self.page)

    def test_inline_scripts_parse(self):
        check_scripts(self, self.page, 2)


class QueuePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = queue_page.render(queue_model())

    def test_structure(self):
        for needle in ("Let's review!", 'id="qsum"', "3 PRs · ~24 min", 'id="qs"', 'id="qa"',
                       'id="qclear"', 'id="qnone"', 'data-effort="Large"', 'data-tog="failing"', 'class="qbucket"', 'class="qitem"',
                       'class="briefbtn"', "<title>Review queue</title>", "Brief<svg", "Details<svg", "dependabot (bot)</span>"):
            self.assertIn(needle, self.page, needle)

    def test_author_dropdown_options(self):
        raw = re.search(r'id="qa" data-options="(.*?)"', self.page).group(1)
        options = json.loads(raw.replace("&quot;", '"').replace("&amp;", "&"))
        self.assertEqual([o["label"] for o in options], ["All authors", "alice", "dependabot (bot)"])

    def test_item_attrs_and_pills(self):
        self.assertIn('data-author="alice" data-effort="Small" data-brief="1" data-ci="passing" data-draft="0" data-min="8"', self.page)
        self.assertIn('data-brief="0" data-ci="failing" data-draft="1"', self.page)
        self.assertIn("2 should fix", self.page)
        self.assertIn("1 nit<", self.page)
        self.assertIn("(estimated)", self.page)
        self.assertIn("2 comments · 1 open", self.page)
        self.assertIn('data-req datetime="2026-11-01T10:00:00Z"', self.page)

    def test_approved_chip(self):
        self.assertNotIn('class="chip approved"', self.page)
        model = queue_model()
        model["buckets"][0]["items"][0]["approved"] = True
        page = queue_page.render(model)
        self.assertEqual(page.count('<span class="chip approved">Approved</span>'), 1)

    def test_description_escaped(self):
        self.assertNotIn("<script>alert(1)</script>", self.page)

    def test_empty_queue(self):
        page = queue_page.render({"user": "Tony", "total_minutes": 0, "authors": [], "buckets": []})
        self.assertIn("Nothing waiting for your review.", page)
        self.assertEqual(len(inline_scripts(page)), 2)

    def test_inline_scripts_parse(self):
        check_scripts(self, self.page, 2)


def check_scripts(test, page, expected):
    node = shutil.which("node")
    if not node:
        test.skipTest("node not available")
    scripts = inline_scripts(page)
    test.assertEqual(len(scripts), expected)
    with tempfile.TemporaryDirectory() as tmp:
        for i, code in enumerate(scripts):
            path = Path(tmp) / f"s{i}.js"
            path.write_text(code)
            result = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
            test.assertEqual(result.returncode, 0, result.stderr)


class BundleTests(unittest.TestCase):
    def test_js_is_one_iife_and_review_boots_once(self):
        js = assets.bundle_js(review_page.JS)
        self.assertTrue(js.startswith("(function () {"))
        self.assertTrue(js.rstrip().endswith("})();"))
        self.assertEqual(js.count("'use strict'"), 1)

    def test_only_main_runs_boot_code(self):
        for name in review_page.JS + queue_page.JS:
            if name.endswith("main.js"):
                continue
            text = assets.read(f"js/{name}")
            top_level = [ln for ln in text.splitlines() if re.match(r"^(init|render|reload|computeCurrent|tree\.)\w*\(", ln)]
            self.assertEqual(top_level, [], name)

    def test_every_static_file_is_bundled(self):
        css = {p.name for p in (assets.STATIC / "css").glob("*.css")}
        self.assertEqual(css, set(review_page.CSS) | set(queue_page.CSS))
        js = {str(p.relative_to(assets.STATIC / "js")) for p in (assets.STATIC / "js").rglob("*.js")}
        self.assertEqual(js - {"shared/dropdown.js"}, (set(review_page.JS) | set(queue_page.JS)) - {"shared/dropdown.js"})


THREADS = ("threads: [{id: 't1', path: 'src/components/Button.tsx', side: 'RIGHT', start_line: 2, line: 2, noteKey: null, commit: '%s', "
           "resolved: false, resolvedAt: null, posted: null, messages: [{id: 'm1', who: 'me', text: 'Why this?', at: '2026-11-06T12:00:00.000Z'}, "
           "{id: 'm2', who: 'ai', text: 'Because.', at: '2026-11-06T12:01:00.000Z'}]}, "
           "{id: 't2', path: 'src/components/Button.tsx', side: 'RIGHT', start_line: 3, line: 3, noteKey: 'n1', commit: '%s', resolved: false, resolvedAt: null, "
           "posted: null, messages: [{id: 'm3', who: 'me', text: 'About the note', at: '2026-11-06T12:00:00.000Z'}]}]") % (SHA, SHA)


def page_with_threads(model):
    page = review_page.render(model)
    marker = "threads: []"
    assert marker in page
    return page.replace(marker, THREADS, 1)


class InlineIconTests(unittest.TestCase):
    def test_icons_for_notes_and_threads_in_a_real_browser(self):
        if not Path(CHROME).exists():
            self.skipTest("Chrome not available")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        path = OUT_DIR / "threads.html"
        path.write_text(page_with_threads(review_model()))
        run = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--window-size=1500,950", "--virtual-time-budget=3000",
                              "--dump-dom", f"file://{path}"], capture_output=True, text=True, timeout=90)
        dom = run.stdout
        self.assertIn('class="ti should" type="button" data-card="n:n1"', dom)
        self.assertIn('class="ti thread" type="button" data-card="t:t1"', dom)
        self.assertNotIn('data-card="t:t2"', dom)


class ScreenshotTests(unittest.TestCase):
    def test_render_pages_and_screenshot(self):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        pages = {"review": review_page.render(review_model(banners=[{"type": "stale", "from": SHA, "to": "ffffffffff"}])),
                 "queue": queue_page.render(queue_model())}
        for name, html in pages.items():
            (OUT_DIR / f"{name}.html").write_text(html)
        if not Path(CHROME).exists():
            self.skipTest("Chrome not available")
        for name in pages:
            out = OUT_DIR / f"{name}.png"
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1500,950",
                            "--virtual-time-budget=3000", f"--screenshot={out}", f"file://{OUT_DIR / (name + '.html')}"],
                           capture_output=True, timeout=90)
            self.assertTrue(out.exists(), name)


if __name__ == "__main__":
    unittest.main()


class IntralineTests(unittest.TestCase):
    def test_review_page_loads_pinned_jsdiff_with_integrity_before_the_bundle(self):
        page = review_page.render(review_model())
        tag = 'src="https://cdn.jsdelivr.net/npm/diff@5.2.0/dist/diff.min.js" integrity="sha384-'
        self.assertIn(tag, page)
        self.assertLess(page.index(tag), page.rindex("initIntraline();"))
