"""Standings: the league table of the selected season (overall, home or away)."""
from nicegui import ui

import layout
import season_stats

# The three tables: None = all matches, "home" or "away" = only those matches
VIEWS = {"Overall": None, "Home": "home", "Away": "away"}

NUMBER = {"style": "width: 52px", "headerStyle": "width: 52px"}

COLUMNS = [
    {"name": "position", "label": "Pos", "field": "position", "align": "center", **NUMBER},
    {"name": "team", "label": "Club", "field": "team", "align": "left"},
    {"name": "played", "label": "P", "field": "played", **NUMBER},
    {"name": "wins", "label": "W", "field": "wins", **NUMBER},
    {"name": "draws", "label": "D", "field": "draws", **NUMBER},
    {"name": "losses", "label": "L", "field": "losses", **NUMBER},
    {"name": "goals_for", "label": "GF", "field": "goals_for", **NUMBER},
    {"name": "goals_against", "label": "GA", "field": "goals_against", **NUMBER},
    {"name": "goal_difference", "label": "GD", "field": "goal_difference", **NUMBER},
    {"name": "points", "label": "Pts", "field": "points", **NUMBER},
]

# One template for every cell: the club's row is highlighted, GD gets its sign
CELL = r'''
<q-td :props="props" :class="props.row.mine ? 'mine' : ''">
  <template v-if="props.col.name === 'team'"><span class="team">{{ props.value }}</span></template>
  <template v-else-if="props.col.name === 'goal_difference'">{{ props.value > 0 ? '+' + props.value : props.value }}</template>
  <template v-else-if="props.col.name === 'points'"><span class="pts">{{ props.value }}</span></template>
  <template v-else>{{ props.value }}</template>
</q-td>
'''

NOTES = {
    "Overall": "Teams level on points are ordered by goal difference, then goals scored.",
    "Home": "Home matches only: 3 points for a win, 1 for a draw. "
            "Teams level on points are ordered by goal difference, then goals scored.",
    "Away": "Away matches only: 3 points for a win, 1 for a draw. "
            "Teams level on points are ordered by goal difference, then goals scored.",
}


def signed(value) -> str:
    return f"+{value}" if value > 0 else str(value)


def rank(position) -> str:
    return season_stats.ordinal(position) if isinstance(position, int) else "-"


def points_gap(gap: int) -> str:
    """-3 -> "3 pts behind", 1 -> "1 pt ahead", 0 -> "level on points"."""
    if gap == 0:
        return "level on points"
    count = abs(gap)
    return f"{count} {'pt' if count == 1 else 'pts'} {'ahead' if gap > 0 else 'behind'}"


@ui.page("/standings")
def standings_page() -> None:
    with layout.frame("/standings") as (career, season):
        if career is None:
            return

        rows = season_stats.season_rows(career["folder"], season, "standings") if season else None

        if not rows:
            ui.label("Standings").classes("page-title")
            if season is None:
                ui.label("No season exported yet for this career.").classes("page-note")
            else:
                ui.label(f"No league table exported for {season} yet. It arrives with the next export "
                         "of tco_session.lua in the game.").classes("page-note")
            return

        build_page(rows, career.get("team_id"))


def build_page(rows: list[dict], team_id) -> None:
    state = {"view": "Overall"}
    competition = rows[0].get("competition") or "League"

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    with ui.row().classes("w-full items-center justify-between"):
        with ui.column().classes("gap-0"):
            ui.label("Standings").classes("page-title")
            ui.label(f"{competition}, {len(rows)} teams").classes("page-note competition")
        ui.toggle(list(VIEWS), value="Overall", on_change=lambda e: change_view(e.value)).props(
            "no-caps unelevated color=white text-color=primary toggle-color=primary toggle-text-color=white"
        ).classes("comp-toggle view-toggle")

    with ui.element("div").classes("main-grid w-full"):
        with ui.column().classes("w-full min-w-0 gap-2"):
            table = ui.table(
                rows=[],
                columns=COLUMNS,
                row_key="teamid",
                pagination={"rowsPerPage": 0},
            ).props("dense flat hide-bottom").classes("standings-table w-full")
            table.add_slot("body-cell", CELL)
            note = ui.label().classes("page-note")

        panel = ui.column().classes("side-panel w-full gap-3")

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def refresh() -> None:
        lines = season_stats.standings(rows, VIEWS[state["view"]])
        table.rows = [dict(line, mine=line["teamid"] == team_id) for line in lines]
        table.update()
        note.set_text(NOTES[state["view"]])
        side_panel(lines)

    def change_view(view: str | None) -> None:
        state["view"] = view if view in VIEWS else "Overall"
        refresh()

    # ------------------------------------------------------------------
    # Side panel: the club's position and the gaps around it
    # ------------------------------------------------------------------
    def side_panel(lines: list[dict]) -> None:
        info = season_stats.table_position(lines, team_id)
        panel.clear()
        with panel:
            view = state["view"]
            ui.label("Position" if view == "Overall" else f"Position, {view.lower()} matches").classes("side-title")
            if info is None:
                ui.label("Your club is not in this table.").classes("side-note")
                return

            club = info["club"]
            with ui.row().classes("items-baseline gap-2 no-wrap"):
                ui.label(rank(club["position"])).classes("big-position")
                ui.label(f"of {info['teams']} teams").classes("side-note")

            with ui.element("div").classes("facts"):
                for key, value in [
                    ("Points", club["points"]),
                    ("Played", club["played"]),
                    ("Won, drawn, lost", f"{club['wins']}-{club['draws']}-{club['losses']}"),
                    ("Goal difference", signed(club["goal_difference"])),
                ]:
                    ui.label(key).classes("k")
                    ui.label(str(value))

            ui.label("Gaps").classes("section-title")
            if info["leader"] is None:
                ui.label("Top of the table.").classes("side-note")
            with ui.element("div").classes("w-full"):
                for label, line in [("Leader", info["leader"]), ("Just above", info["above"]),
                                    ("Just below", info["below"])]:
                    if line is None:
                        continue
                    with ui.element("div").classes("gap-row"):
                        ui.label(label).classes("what")
                        with ui.element("div").classes("who"):
                            ui.label(rank(line["position"])).classes("rank")
                            ui.label(line["team"]).classes("name")
                        ui.label(points_gap(line["gap"])).classes("gap-value")

    refresh()
