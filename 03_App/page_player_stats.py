"""Player stats: the squad of the selected season, by competition."""
from nicegui import ui

import football
import layout
import store
import theme

ALL_COMPETITIONS = "All competitions"
ALL = "All"

POSITION_SORT = f"(a, b) => {football.POSITION_ORDER}.indexOf(a) - {football.POSITION_ORDER}.indexOf(b)"

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


def load_rows(folder: str, season: str) -> list[dict]:
    path = store.find_file(store.career_dir(folder) / season, "player_stats")

    if path is None:
        return []

    rows = store.read_rows(path)

    for row in rows:
        row["pos_group"] = football.position_group(row.get("position"))

    return rows


def mean(values: list) -> str:
    values = [v for v in values if isinstance(v, (int, float))]
    return f"{sum(values) / len(values):.1f}" if values else "-"


def number(value) -> float:
    return value if isinstance(value, (int, float)) else 0


@ui.page("/player-stats")
def player_stats() -> None:
    with layout.frame("/player-stats", wide=True) as (career, season):
        if career is None:
            return

        rows_all = load_rows(career["folder"], season) if season else []

        if not rows_all:
            ui.label("Player stats").classes("page-title")
            ui.label(f"No player stats exported for {season} yet. They arrive with the next export "
                     "of tco_session.lua in the game.").classes("page-note")
            return

        build_page(rows_all)


