import json
import unittest

from helpers import *  # noqa: F401,F403
from app.services import inbox
from test_server import ServerBase


def thread(tid, msgs, **kw):
    return {"id": tid, "messages": [{"id": i, "who": w, "text": t, "at": f"2026-01-01T00:00:0{n}Z"}
                                    for n, (i, w, t) in enumerate(msgs)], **kw}


class InboxTests(TmpCase):
    def lines(self):
        f = inbox.path(self.cfg)
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []

    def test_new_user_message_adds_one_line(self):
        before = {"threads": [thread("t1", [("m1", "me", "hi")], path="a.py", line=3)]}
        after = {"threads": [thread("t1", [("m1", "me", "hi"), ("m2", "me", "more")], path="a.py", line=3)]}
        inbox.append(self.cfg, inbox.entries_for("acme-widgets-7", before, after))
        (e,) = self.lines()
        self.assertEqual((e["slug"], e["pr"], e["thread"], e["kind"], e["path"], e["line"], e["text"]),
                         ("acme-widgets-7", 7, "t1", "comment", "a.py", 3, "more"))

    def test_ai_message_and_unchanged_resave_add_nothing(self):
        before = {"threads": [thread("t1", [("m1", "me", "hi")])]}
        ai = {"threads": [thread("t1", [("m1", "me", "hi"), ("m2", "ai", "yo"), ("m3", "claude", "yo")])]}
        self.assertEqual(inbox.new_user_messages(before, ai), [])
        self.assertEqual(inbox.new_user_messages(before, before), [])
        inbox.append(self.cfg, [])
        self.assertEqual(self.lines(), [])

    def test_chat_thread_kind_without_path(self):
        after = {"threads": [thread("chat", [("m1", "me", "hello")])]}
        inbox.append(self.cfg, inbox.entries_for("acme-widgets-7", {}, after))
        (e,) = self.lines()
        self.assertEqual((e["kind"], e["path"], e["line"]), ("chat", None, None))

    def test_keeps_last_lines(self):
        inbox.append(self.cfg, [{"n": i} for i in range(2 * inbox.KEEP + 5)])
        self.assertEqual(len(self.lines()), inbox.KEEP)


class InboxServerTests(ServerBase):
    def put(self, threads):
        return self.req("PUT", "/api/state/acme-widgets-7", {"threads": threads}, self.cookie)[0]

    def test_put_logs_only_new_user_messages(self):
        t = thread("chat", [("m1", "me", "hello")])
        self.assertEqual(self.put([t]), 200)
        self.assertEqual(self.put([t]), 200)
        ai = thread("chat", [("m2", "ai", "hi")])
        self.assertEqual(self.put([ai]), 200)
        f = inbox.path(self.cfg)
        (e,) = [json.loads(l) for l in f.read_text().splitlines()]
        self.assertEqual((e["kind"], e["text"], e["pr"]), ("chat", "hello", 7))


if __name__ == "__main__":
    unittest.main()
