"""Colours and fonts of the app (one place to change them)."""
from nicegui import ui

INK = "#15233F"
MUTED = "#5B6B82"
LINE = "#DCE2EA"
TURF = "#1F7A4D"
WARN = "#B4530D"
ASSIST = "#93A6C2"

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
    --gk: #C98A00;
    --def: #2D6CB5;
    --mid: #2E8A57;
    --att: #C7432E;
    --win: #1F7A4D;
    --draw: #8A97A8;
    --loss: #B23A2B;
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
.sync-note {{ color: #C9D3E3; font-size: 13px; white-space: nowrap; text-decoration: none; }}
.sync-note:hover {{ color: #fff; text-decoration: underline; }}

.page {{ padding: 22px 28px 32px; max-width: 1280px; margin: 0 auto; }}
.page.wide {{ max-width: 1680px; }}
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

/* ---------- Home ---------- */

.panel {{ background: var(--sheet); border: 1px solid var(--line); border-radius: 6px; padding: 16px 18px; }}
.panel-title {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 20px; font-weight: 700; }}
.panel-subtitle {{ font-size: 15px; font-weight: 600; margin-top: 4px; }}
.title-link {{ color: var(--ink); text-decoration: none; }}
.title-link:hover {{ text-decoration: underline; }}

/* Season snapshot: the big numbers */
.snapshot {{ display: grid; grid-template-columns: repeat(5, auto); justify-content: space-between; gap: 18px 28px; }}
.stat .value {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 44px; font-weight: 700; line-height: 1; }}
.stat .caption {{ color: var(--muted); font-size: 14px; margin-top: 6px; }}
@media (max-width: 1100px) {{ .snapshot {{ grid-template-columns: repeat(3, auto); justify-content: start; }} }}
@media (max-width: 640px) {{ .snapshot {{ grid-template-columns: repeat(2, auto); }} }}

/* Results: W, D, L */
.form {{ display: flex; gap: 6px; margin-top: 4px; }}
.res {{ display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 4px;
        color: #fff; font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 14px; font-weight: 700; }}
.form .res {{ width: 38px; height: 38px; font-size: 20px; }}
.res-W {{ background: var(--win); }} .res-D {{ background: var(--draw); }} .res-L {{ background: var(--loss); }}

.home-grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; align-items: start; }}
@media (max-width: 1100px) {{ .home-grid {{ grid-template-columns: minmax(0, 1fr); }} }}

/* Matches */
.match-row {{ display: grid; grid-template-columns: 52px 26px minmax(0, 1fr) auto; align-items: center; gap: 10px;
              padding: 7px 0; border-top: 1px solid #EEF1F5; }}
.match-row:first-of-type {{ border-top: none; }}
.match-row .when {{ color: var(--muted); font-size: 13px; }}
.match-row .who {{ font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.match-row .comp {{ color: var(--muted); font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.match-row .score {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 18px; font-weight: 700; text-align: right; }}
.venue {{ color: var(--muted); font-weight: 400; }}

/* Leaders */
.leader-row {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 10px; padding: 8px 0; border-top: 1px solid #EEF1F5; }}
.leader-row:first-of-type {{ border-top: none; }}
.leader-row .what {{ grid-column: 1 / -1; color: var(--muted); font-size: 12px; }}
.leader-row .who {{ display: flex; align-items: center; gap: 8px; font-weight: 600; min-width: 0; }}
.leader-row .who span:last-child {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.leader-row .value {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 22px; font-weight: 700; }}

.names {{ color: var(--muted); font-size: 13px; }}
.money-out {{ color: var(--loss); }} .money-in {{ color: var(--turf); }}
.home-note {{ color: var(--muted); font-size: 13px; }}
.home-note a {{ color: var(--ink); }}

/* ---------- Matches ---------- */

.match-table tbody tr {{ cursor: default; }}
.match-table .upcoming {{ color: var(--muted); }}
.match-table .opponent {{ font-weight: 600; }}
.match-table .upcoming .opponent {{ font-weight: 400; }}
.match-table .score-cell {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 16px; font-weight: 700; }}
.pens {{ color: var(--muted); font-size: 12px; margin-left: 4px; }}
.next-tag {{ font-size: 12px; font-weight: 600; color: var(--turf); border: 1px solid #BFDCCB; background: #EEF7F1;
             border-radius: 10px; padding: 1px 8px; }}
.rec-lines {{ display: grid; grid-template-columns: minmax(0, 1fr) repeat(6, 28px); gap: 3px 6px; font-size: 13px; }}
.rec-lines .h {{ color: var(--muted); font-size: 12px; }}
.rec-lines .n {{ text-align: right; }}
.rec-lines .name {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.rec-lines .current {{ font-weight: 700; }}
.big-score {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 28px; font-weight: 700; min-width: 48px; }}
.side-panel .opponent {{ font-weight: 600; }}

/* ---------- Player stats ---------- */

/* Competition switch */
.comp-toggle {{ border: 1px solid var(--line); border-radius: 6px; background: var(--sheet); }}
.comp-toggle .q-btn {{ font-size: 14px; padding: 4px 14px; }}

/* Summary strip: reads like a sentence */
.summary {{ display: flex; flex-wrap: wrap; gap: 6px 28px; padding: 10px 0 4px; border-top: 1px solid var(--line); }}
.summary .value {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 24px; font-weight: 700; margin-right: 6px; }}
.summary .label {{ color: var(--muted); font-size: 14px; }}

.main-grid {{ display: grid; grid-template-columns: minmax(0, 1fr) 360px; gap: 24px; align-items: start; }}
@media (max-width: 1100px) {{ .main-grid {{ grid-template-columns: minmax(0, 1fr); }} }}

/* Squad table */
.squad-table {{ height: calc(100vh - 290px); min-height: 360px; border: 1px solid var(--line); border-radius: 6px; background: var(--sheet); }}
.squad-table thead tr th {{
    position: sticky; top: 0; z-index: 2; background: var(--sheet);
    color: var(--muted); font-size: 13px; font-weight: 600; text-transform: none;
    font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; border-bottom: 1px solid var(--line);
}}
.squad-table tbody td {{ font-size: 14px; border-color: #EEF1F5; }}
.squad-table th, .squad-table td {{ padding: 4px 7px !important; white-space: nowrap; }}
/* Sort arrow only on the sorted column: keeps the columns narrow */
.squad-table th .q-table__sort-icon {{ display: none; }}
.squad-table th.sorted .q-table__sort-icon {{ display: inline-flex; }}
.squad-table tbody tr {{ cursor: pointer; }}
.squad-table tbody tr:hover td {{ background: #F6F8FB; }}
.squad-table tbody tr.selected td {{ background: #E6F0EA; }}
.squad-table .q-table--col-auto-width {{ display: none; }}
.squad-table .player {{ font-weight: 600; }}

/* Position colour code (the squad sheet) */
.pos {{
    display: inline-block; min-width: 40px; padding: 1px 6px; border-radius: 3px; text-align: center;
    color: #fff; font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 13px; font-weight: 700;
}}
.pos-gk {{ background: var(--gk); }} .pos-def {{ background: var(--def); }}
.pos-mid {{ background: var(--mid); }} .pos-att {{ background: var(--att); }}
.pos.secondary {{ background: transparent; color: var(--muted); border: 1px solid var(--line); }}
.growth.up {{ color: var(--turf); font-weight: 600; }}

/* Side panel: top contributors or player sheet */
.side-panel {{ background: var(--sheet); border: 1px solid var(--line); border-radius: 6px; padding: 16px 18px; }}
.side-title {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 20px; font-weight: 700; }}
.side-note {{ color: var(--muted); font-size: 13px; }}
.player-card {{ border-left: 6px solid var(--mid); padding-left: 14px; }}
.player-card.gk {{ border-color: var(--gk); }} .player-card.def {{ border-color: var(--def); }}
.player-card.att {{ border-color: var(--att); }}
.player-name {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 30px; font-weight: 700; line-height: 1.05; }}
.rating {{ display: flex; align-items: baseline; gap: 6px; }}
.rating .value {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 34px; font-weight: 700; }}
.rating .label {{ color: var(--muted); font-size: 13px; }}
.facts {{ display: grid; grid-template-columns: 130px 1fr; gap: 4px 12px; font-size: 14px; }}
.facts .k {{ color: var(--muted); }}
.section-title {{ font-size: 15px; font-weight: 600; margin-top: 6px; }}
.comp-lines {{ display: grid; grid-template-columns: minmax(0, 1fr) repeat(5, 38px); gap: 3px 6px; font-size: 13px; }}
.comp-lines .h {{ color: var(--muted); font-size: 12px; }}
.comp-lines .n {{ text-align: right; }}
.comp-lines .total {{ font-weight: 700; border-top: 1px solid var(--line); padding-top: 3px; }}

.empty {{ max-width: 640px; margin: 80px auto; }}
.empty .path {{ background: var(--sheet); border: 1px solid var(--line); border-radius: 4px; padding: 6px 10px; font-size: 13px; }}
"""


def apply() -> None:
    ui.add_css(CSS)
    ui.colors(primary=INK, positive=TURF, warning=WARN)
