"""Matches: the fixtures and results of the club for the selected season."""
from nicegui import ui

import layout
import season_stats

ALL_COMPETITIONS = "All competitions"
ALL = "All"
STATUS = {ALL: None, "Played": True, "To play": False}
VENUE = {ALL: None, "Home": "H", "Away": "A"}
RESULT = {ALL: None, "Won": "W", "Drawn": "D", "Lost": "L"}

COLUMNS = [
    {"name": "date", "label": "Date", "field": "date_sort", "sortable": True, "align": "left"},
    {"name": "competition", "label": "Competition", "field": "competition", "sortable": True, "align": "left"},
    {"name": "venue", "label": "H/A", "field": "venue", "sortable": True, "align": "center"},
    {"name": "opponent", "label": "Opponent", "field": "opponent", "sortable": True, "align": "left"},
    {"name": "score", "label": "Score", "field": "score", "align": "center"},
    {"name": "result", "label": "Result", "field": "result", "sortable": True, "align": "center"},
]

# One template for every cell: upcoming matches are greyed, the result is a W/D/L badge
CELL = r'''
<q-td :props="props" :class="props.row.played ? '' : 'upcoming'">
  <template v-if="props.col.name === 'date'">{{ props.row.date_text || '-' }}</template>
  <template v-else-if="props.col.name === 'opponent'"><span class="opponent">{{ props.value }}</span></template>
  <template v-else-if="props.col.name === 'score'">
    <span v-if="props.row.played" class="score-cell">{{ props.row.score_main }}</span>
    <span v-if="props.row.penalties" class="pens">({{ props.row.penalties }})</span>
    <span v-if="!props.row.played">-</span>
  </template>
  <template v-else-if="props.col.name === 'result'">
    <span v-if="props.row.played" :class="'res res-' + props.value">{{ props.value }}</span>
    <span v-else-if="props.row.next" class="next-tag">Next</span>
  </template>
  <template v-else>{{ props.value }}</template>
</q-td>
'''


def table_rows(items: list[dict]) -> list[dict]:
    rows = []
    next_found = False
    for index, match in enumerate(items):
        is_next = not match["played"] and not next_found
        next_found = next_found or is_next
        rows.append({
            "key": index,
            "date_sort": index,  # the list is already in date order
            "date_text": match["date_text"],
            "competition": match["competition"],
            "venue": match["venue"],
            "opponent": match["opponent"],
            "score": match["score"],
            "score_main": match["score"].split(" (")[0],
            "penalties": match["penalties"],
            "result": match["result"],
            "played": match["played"],
            "next": is_next,
        })
    return rows


def record_line(grid, name: str, rec: dict, current: bool = False) -> None:
    extra = " current" if current else ""
    with grid:
        ui.label(name).classes("name" + extra)
        for key in ["played", "wins", "draws", "losses", "goals_for", "goals_against"]:
            ui.label(str(rec[key])).classes("n" + extra)


@ui.page("/matches")
def matches_page() -> None:
    with layout.frame("/matches", wide=True) as (career, season):
        if career is None:
            return

        rows = season_stats.season_rows(career["folder"], season, "fixtures") if season else None

        if not rows:
            ui.label("Matches").classes("page-title")
            ui.label(f"No fixtures exported for {season} yet. They arrive with the next export "
                     "of tco_session.lua in the game.").classes("page-note")
            return

        build_page(season_stats.match_list(rows))


