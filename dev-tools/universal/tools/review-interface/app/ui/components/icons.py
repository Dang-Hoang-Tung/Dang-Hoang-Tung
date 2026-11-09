from app.ui.html import svg_icon

BACK = svg_icon('<path d="M15 6l-6 6 6 6"/>')
PALETTE = svg_icon('<path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.6-.8 1.6-1.6 0-.9-.6-1.2-.6-2.1 0-.9.7-1.6 1.6-1.6H17a4 4 0 0 0 4-4c0-4.7-4-8.7-9-8.7z"/><circle cx="7.5" cy="11" r="1.2"/><circle cx="10.5" cy="7" r="1.2"/><circle cx="15" cy="7.5" r="1.2"/>')
EXTERNAL = svg_icon('<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>')
TREE = svg_icon('<rect x="9" y="2" width="6" height="5" rx="1.5"/><rect x="2" y="17" width="6" height="5" rx="1.5"/><rect x="16" y="17" width="6" height="5" rx="1.5"/><path d="M12 7v5M5 17v-2.5a2.5 2.5 0 0 1 2.5-2.5h9a2.5 2.5 0 0 1 2.5 2.5V17"/>')
MAP = svg_icon('<rect x="3" y="3" width="10" height="11" rx="1.5"/><rect x="15" y="3" width="6" height="7" rx="1.5"/><rect x="15" y="12" width="6" height="9" rx="1.5"/><rect x="3" y="16" width="10" height="5" rx="1.5"/>')
BRIEF = svg_icon('<path d="M7 3h7l5 5v12a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>')
EYE = svg_icon('<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>')
COMMENTS = svg_icon('<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M8.5 10.5h7M8.5 13.5h4"/>')
OVERVIEW = svg_icon('<rect x="3" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5"/><rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5"/><rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5"/>')
CLOSE = svg_icon('<path d="M6 6l12 12M18 6L6 18"/>')
CHEVRON_DOWN = svg_icon('<path d="M6 9l6 6 6-6"/>')
THEME_TOGGLE = (
    '<svg class="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>'
    '<svg class="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
)


def _status_icon(status, inner):
    return (f'<svg class="fstat {status}" viewBox="0 0 16 16" aria-hidden="true">'
            f'<rect x="1.75" y="1.75" width="12.5" height="12.5" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.4"/>{inner}</svg>')


_DOT = 'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"'
FILE_STATUS = {
    "added": _status_icon("added", f'<path d="M8 5v6M5 8h6" {_DOT}/>'),
    "deleted": _status_icon("deleted", f'<path d="M5 8h6" {_DOT}/>'),
    "modified": _status_icon("modified", f'<path d="M8 4.5v4M6 6.5h4M6 11h4" {_DOT}/>'),
    "renamed": _status_icon("renamed", f'<path d="M4.75 8h6M8.5 5.5 11 8l-2.5 2.5" {_DOT}/>'),
}
STATUS_LABELS = {"added": "Added", "deleted": "Deleted", "modified": "Modified", "renamed": "Renamed or moved"}


def status_title(status, old_path=None):
    label = STATUS_LABELS.get(status, "Modified")
    return f"{label} from {old_path}" if status == "renamed" and old_path else label