def build_page(rows_all: list[dict]) -> None:
    state = {"competition": ALL_COMPETITIONS, "selected": None, "chart_ids": []}

    # Competitions ordered by matches played (the league first)
    played = {}
    for row in rows_all:
        if row.get("row_type") == "COMPETITION" and row.get("competition"):
            played[row["competition"]] = played.get(row["competition"], 0) + number(row.get("appearances"))
    competitions = sorted(played, key=lambda c: -played[c])

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Player stats").classes("page-title")
        ui.toggle([ALL_COMPETITIONS] + competitions, value=ALL_COMPETITIONS,
                  on_change=lambda e: change_competition(e.value)).props(
            "no-caps unelevated color=white text-color=primary toggle-color=primary toggle-text-color=white"
        ).classes("comp-toggle")

    with ui.row().classes("w-full items-end gap-3"):
        position_filter = ui.select([ALL], value=ALL, label="Position", on_change=lambda: refresh()) \
            .props("outlined dense options-dense").classes("w-36")
        role_filter = ui.select([ALL], value=ALL, label="Squad role", on_change=lambda: refresh()) \
            .props("outlined dense options-dense").classes("w-40")
        nation_filter = ui.select([ALL], value=ALL, label="Nationality", on_change=lambda: refresh()) \
            .props("outlined dense options-dense").classes("w-48")
        min_apps = ui.number("Min. appearances", value=0, min=0, step=1, precision=0, on_change=lambda: refresh()) \
            .props("outlined dense").classes("w-40")
        search = ui.input(placeholder="Search a player", on_change=lambda: refresh()) \
            .props("outlined dense clearable").classes("w-56")
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

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def view_rows() -> list[dict]:
        if state["competition"] == ALL_COMPETITIONS:
            return [r for r in rows_all if r.get("row_type") == "TOTAL"]
        return [r for r in rows_all
                if r.get("row_type") == "COMPETITION" and r.get("competition") == state["competition"]]

    def filtered_rows() -> list[dict]:
        rows = view_rows()
        if position_filter.value not in (None, ALL):
            rows = [r for r in rows if r.get("position") == position_filter.value]
        if role_filter.value not in (None, ALL):
            rows = [r for r in rows if r.get("squad_role") == role_filter.value]
        if nation_filter.value not in (None, ALL):
            rows = [r for r in rows if r.get("nationality") == nation_filter.value]
        rows = [r for r in rows if number(r.get("appearances")) >= (min_apps.value or 0)]
        text = (search.value or "").strip().lower()
        if text:
            rows = [r for r in rows if text in str(r.get("playername", "")).lower()]
        return rows

    def set_options(select, values, ordering=None) -> None:
        options = sorted({v for v in values if v}, key=ordering)
        select.set_options([ALL] + options, value=select.value if select.value in options else ALL)

    def refresh_filters() -> None:
        rows = view_rows()
        set_options(position_filter, [r.get("position") for r in rows], ordering=football.position_rank)
        set_options(role_filter, [r.get("squad_role") for r in rows], ordering=football.role_rank)
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
                (sum(1 for r in rows if number(r.get("appearances")) > 0), "played"),
                (mean([r.get("age") for r in rows]), "average age"),
                (mean([r.get("overall") for r in rows]), "average OVR"),
                (mean([r.get("potential") for r in rows]), "average POT"),
            ]:
                with ui.element("span"):
                    ui.label(str(value)).classes("value inline")
                    ui.label(label).classes("label inline")

        if state["selected"] is None:
            show_overview()

    def change_competition(competition: str | None) -> None:
        state["competition"] = competition or ALL_COMPETITIONS
        refresh_filters()
        refresh()

    # ------------------------------------------------------------------
    # Side panel: top contributors, or one player
    # ------------------------------------------------------------------
    def show_overview() -> None:
        state["selected"] = None
        table.selected = []
        table.update()
        top = sorted(
            [r for r in filtered_rows() if number(r.get("goal_contributions")) > 0],
            key=lambda r: (number(r.get("goal_contributions")), number(r.get("goals"))),
            reverse=True,
        )[:8]
        panel.clear()
        with panel:
            ui.label("Top goal contributions").classes("side-title")
            if not top:
                ui.label("No goals or assists yet in this view.").classes("side-note")
                return
            state["chart_ids"] = [r["playerid"] for r in top]
            totals = [number(r.get("goal_contributions")) for r in top]
            ui.echart({
                "animation": False,
                "textStyle": {"fontFamily": theme.FONT},
                "grid": {"left": 4, "right": 28, "top": 30, "bottom": 4, "containLabel": True},
                "legend": {"top": 0, "left": 0, "icon": "rect", "itemWidth": 10, "itemHeight": 10,
                           "textStyle": {"color": theme.MUTED}},
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "xAxis": {"type": "value", "minInterval": 1, "splitLine": {"lineStyle": {"color": "#EEF1F5"}},
                          "axisLabel": {"color": theme.MUTED}},
                "yAxis": {"type": "category", "inverse": True, "data": [r["playername"] for r in top],
                          "axisTick": {"show": False}, "axisLine": {"show": False},
                          "axisLabel": {"color": theme.INK, "fontSize": 13}},
                "series": [
                    {"name": "Goals", "type": "bar", "stack": "ga", "barWidth": 14,
                     "data": [number(r.get("goals")) for r in top], "itemStyle": {"color": theme.INK}},
                    {"name": "Assists", "type": "bar", "stack": "ga", "barWidth": 14,
                     "data": [number(r.get("assists")) for r in top], "itemStyle": {"color": theme.ASSIST},
                     "label": {"show": True, "position": "right", "color": theme.INK, "fontWeight": 600,
                               ":formatter": f"p => {totals}[p.dataIndex]"}},
                ],
            }, on_point_click=lambda e: show_player(state["chart_ids"][e.data_index])) \
                .classes("w-full").style(f"height: {70 + 34 * len(top)}px")
            ui.label("Click a player in the table or in the chart to open their sheet.").classes("side-note")

    def show_player(playerid) -> None:
        total = next((r for r in rows_all if r.get("playerid") == playerid and r.get("row_type") == "TOTAL"), None)
        if total is None:
            return
        state["selected"] = playerid
        table.selected = [r for r in table.rows if r["playerid"] == playerid]
        table.update()
        competitions_of_player = [r for r in rows_all
                                  if r.get("playerid") == playerid and r.get("row_type") == "COMPETITION"]

        panel.clear()
        with panel:
            with ui.row().classes("w-full items-start justify-between no-wrap"):
                with ui.column().classes(f"player-card {total['pos_group']} gap-2"):
                    ui.label(total.get("playername", "")).classes("player-name")
                    with ui.row().classes("gap-1"):
                        for index, key in enumerate(["position", "second_position", "third_position", "fourth_position"]):
                            position = total.get(key)
                            if position:
                                group = football.position_group(position)
                                ui.label(position).classes(f"pos pos-{group}" + (" secondary" if index else ""))
                ui.button(icon="close", on_click=show_overview).props("flat round dense").tooltip("Close")

            growth = total.get("growth_gap")
            with ui.row().classes("gap-6"):
                for label, value in [("OVR", total.get("overall")), ("POT", total.get("potential")),
                                     ("growth", f"+{growth}" if number(growth) > 0 else growth)]:
                    with ui.element("div").classes("rating"):
                        ui.label(str(value if value is not None else "-")).classes("value")
                        ui.label(label).classes("label")

            ui.label("Profile").classes("section-title")
            with ui.element("div").classes("facts"):
                for key, value in [
                    ("Nationality", total.get("nationality")),
                    ("Age", total.get("age")),
                    ("Height / weight", f"{total.get('height')} cm / {total.get('weight')} kg"),
                    ("Preferred foot", football.FOOT.get(total.get("preferred_foot"), total.get("preferred_foot"))),
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
            if not competitions_of_player:
                ui.label("No appearance this season.").classes("side-note")
            else:
                with ui.element("div").classes("comp-lines w-full"):
                    for header in ["Competition", "Apps", "AVG", "G", "A", "MOTM"]:
                        ui.label(header).classes("h" + ("" if header == "Competition" else " n"))
                    for line in competitions_of_player + [dict(total, competition=ALL_COMPETITIONS)]:
                        extra = " total" if line.get("row_type") == "TOTAL" else ""
                        ui.label(line.get("competition", "")).classes(extra)
                        for key in ["appearances", "AVG", "goals", "assists", "MOTMs"]:
                            value = line.get(key)
                            text = f"{value:.2f}" if key == "AVG" and value else str(value if value is not None else "-")
                            ui.label(text).classes("n" + extra)

    refresh_filters()
    refresh()