def build_page(items: list[dict]) -> None:
    state = {"competition": ALL_COMPETITIONS}

    # Competitions ordered by number of matches (the league first)
    counts = {}
    for match in items:
        counts[match["competition"]] = counts.get(match["competition"], 0) + 1
    competitions = sorted(counts, key=lambda c: -counts[c])

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Matches").classes("page-title")
        ui.toggle([ALL_COMPETITIONS] + competitions, value=ALL_COMPETITIONS,
                  on_change=lambda e: change_competition(e.value)).props(
            "no-caps unelevated color=white text-color=primary toggle-color=primary toggle-text-color=white"
        ).classes("comp-toggle")

    with ui.row().classes("w-full items-end gap-3"):
        status_filter = ui.select(list(STATUS), value=ALL, label="Status", on_change=lambda: refresh()) \
            .props("outlined dense options-dense").classes("w-36")
        venue_filter = ui.select(list(VENUE), value=ALL, label="Home or away", on_change=lambda: refresh()) \
            .props("outlined dense options-dense").classes("w-36")
        result_filter = ui.select(list(RESULT), value=ALL, label="Result", on_change=lambda: refresh()) \
            .props("outlined dense options-dense").classes("w-36")
        search = ui.input(placeholder="Search an opponent", on_change=lambda: refresh()) \
            .props("outlined dense clearable").classes("w-56")
        with search.add_slot("prepend"):
            ui.icon("search").classes("text-lg")

    summary = ui.element("div").classes("summary w-full")

    with ui.element("div").classes("main-grid w-full"):
        table = ui.table(
            rows=[],
            columns=COLUMNS,
            row_key="key",
            pagination={"rowsPerPage": 0, "sortBy": "date", "descending": False},
        ).props("dense flat virtual-scroll hide-bottom").classes("squad-table match-table")
        table.add_slot("body-cell", CELL)

        panel = ui.column().classes("side-panel w-full gap-3")

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------
    def competition_items() -> list[dict]:
        if state["competition"] == ALL_COMPETITIONS:
            return items
        return [m for m in items if m["competition"] == state["competition"]]

    def filtered_items() -> list[dict]:
        result = competition_items()
        if STATUS[status_filter.value] is not None:
            result = [m for m in result if m["played"] == STATUS[status_filter.value]]
        if VENUE[venue_filter.value] is not None:
            result = [m for m in result if m["venue"] == VENUE[venue_filter.value]]
        if RESULT[result_filter.value] is not None:
            result = [m for m in result if m["result"] == RESULT[result_filter.value]]
        text = (search.value or "").strip().lower()
        if text:
            result = [m for m in result if text in m["opponent"].lower()]
        return result

    def refresh() -> None:
        shown = filtered_items()
        # "Next" is the first match to play of the competition, even when filters hide others
        rows = table_rows(competition_items())
        keys = {id(m) for m in shown}
        table.rows = [row for row, match in zip(rows, competition_items()) if id(match) in keys]
        table.update()

        rec = season_stats.record(shown)
        gd = rec["goals_for"] - rec["goals_against"]
        summary.clear()
        with summary:
            for value, label in [
                (rec["played"], "played"),
                (f"{rec['wins']}-{rec['draws']}-{rec['losses']}", "won, drawn, lost"),
                (rec["goals_for"], "scored"),
                (rec["goals_against"], "conceded"),
                (f"+{gd}" if gd > 0 else gd, "goal difference"),
                (rec["to_play"], "to play"),
            ]:
                with ui.element("span"):
                    ui.label(str(value)).classes("value inline")
                    ui.label(label).classes("label inline")

    def change_competition(competition: str | None) -> None:
        state["competition"] = competition or ALL_COMPETITIONS
        refresh()
        side_panel()

    # ------------------------------------------------------------------
    # Side panel: record by competition, home and away, biggest results
    # ------------------------------------------------------------------
    def side_panel() -> None:
        current = competition_items()
        panel.clear()
        with panel:
            ui.label("Record").classes("side-title")
            grid = ui.element("div").classes("rec-lines w-full")
            with grid:
                for header in ["Competition", "P", "W", "D", "L", "GF", "GA"]:
                    ui.label(header).classes("h" + ("" if header == "Competition" else " n"))
            for competition in competitions:
                record_line(grid, competition, season_stats.record([m for m in items if m["competition"] == competition]),
                            current=competition == state["competition"])
            if len(competitions) > 1:
                record_line(grid, ALL_COMPETITIONS, season_stats.record(items),
                            current=state["competition"] == ALL_COMPETITIONS)

            title = "Home and away" + ("" if state["competition"] == ALL_COMPETITIONS else f", {state['competition']}")
            ui.label(title).classes("section-title")
            grid = ui.element("div").classes("rec-lines w-full")
            with grid:
                for header in ["", "P", "W", "D", "L", "GF", "GA"]:
                    ui.label(header).classes("h" + ("" if header == "" else " n"))
            record_line(grid, "Home", season_stats.record([m for m in current if m["venue"] == "H"]))
            record_line(grid, "Away", season_stats.record([m for m in current if m["venue"] == "A"]))

            for result, label in [("W", "Biggest win"), ("L", "Heaviest defeat")]:
                ui.label(label).classes("section-title")
                match = season_stats.biggest(current, result)
                if match is None:
                    ui.label("None yet.").classes("side-note")
                    continue
                with ui.row().classes("items-center gap-2 no-wrap"):
                    ui.label(match["score"].split(" (")[0]).classes("big-score")
                    with ui.column().classes("gap-0 min-w-0"):
                        ui.label(f"{'vs' if match['venue'] == 'H' else 'at'} {match['opponent']}").classes("opponent")
                        ui.label(", ".join(p for p in [match["competition"], match["date_text"]] if p)).classes("side-note")

    refresh()
    side_panel()
