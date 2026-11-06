import unittest

import helpers  # noqa: F401

from app.services.adapters.team_reviewer import brief_to_insights

NEW = """# #7 Add thing
ann · +10 −2 · 3 files · CI passing

Verdict: Approve with nits. Safe to fix after merge.
What: Adds retry to the sync job.
Risk: Medium. Could double-send on retry.
Time: ~12 min

## Check
1. 🔴 Retry is not idempotent — `src/sync.py:42`
   Runs twice when the first call times out.
   Sends duplicate emails.
   > Can we add an idempotency key here? Retries may double-send.
2. 🟡 Missing test — `tests/test_sync.py:10-20`
   No retry case.
3. ⚪ Typo — `README.md:3`
+2 nits

## Ask the author
- Is the timeout configurable?
"""

OLD = """## 30 seconds
- Verdict: Request changes
- Risk: High. big
- Time needed: ~30 min

## Findings
🔴 **Bad thing** — `a/b.py:5`
body line
> Comment: fix it

## Questions for the author
- Why?
"""


class TeamReviewerV2Test(unittest.TestCase):
    def test_new_format(self):
        ins = brief_to_insights(NEW, "o/r", 7, "abc")
        s = ins["summary"]
        self.assertEqual(s["verdict"], "Approve with nits. Safe to fix after merge.")
        self.assertEqual(s["what"], "Adds retry to the sync job.")
        self.assertEqual((s["risk"], s["minutes"]), ("Medium", 12))
        self.assertEqual(s["risk_note"], "Medium. Could double-send on retry.")
        self.assertEqual(len(s["tldr"]), 4)
        self.assertEqual(s["questions"], ["Is the timeout configurable?"])
        r = ins["recommendations"]
        self.assertEqual([x["severity"] for x in r], ["block", "should", "nit"])
        self.assertEqual(r[0]["title"], "Retry is not idempotent")
        self.assertEqual((r[0]["path"], r[0]["start_line"]), ("src/sync.py", 42))
        self.assertEqual(r[0]["body"], "Runs twice when the first call times out.\nSends duplicate emails.")
        self.assertTrue(r[0]["draft_comment"].startswith("Can we add"))
        self.assertEqual((r[1]["start_line"], r[1]["end_line"]), (10, 20))

    def test_none_is_empty(self):
        ins = brief_to_insights("Verdict: Approve. ok\n\n## Check\nNone.\n\n## Ask the author\nNone.\n", "o/r", 1, "a")
        self.assertEqual(ins["recommendations"], [])
        self.assertEqual(ins["summary"]["questions"], [])

    def test_old_format(self):
        ins = brief_to_insights(OLD, "o/r", 7, "abc")
        s = ins["summary"]
        self.assertEqual((s["verdict"], s["risk"], s["minutes"], s["what"]), ("Request changes", "High", 30, ""))
        self.assertEqual(s["questions"], ["Why?"])
        self.assertEqual(ins["recommendations"][0]["title"], "Bad thing")
        self.assertEqual(ins["recommendations"][0]["draft_comment"], "fix it")


if __name__ == "__main__":
    unittest.main()
