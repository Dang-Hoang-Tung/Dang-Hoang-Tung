import subprocess

FAILURES = (subprocess.CalledProcessError, subprocess.TimeoutExpired)


def run(*args, timeout=60, **kw):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=timeout, **kw).stdout


def why(e):
    text = (getattr(e, "stderr", "") or str(e)).strip()
    return text.splitlines()[-1][:300] if text else type(e).__name__
