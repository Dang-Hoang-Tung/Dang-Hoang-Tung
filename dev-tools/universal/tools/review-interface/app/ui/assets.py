from pathlib import Path

STATIC = Path(__file__).parent / "static"


def read(relative):
    return (STATIC / relative).read_text(encoding="utf-8")


def themes_js():
    return read("themes.js")


def bundle_css(files):
    return "\n".join(read(f"css/{name}") for name in files)


def bundle_js(files):
    body = "\n".join(read(f"js/{name}") for name in files)
    return f"(function () {{\n'use strict';\n{body}\n}})();"
