"""The Club Office - interface trial with NiceGUI: the Player stats page.

Reads the files written by 02_Lua/tco_session.lua directly from
Documents/TheClubOffice/exports (no manual import, no team id to type).

Launch: lancer_essai.bat (Windows) or `python main.py`.
"""
import os
from datetime import date
from pathlib import Path

from nicegui import ui

import exports_data as data

ALL_COMPETITIONS = "All competitions"
ALL = "All"

INK = "#15233F"
MUTED = "#5B6B82"
LINE = "#DCE2EA"
TURF = "#1F7A4D"
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
    --gk: #C98A00;
    --def: #2D6CB5;
    --mid: #2E8A57;
    --att: #C7432E;
}}
body {{ background: var(--paper); color: var(--ink); font-family: {FONT} !important; }}
.cond {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; }}

/* Header bar: the club and the season */
.tco-header {{ background: var(--ink); color: #fff; padding: 10px 28px; }}
.club-select .q-field__native, .club-select .q-field__native span {{
    font-family: {FONT_CONDENSED}; font-stretch: semi-condensed;
    font-size: 30px; font-weight: 700; color: #fff; line-height: 1.1;
}}
.season-select .q-field__native, .season-select .q-field__native span {{ font-size: 16px; color: #fff; }}
.export-note {{ color: #C9D3E3; font-size: 13px; }}

.page {{ padding: 20px 28px 28px; max-width: 1680px; margin: 0 auto; }}
.page-title {{ font-family: {FONT_CONDENSED}; font-stretch: semi-condensed; font-size: 26px; font-weight: 700; }}

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
.squad-table {{ height: calc(100vh - 300px); min-height: 360px; border: 1px solid var(--line); border-radius: 6px; background: var(--sheet); }}
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

/* Side panel */
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

.empty {{ max-width: 620px; margin: 80px auto; text-align: left; }}
.empty .path {{ background: var(--sheet); border: 1px solid var(--line); border-radius: 4px; padding: 6px 10px; font-size: 13px; }}
"""

POSITION_SORT = "(a, b) => order.indexOf(a) - order.indexOf(b)".replace(
    "order", str(data.POSITION_ORDER)
)

COLUMNS = [
    {"name": "position", "label": "Pos", "field": "position", "sortable": True, "align": "left", ":sort": POSITION_SORT},
    {"name": "playername", "label": "Player", "field": "playername", "sortable": True, "align": "left", "classes": "player"},
    {"name": "age", "label": "Age", "field": "age", "sortable": True},
    {"name": "overall", "label": "OVR", "field": "overall", "sortable": True},
    {"name": "potential", "label": "POT", "field": "potential", "sortable": True},
    {"name": "growth_gap", "label": "Growth", "field": "growth_gap", "sortable": True},
    {"name": "squad_role", "label": "Role", "field": "squad_role", "sortable": True, "align": "left"},
    {"name": "appearances", "label": "Apps", "field": "appearances", "sortable": True},
    {"name": "AVG", "label": "AVG", "field": "AVG", "sortable": True, ":format": "v => v ? Number(v).toFixed(2) : '-'"},
    {"name": "goals", "label": "Goals", "field": "goals", "sortable": True},
    {"name": "assists", "label": "Assists", "field": "assists", "sortable": True},
    {"name": "goal_contributions", "label": "G+A", "field": "goal_contributions", "sortable": True},
    {"name": "MOTMs", "label": "MOTM", "field": "MOTMs", "sortable": True},
    {"name": "yellow_cards", "label": "YC", "field": "yellow_cards", "sortable": True},
    {"name": "red_cards", "label": "RC", "field": "red_cards", "sortable": True},
    {"name": "cleansheets", "label": "CS", "field": "cleansheets", "sortable": True},
]

FOOT = {1: "Right", 2: "Left"}


def format_game_date(text: str | None) -> str:
    try:
        return date.fromisoformat(text or "").strftime("%d %b %Y").lstrip("0")
    except ValueError:
        return "unknown"


def mean(values: list) -> str:
    values = [v for v in values if isinstance(v, (int, float))]
    return f"{sum(values) / len(values):.1f}" if values else "-"


@ui.page("/")
def player_stats_page() -> None:
    ui.add_css(CSS)
    ui.colors(primary=INK, positive=TURF)

    root = data.find_exports_root()
    state = {"careers": [], "career": None, "season": None, "rows": [], "competition": ALL_COMPETITIONS, "selected": None}

    def scan() -> None:
        state["careers"] = data.list_careers(root)

    scan()

    if not state["careers"]:
        with ui.column().classes("empty gap-3"):
            ui.label("No exported career yet").classes("page-title")
            ui.label("The files written by tco_session.lua were not found in this folder:")
            ui.label(str(root)).classes("path")
            ui.label("Run 02_Lua/tco_session.lua in FC 26 (F9, Lua Engine, Execute), then reload this page.")
        return

    # ------------------------------------------------------------------
    # Header: career and season
    # ------------------------------------------------------------------
    with ui.header().classes("tco-header items-center justify-between no-wrap"):
        with ui.row().classes("items-center gap-6 no-wrap"):
            career_select = ui.select({}, on_change=lambda e: change_career(e.value)).props(
                "dark borderless dense options-dense behavior=menu"
            ).classes("club-select")
            season_select = ui.select([], label="Season", on_change=lambda e: change_season(e.value)).props(
                "dark borderless dense options-dense behavior=menu label-color=grey-5"
            ).classes("season-select")
        with ui.row().classes("items-center gap-4 no-wrap"):
            export_note = ui.label("").classes("export-note")
            ui.button("Reload files", icon="refresh", on_click=lambda: reload_files()).props(
                "flat dense no-caps color=white"
            )

    # ------------------------------------------------------------------
    # Page
    # ------------------------------------------------------------------
    with ui.column().classes("page w-full gap-3"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("Player stats").classes("page-title")
            comp_toggle = ui.toggle([ALL_COMPETITIONS], value=ALL_COMPETITIONS, on_change=lambda e: change_competition(e.value)).props(
                "no-caps unelevated color=white text-color=primary toggle-color=primary toggle-text-color=white"
            ).classes("comp-toggle")

        with ui.row().classes("w-full items-end gap-3"):
            position_filter = ui.select([ALL], value=ALL, label="Position", on_change=lambda: refresh()).props("outlined dense options-dense").classes("w-36")
            role_filter = ui.select([ALL], value=ALL, label="Squad role", on_change=lambda: refresh()).props("outlined dense options-dense").classes("w-40")
            nation_filter = ui.select([ALL], value=ALL, label="Nationality", on_change=lambda: refresh()).props("outlined dense options-dense").classes("w-48")
            min_apps = ui.number("Min. appearances", value=0, min=0, step=1, precision=0, on_change=lambda: refresh()).props("outlined dense").classes("w-40")
            search = ui.input(placeholder="Search a player", on_change=lambda: refresh()).props("outlined dense clearable").classes("w-56")
            with search.add_slot("prepend"):
                ui.icon("search").classes("text-lg")

        summary = ui.element("div").classes("summary w-full")

        with ui.element("div").classes("main-grid w-full"):
            table = ui.table(
                rows=[],
                columns=COLUMNS,
                row_key="playerid",
                selection="single",
                pagination={"rowsPerPage": 0, "sortBy": "appearances", "descending": True},
            ).props("dense flat virtual-scroll hide-bottom").classes("squad-table")
            table.add_slot("body-cell-position", r'''
                <q-td :props="props"><span :class="'pos pos-' + props.row.pos_group">{{ props.value }}</span></q-td>
            ''')
            table.add_slot("body-cell-growth_gap", r'''
                <q-td :props="props"><span :class="props.value > 0 ? 'growth up' : 'growth'">{{ props.value > 0 ? '+' + props.value : props.value }}</span></q-td>
            ''')
            table.on("rowClick", lambda e: show_player(e.args[1]["playerid"]))

            panel = ui.column().classes("side-panel w-full gap-3")

    chart_holder = {"chart": None, "ids": []}

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def season_dir() -> Path:
        return state["career"] / state["season"]

    def view_rows() -> list[dict]:
        if state["competition"] == ALL_COMPETITIONS:
            return [r for r in state["rows"] if r.get("row_type") == "TOTAL"]
        return [r for r in state["rows"] if r.get("row_type") == "COMPETITION" and r.get("competition") == state["competition"]]

    def filtered_rows() -> list[dict]:
        rows = view_rows()
        if position_filter.value not in (None, ALL):
            rows = [r for r in rows if r.get("position") == position_filter.value]
        if role_filter.value not in (None, ALL):
            rows = [r for r in rows if r.get("squad_role") == role_filter.value]
        if nation_filter.value not in (None, ALL):
            rows = [r for r in rows if r.get("nationality") == nation_filter.value]
        rows = [r for r in rows if (r.get("appearances") or 0) >= (min_apps.value or 0)]
        text = (search.value or "").strip().lower()
        if text:
            rows = [r for r in rows if text in str(r.get("playername", "")).lower()]
        return rows

    def set_options(select, values, ordering=None) -> None:
        options = sorted({v for v in values if v}, key=ordering)
        select.set_options([ALL] + options, value=select.value if select.value in options else ALL)

    def refresh_filters() -> None:
        rows = view_rows()
        set_options(position_filter, [r.get("position") for r in rows],
                    ordering=lambda p: data.POSITION_ORDER.index(p) if p in data.POSITION_ORDER else 99)
        set_options(role_filter, [r.get("squad_role") for r in rows],
                    ordering=lambda r: ["Crucial", "Important", "Rotation", "Sporadic", "Prospect"].index(r)
                    if r in ["Crucial", "Important", "Rotation", "Sporadic", "Prospect"] else 99)
        set_options(nation_filter, [r.get("nationality") for r in rows])

    def refresh() -> None:
        rows = filtered_rows()
        table.rows = rows
        table.selected = [r for r in rows if r["playerid"] == state["selected"]]
        table.update()

        summary.clear()
        with summary:
            for value, label in [
                (len(rows), "players"),
                (sum(1 for r in rows if (r.get("appearances") or 0) > 0), "played"),
                (mean([r.get("age") for r in rows]), "average age"),
                (mean([r.get("overall") for r in rows]), "average OVR"),
                (mean([r.get("potential") for r in rows]), "average POT"),
            ]:
                with ui.element("span"):
                    ui.label(str(value)).classes("value inline")
                    ui.label(label).classes("label inline")

        if state["selected"] is None:
            show_overview()

    def load_season() -> None:
        state["rows"] = data.load_player_stats(season_dir())
        # Competitions ordered by matches played (the league first)
        played = {}
        for r in state["rows"]:
            if r.get("row_type") == "COMPETITION" and r.get("competition"):
                played[r["competition"]] = played.get(r["competition"], 0) + (r.get("appearances") or 0)
        competitions = sorted(played, key=lambda c: -played[c])
        comp_toggle.set_options([ALL_COMPETITIONS] + competitions, value=ALL_COMPETITIONS)
        state["competition"] = ALL_COMPETITIONS
        state["selected"] = None
        saved = data.read_state(season_dir())
        export_note.set_text(f"Last export: {format_game_date(saved.get('game_date'))} in the game")
        refresh_filters()
        refresh()

    def change_career(path_text: str | None) -> None:
        if not path_text:
            return
        state["career"] = Path(path_text)
        seasons = data.list_seasons(state["career"])
        state["season"] = seasons[-1] if seasons else None
        season_select.set_options(seasons, value=state["season"])
        if state["season"]:
            load_season()

    def change_season(season: str | None) -> None:
        if season and season != state["season"]:
            state["season"] = season
            load_season()

    def change_competition(competition: str | None) -> None:
        state["competition"] = competition or ALL_COMPETITIONS
        refresh_filters()
        refresh()

    def reload_files() -> None:
        scan()
        current = state["career"]
        options = {str(c): data.career_label(c, state["careers"]) for c in state["careers"]}
        career_select.set_options(options, value=str(current) if current and str(current) in options else next(iter(options)))
        if state["career"] and state["season"]:
            seasons = data.list_seasons(state["career"])
            season_select.set_options(seasons, value=state["season"] if state["season"] in seasons else seasons[-1])
            load_season()
        ui.notify("Files reloaded", position="bottom-right")

    # ------------------------------------------------------------------
    # Side panel: top contributors, or one player
    # ------------------------------------------------------------------
    def show_overview() -> None:
        state["selected"] = None
        table.selected = []
        table.update()
        top = sorted(
            [r for r in filtered_rows() if (r.get("goal_contributions") or 0) > 0],
            key=lambda r: (r.get("goal_contributions") or 0, r.get("goals") or 0),
            reverse=True,
        )[:8]
        panel.clear()
        with panel:
            ui.label("Top goal contributions").classes("side-title")
            if not top:
                ui.label("No goals or assists yet in this view.").classes("side-note")
                return
            chart_holder["ids"] = [r["playerid"] for r in top]
            totals = [r.get("goal_contributions") or 0 for r in top]
            ui.echart({
                "animation": False,
                "textStyle": {"fontFamily": FONT},
                "grid": {"left": 4, "right": 28, "top": 30, "bottom": 4, "containLabel": True},
                "legend": {"top": 0, "left": 0, "icon": "rect", "itemWidth": 10, "itemHeight": 10,
                           "textStyle": {"color": MUTED}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "xAxis": {"type": "value", "minInterval": 1, "splitLine": {"lineStyle": {"color": "#EEF1F5"}},
                          "axisLabel": {"color": MUTED}},
                "yAxis": {"type": "category", "inverse": True, "data": [r["playername"] for r in top],
                          "axisTick": {"show": False}, "axisLine": {"show": False},
                          "axisLabel": {"color": INK, "fontSize": 13}},
                "series": [
                    {"name": "Goals", "type": "bar", "stack": "ga", "barWidth": 14,
                     "data": [r.get("goals") or 0 for r in top], "itemStyle": {"color": INK}},
                    {"name": "Assists", "type": "bar", "stack": "ga", "barWidth": 14,
                     "data": [r.get("assists") or 0 for r in top], "itemStyle": {"color": ASSIST},
                     "label": {"show": True, "position": "right", "color": INK, "fontWeight": 600,
                               ":formatter": f"p => {totals}[p.dataIndex]"}},
                ],
            }, on_point_click=lambda e: show_player(chart_holder["ids"][e.data_index])).classes("w-full").style(f"height: {70 + 34 * len(top)}px")
            ui.label("Click a player in the table or in the chart to open their sheet.").classes("side-note")

    def show_player(playerid) -> None:
        total = next((r for r in state["rows"] if r.get("playerid") == playerid and r.get("row_type") == "TOTAL"), None)
        if total is None:
            return
        state["selected"] = playerid
        table.selected = [r for r in table.rows if r["playerid"] == playerid]
        table.update()
        competitions = [r for r in state["rows"] if r.get("playerid") == playerid and r.get("row_type") == "COMPETITION"]

        panel.clear()
        with panel:
            with ui.row().classes("w-full items-start justify-between no-wrap"):
                with ui.column().classes(f"player-card {total['pos_group']} gap-2"):
                    ui.label(total.get("playername", "")).classes("player-name")
                    with ui.row().classes("gap-1"):
                        for index, key in enumerate(["position", "second_position", "third_position", "fourth_position"]):
                            position = total.get(key)
                            if position:
                                group = data.POSITION_GROUPS.get(position, "mid")
                                ui.label(position).classes(f"pos pos-{group}" + (" secondary" if index else ""))
                ui.button(icon="close", on_click=show_overview).props("flat round dense").tooltip("Close")

            with ui.row().classes("gap-6"):
                for label, value in [("OVR", total.get("overall")), ("POT", total.get("potential")),
                                     ("growth", f"+{total.get('growth_gap')}" if (total.get("growth_gap") or 0) > 0 else total.get("growth_gap"))]:
                    with ui.element("div").classes("rating"):
                        ui.label(str(value if value is not None else "-")).classes("value")
                        ui.label(label).classes("label")

            ui.label("Profile").classes("section-title")
            with ui.element("div").classes("facts"):
                for key, value in [
                    ("Nationality", total.get("nationality")),
                    ("Age", total.get("age")),
                    ("Height / weight", f"{total.get('height')} cm / {total.get('weight')} kg"),
                    ("Preferred foot", FOOT.get(total.get("preferred_foot"), total.get("preferred_foot"))),
                    ("Skill moves", total.get("skill_moves")),
                    ("Weak foot", total.get("weak_foot")),
                ]:
                    ui.label(key).classes("k")
                    ui.label(str(value if value not in (None, "") else "-"))

            ui.label("Contract").classes("section-title")
            with ui.element("div").classes("facts"):
                for key, value in [
                    ("Squad role", total.get("squad_role")),
                    ("Contract until", total.get("contract_end")),
                    ("Length", f"{total.get('contract_duration_months')} months"),
                    ("Retiring", "Yes" if total.get("is_retiring") == 1 else "No"),
                ]:
                    ui.label(key).classes("k")
                    ui.label(str(value if value not in (None, "") else "-"))

            ui.label("This season").classes("section-title")
            if not competitions:
                ui.label("No appearance this season.").classes("side-note")
            else:
                with ui.element("div").classes("comp-lines w-full"):
                    for header in ["Competition", "Apps", "AVG", "G", "A", "MOTM"]:
                        ui.label(header).classes("h" + ("" if header == "Competition" else " n"))
                    for line in competitions + [dict(total, competition="All competitions")]:
                        extra = " total" if line.get("row_type") == "TOTAL" else ""
                        ui.label(line.get("competition", "")).classes(extra)
                        for key in ["appearances", "AVG", "goals", "assists", "MOTMs"]:
                            value = line.get(key)
                            text = f"{value:.2f}" if key == "AVG" and value else str(value if value is not None else "-")
                            ui.label(text).classes("n" + extra)

    # First load: the first career, its most recent season
    career_options = {str(c): data.career_label(c, state["careers"]) for c in state["careers"]}
    career_select.set_options(career_options, value=next(iter(career_options)))


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="Player stats - The Club Office",
        favicon="⚽",
        port=int(os.environ.get("TCO_PORT", "8765")),
        reload=False,
        show=os.environ.get("TCO_NO_BROWSER") is None,
    )
