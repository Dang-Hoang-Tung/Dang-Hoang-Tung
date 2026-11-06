"""Shared fixtures for the tests: sys.path setup, sample PR, diff, config and state builders."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config  # noqa: E402

HEAD = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
REPO = "acme/widgets"

DIFF = """diff --git a/src/app/Widget.tsx b/src/app/Widget.tsx
index 111..222 100644
--- a/src/app/Widget.tsx
+++ b/src/app/Widget.tsx
@@ -10,4 +10,5 @@ export function Widget() {
   const a = 1;
-  const b = 2;
+  const b = 3;
+  const c = 4;
   return a;
 }
diff --git a/src/lib/util.ts b/src/lib/util.ts
index 333..444 100644
--- a/src/lib/util.ts
+++ b/src/lib/util.ts
@@ -1,3 +1,3 @@
 export const x = 1;
-export const y = 2;
+export const y = 5;
 export const z = 3;
diff --git a/src/generated/api.ts b/src/generated/api.ts
index 555..666 100644
--- a/src/generated/api.ts
+++ b/src/generated/api.ts
@@ -1,2 +1,2 @@
 // generated
-old
+new
"""


def make_pr(**kw):
    pr = {
        "number": 7, "title": "Add widget", "url": "https://github.com/acme/widgets/pull/7",
        "author": {"login": "alice"}, "headRefOid": HEAD, "baseRefName": "main", "isDraft": False,
        "body": "Some **description**", "createdAt": "2026-11-01T10:00:00Z", "statusCheckRollup": [],
        "repo": REPO, "source": {"repo": REPO},
    }
    pr.update(kw)
    return pr


def make_cfg(tmp, **extra):
    data_dir = Path(tmp) / "data"
    conf = {**copy.deepcopy(config.DEFAULTS), "data_dir": str(data_dir), "port": 0, "sources": [{"repo": REPO}], **extra}
    path = Path(tmp) / "config.json"
    path.write_text(json.dumps(conf))
    return config.load_config(path)


class TmpCase(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.tmp = self._td.name
        self.cfg = make_cfg(self.tmp)


def msg(i, who, text, at):
    return {"id": i, "who": who, "text": text, "at": at}


def thread(tid, messages, **kw):
    return {"id": tid, "messages": messages, **kw}


def good_insights(**kw):
    obj = {
        "schema": "review-insights/1", "repo": REPO, "pr": 7, "head_sha": HEAD[:7],
        "summary": {"verdict": "Approve with nits", "risk": "Medium", "minutes": 25, "tldr": ["What: widget"], "questions": ["Why?"]},
        "recommendations": [
            {"id": "r1", "severity": "should", "title": "Bump looks wrong", "body": "body", "path": "src/app/Widget.tsx",
             "start_line": 11, "end_line": 12, "draft_comment": "please check"},
            {"severity": "nit", "title": "General nit"},
        ],
    }
    obj.update(kw)
    return obj


BRIEF = """# acme/widgets#7

## 30 seconds
- Verdict: Approve with nits. One thing to check.
- Risk: Medium — touches the widget layout
- Time needed: ~25 min

## Look here
1. `src/app/Widget.tsx:10-14` — the counter changed from 2 to 3
2. `src/lib/util.ts:2` — y is now 5

## Findings
🔴 Blocking
**Counter off by one** — `src/app/Widget.tsx:11-12` · HIGH
The new value breaks the loop bound.
> Comment: This looks off by one, can you check?

🟡 Should fix
**Magic number** — `src/lib/util.ts:2` · MEDIUM
Name the constant.

⚪ Nits
**Spelling** — `src/lib/util.ts:3` · LOW
Typo in name.

## Questions for the author
- Why 5 and not 4?
- Is there a ticket?
"""


def tree_stats(paths, notes=None):
    notes = notes or {}
    return {p: {"idx": i, "a": 1, "d": 2, "gen": p.endswith("gen.ts"), "notes": notes.get(p, [])} for i, p in enumerate(paths)}


def summary_for(slug_, number, author, minutes=10, **kw):
    s = {"slug": slug_, "number": number, "title": f"t{number}", "url": "u", "author": author, "head_sha": HEAD, "ci": "none", "draft": False,
         "effort": "Small", "minutes": minutes, "minutes_source": "estimate", "added": 1, "deleted": 0, "files": 1, "verdict": "", "risk": "",
         "findings": {}, "has_insights": False, "summary": {"tldr": [], "questions": [], "description": None}}
    s.update(kw)
    return s
