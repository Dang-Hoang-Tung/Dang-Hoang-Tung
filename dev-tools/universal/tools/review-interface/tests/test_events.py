import unittest

from helpers import *  # noqa: F401,F403  (sys.path setup)
from app.services import events


def entry(n, sha, status="current"):
    return {"slug": f"acme-widgets-{n}", "pr": n, "title": f"PR {n}", "head_sha": sha, "insights_status": status}


class RebuildEventTests(unittest.TestCase):
    def test_lists_exactly_the_new_and_moved_prs_to_check(self):
        previous = {e["slug"]: e for e in (entry(1, "aaa"), entry(2, "bbb"), entry(3, "ccc"))}
        current = [entry(1, "aaa"), entry(2, "bbb2", "stale"), entry(4, "ddd", "missing")]
        ev = events.rebuild_event(previous, current, "refresh", partial=False)
        self.assertEqual(ev["check"], [2, 4])
        self.assertEqual([m["pr"] for m in ev["moved"]], [2])
        self.assertEqual([n["pr"] for n in ev["new"]], [4])
        self.assertEqual(ev["gone"], ["acme-widgets-3"])
        self.assertEqual({x["pr"] for x in ev["needs_insights"]}, {2, 4})

    def test_partial_build_does_not_report_gone(self):
        previous = {e["slug"]: e for e in (entry(1, "aaa"), entry(2, "bbb"))}
        ev = events.rebuild_event(previous, [entry(1, "aaa")], "cli", partial=True)
        self.assertEqual((ev["gone"], ev["check"]), ([], []))
