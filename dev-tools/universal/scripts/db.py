#!/usr/bin/env python3
"""Run SQL against the local Postgres database (container and names from workspace/config.json). Reads run straight away; writes need --apply.

Usage: db.py "<sql>" [--apply] [--limit N]    or    db.py --file seed.sql [--apply]
"""
import argparse
import csv
import io
import pathlib
import re
from _lib import require_config, DB_CONTAINER, LOCAL, apply_flag, code, fail, out
require_config()

apply = apply_flag()
p = argparse.ArgumentParser()
p.add_argument("sql", nargs="?")
p.add_argument("--file")
p.add_argument("--limit", type=int, default=200)
a = p.parse_args()

sql = pathlib.Path(a.file).read_text() if a.file else a.sql
if not sql:
    fail("give SQL or --file")
read_only = all(re.match(r"\s*(select|with|explain|show)\b", s, re.I) for s in sql.split(";") if s.strip())
if not read_only and not apply:
    out({"ok": True, "applied": False, "note": "this SQL writes; re-run with --apply", "sql": sql[:1000]})
    raise SystemExit

rc, stdout, stderr = code(["docker", "exec", "-i", DB_CONTAINER, "psql", "-U", LOCAL["db_user"], "-d", LOCAL["db_name"],
                           "-v", "ON_ERROR_STOP=1", "--csv", "-c", sql])
if rc != 0:
    fail(stderr or "psql failed")
rows = list(csv.DictReader(io.StringIO(stdout))) if read_only else []
out({"ok": True, "applied": not read_only, "rows": rows[: a.limit], "row_count": len(rows),
     "truncated": len(rows) > a.limit, "output": None if read_only else stdout[-1000:]})
