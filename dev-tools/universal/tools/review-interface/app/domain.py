"""Shared vocabulary for logic and UI: pure data, no I/O."""

SEVERITIES = ("block", "should", "nit", "question", "look")
SEVERITY_LABELS = {"block": "Blocking", "should": "Should fix", "nit": "Nit", "look": "Look here", "question": "Question"}
LAYERS = ("UI", "Hooks", "API", "Domain", "Data", "Copy", "Config", "Tests", "Other", "Generated")


def worst(kinds):
    """The most severe kind among `kinds` (strings), or None."""
    kinds = set(kinds)
    return next((k for k in SEVERITIES if k in kinds), None)
