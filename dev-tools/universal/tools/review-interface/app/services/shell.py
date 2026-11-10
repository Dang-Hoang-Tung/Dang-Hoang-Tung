import subprocess

FAILURES = (subprocess.CalledProcessError, subprocess.TimeoutExpired)


def run(*args, timeout=60, errors="replace", **kw):
    """Stdout as text. Bytes are decoded as-is, so a lone carriage return stays inside its line."""
    return subprocess.run(args, capture_output=True, check=True, timeout=timeout, **kw).stdout.decode("utf-8", errors)


def why(e):
    text = getattr(e, "stderr", None) or str(e)
    text = (text.decode("utf-8", "replace") if isinstance(text, bytes) else text).strip()
    return text.splitlines()[-1][:300] if text else type(e).__name__
