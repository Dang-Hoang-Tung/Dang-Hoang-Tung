from app.ui import assets
from app.ui.html import esc

FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22%3E%3Crect width=%2232%22 height=%2232%22 rx=%228%22 fill=%22%237aa3ff%22/%3E"
           "%3Cpath d=%22M9 17l5 5 9-11%22 stroke=%22%230b0e13%22 stroke-width=%223.5%22 fill=%22none%22 stroke-linecap=%22round%22 stroke-linejoin=%22round%22/%3E%3C/svg%3E")
FONTS = "https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap"


def script_tag(code):
    safe = code.replace("</script", "<\\/script")
    return f"<script>{safe}</script>"


def render(title, css_files, body, js_files=None, head_extra=""):
    scripts = script_tag(assets.bundle_js(js_files)) if js_files else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{esc(title)}</title>\n"
        f'<link rel="icon" href="{FAVICON}">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'<link rel="stylesheet" href="{FONTS}">\n'
        f"{script_tag(assets.themes_js())}\n"
        f"<style>{assets.bundle_css(css_files)}</style></head><body>\n"
        f"{body}\n{head_extra}{scripts}</body></html>"
    )
