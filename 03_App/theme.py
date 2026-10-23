"""Colours and fonts of the app (one place to change them)."""
from nicegui import ui

INK = "#15233F"
MUTED = "#5B6B82"
LINE = "#DCE2EA"
TURF = "#1F7A4D"
WARN = "#B4530D"

FONT = "'Bahnschrift', 'Segoe UI', sans-serif"
FONT_CONDENSED = "'Bahnschrift SemiCondensed', 'Bahnschrift', 'Arial Narrow', sans-serif"

CSS = f"""
:root {{
    --paper: #F3F5F8;
    --sheet: #FFFFFF;
    --ink: {INK};
    --muted: {MUTED};
    --line: {LINE};
    --turf: {TURF};
    --warn: {WARN};
}}
body {{ background: var(--paper); color: var(--ink); font-family: {FONT} !important; }}
.cond {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; }}

/* Header: club, season, pages */
.tco-header {{ background: var(--ink); color: #fff; padding: 8px 28px; gap: 8px 28px; flex-wrap: wrap; }}
.club-select .q-field__native, .club-select .q-field__native span {{
    font-family: {FONT_CONDENSED}; font-stretch: semi-condensed;
    font-size: 30px; font-weight: 700; color: #fff; line-height: 1.1;
}}
.season-select .q-field__native, .season-select .q-field__native span {{ font-size: 16px; color: #fff; }}
.nav-link {{ color: #C9D3E3; text-decoration: none; font-size: 15px; padding: 6px 2px; border-bottom: 2px solid transparent; }}
.nav-link:hover {{ color: #fff; }}
.nav-link.active {{ color: #fff; border-bottom-color: #fff; }}
.sync-note {{ color: #C9D3E3; font-size: 13px; white-space: nowrap; }}

.page {{ padding: 22px 28px 32px; max-width: 1280px; margin: 0 auto; }}
.page-title {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 26px; font-weight: 700; }}
.page-note {{ color: var(--muted); font-size: 14px; }}

/* Warnings (protected seasons, errors) */
.warning {{ border: 1px solid #F0C9A8; border-left: 5px solid var(--warn); background: #FFF8F2;
            border-radius: 6px; padding: 12px 16px; }}
.warning .title {{ font-weight: 600; }}

/* Seasons */
.seasons {{ background: var(--sheet); border: 1px solid var(--line); border-radius: 6px; }}
.season-row {{ display: grid; grid-template-columns: 130px 120px 140px 170px 1fr 110px;
               align-items: center; gap: 12px; padding: 12px 18px; border-top: 1px solid #EEF1F5; cursor: pointer; }}
.season-row:hover {{ background: #F6F8FB; }}
.season-row.selected {{ background: #E6F0EA; }}
.season-row.head {{ border-top: none; cursor: default; color: var(--muted); font-size: 13px; padding-top: 10px; padding-bottom: 8px; }}
.season-row.head:hover {{ background: none; }}
.season-name {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 20px; font-weight: 700; }}
.big {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 20px; font-weight: 700; }}
.cell-caption {{ display: none; color: var(--muted); font-size: 12px; }}
.files {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.file {{ font-size: 12px; padding: 1px 8px; border-radius: 10px; border: 1px solid var(--line); color: var(--muted); }}
.file.ok {{ border-color: #BFDCCB; background: #EEF7F1; color: var(--turf); }}
.file.missing {{ border-style: dashed; }}
.status {{ font-size: 13px; color: var(--muted); }}
.status.new, .status.updated {{ color: var(--turf); font-weight: 600; }}
.status.protected, .status.error {{ color: var(--warn); font-weight: 600; }}
@media (max-width: 900px) {{
    .tco-header {{ padding: 8px 16px; }}
    .sync-note {{ display: none; }}
    .page {{ padding: 18px 16px 28px; }}
    .season-row {{ grid-template-columns: 1fr 1fr; padding: 12px 14px; }}
    .season-row.head {{ display: none; }}
    .cell-caption {{ display: block; }}
}}

.empty {{ max-width: 640px; margin: 80px auto; }}
.empty .path {{ background: var(--sheet); border: 1px solid var(--line); border-radius: 4px; padding: 6px 10px; font-size: 13px; }}
"""


def apply() -> None:
    ui.add_css(CSS)
    ui.colors(primary=INK, positive=TURF, warning=WARN)
