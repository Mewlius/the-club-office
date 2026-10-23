"""History: the career season by season, and the all-time records."""
from nicegui import ui

import career_stats
import football
import layout
import season_stats

ALL_COMPETITIONS = "All competitions"

SEASON_COLUMNS = [
    {"name": "season", "label": "Season", "field": "season", "align": "left"},
    {"name": "league", "label": "League", "field": "league", "align": "left"},
    {"name": "position", "label": "Pos", "field": "position", "align": "center"},
    {"name": "points", "label": "Pts", "field": "points"},
    {"name": "played", "label": "P", "field": "played"},
    {"name": "wins", "label": "W", "field": "wins"},
    {"name": "draws", "label": "D", "field": "draws"},
    {"name": "losses", "label": "L", "field": "losses"},
    {"name": "goals_for", "label": "GF", "field": "goals_for"},
    {"name": "goals_against", "label": "GA", "field": "goals_against"},
    {"name": "top_scorer", "label": "Top scorer", "field": "top_scorer", "align": "left"},
    {"name": "top_assists", "label": "Top assists", "field": "top_assists", "align": "left"},
    {"name": "net_spend", "label": "Net spend", "field": "net_spend"},
]

# One template for every cell: "in progress" tag, top players with their number, net spend colour
SEASON_CELL = r'''
<q-td :props="props">
  <template v-if="props.col.name === 'season'">
    <span class="season-label">{{ props.value }}</span>
    <span v-if="props.row.in_progress" class="progress-tag">in progress</span>
  </template>
  <template v-else-if="props.col.name === 'top_scorer' || props.col.name === 'top_assists'">
    <span v-if="props.value">{{ props.value }} <span class="count">{{ props.row[props.col.name + '_value'] }}</span></span>
    <span v-else>-</span>
  </template>
  <template v-else-if="props.col.name === 'net_spend'">
    <span :class="props.row.net_class">{{ props.value }}</span>
  </template>
  <template v-else>{{ props.value }}</template>
</q-td>
'''


def season_rows(lines: list[dict]) -> list[dict]:
    """The table rows, most recent season first."""
    rows = []
    for line in reversed(lines):
        league = line["league"] or {}
        record = line["record"] or {}
        position = league.get("position")
        net = line["net_spend"]
        rows.append({
            "season": line["season"],
            "in_progress": line["in_progress"],
            "league": league.get("competition") or "-",
            "position": season_stats.ordinal(position) if isinstance(position, int) else "-",
            "points": f"{league['points']:.0f}" if league else "-",
            **{key: record.get(key, "-") for key in ("played", "wins", "draws", "losses", "goals_for", "goals_against")},
            "top_scorer": (line["top_scorer"] or {}).get("player", ""),
            "top_scorer_value": (line["top_scorer"] or {}).get("value", ""),
            "top_assists": (line["top_assists"] or {}).get("player", ""),
            "top_assists_value": (line["top_assists"] or {}).get("value", ""),
            "net_spend": season_stats.money(net) if net is not None else "-",
            "net_class": "money-out" if net and net > 0 else "money-in" if net and net < 0 else "",
        })
    return rows


@ui.page("/history")
def history_page() -> None:
    with layout.frame("/history", wide=True) as (career, season):
        if career is None:
            return

        seasons = career_stats.load_career(career["folder"])

        if not seasons:
            ui.label("History").classes("page-title")
            ui.label("No season exported yet for this career.").classes("page-note")
            return

        build_page(career, seasons)


def record_card(title: str):
    card = ui.column().classes("panel record-card gap-1")
    with card:
        ui.label(title).classes("section-title")
    return card


def build_page(career: dict, seasons: list[dict]) -> None:
    folder = career["folder"]
    lines = career_stats.season_lines(seasons, career.get("team_id"))
    competitions = career_stats.competitions(seasons)
    state = {"competition": ALL_COMPETITIONS}

    # ------------------------------------------------------------------
    # Season by season
    # ------------------------------------------------------------------
    with ui.column().classes("gap-0"):
        ui.label("History").classes("page-title")
        ui.label(f"{len(seasons)} {'season' if len(seasons) == 1 else 'seasons'} with the club. "
                 "Click a season to open it.").classes("page-note")

    table = ui.table(rows=season_rows(lines), columns=SEASON_COLUMNS, row_key="season",
                     pagination={"rowsPerPage": 0}).props("dense flat hide-bottom").classes("history-table w-full")
    table.add_slot("body-cell", SEASON_CELL)
    table.on("rowClick", lambda e: layout.select_season(folder, e.args[1]["season"], go_to="/"))

    # ------------------------------------------------------------------
    # All-time records
    # ------------------------------------------------------------------
    with ui.row().classes("w-full items-center justify-between records-head"):
        ui.label("All-time records").classes("page-title")
        ui.toggle([ALL_COMPETITIONS] + competitions, value=ALL_COMPETITIONS,
                  on_change=lambda e: change_competition(e.value)).props(
            "no-caps unelevated color=white text-color=primary toggle-color=primary toggle-text-color=white"
        ).classes("comp-toggle records-toggle")

    with ui.element("div").classes("club-records w-full"):
        win_card = record_card("Biggest win")
        season_card = record_card("Best season")
        signing_card = record_card("Biggest signing")
        sale_card = record_card("Biggest sale")

    ui.label("Best season and biggest transfers count all competitions.").classes("page-note")
    players_grid = ui.element("div").classes("record-grid w-full")

    # Fixed: best season and biggest transfers
    best = career_stats.best_season(lines)
    with season_card:
        if best is None:
            ui.label("No league table yet.").classes("side-note")
        else:
            league = best["league"]
            position = league["position"]
            ui.label(f"{league['points']:.0f} pts").classes("big-score")
            ui.label(best["season"] + (" (in progress)" if best["in_progress"] else "")).classes("record-main")
            ui.label(f"{season_stats.ordinal(position) if isinstance(position, int) else '-'} in {league['competition']}") \
                .classes("side-note")

    for card, direction, empty in [(signing_card, "IN", "No signing with a fee yet."),
                                   (sale_card, "OUT", "No sale with a fee yet.")]:
        deal = career_stats.biggest_deal(seasons, direction)
        with card:
            if deal is None:
                ui.label(empty).classes("side-note")
                continue
            ui.label(season_stats.money(deal["fee"])).classes("big-score")
            with ui.row().classes("items-center gap-2 no-wrap min-w-0"):
                if deal["position"]:
                    ui.label(deal["position"]).classes(f"pos pos-{deal['group']}")
                ui.label(deal["player"]).classes("record-main")
            club = f"{'from' if direction == 'IN' else 'to'} {deal['club']}, " if deal["club"] else ""
            ui.label(f"{club}{deal['season']}").classes("side-note")

    # Following the competition: biggest win and player records
    def refresh() -> None:
        competition = None if state["competition"] == ALL_COMPETITIONS else state["competition"]

        win_card.clear()
        with win_card:
            ui.label("Biggest win").classes("section-title")
            match = career_stats.biggest_win(seasons, competition)
            if match is None:
                ui.label("No win yet.").classes("side-note")
            else:
                ui.label(match["score"].split(" (")[0]).classes("big-score")
                ui.label(f"{'vs' if match['venue'] == 'H' else 'at'} {match['opponent']}").classes("record-main")
                ui.label(", ".join(p for p in [match["competition"], match["season"]] if p)).classes("side-note")

        players = career_stats.player_careers(seasons, competition)
        players_grid.clear()
        with players_grid:
            for key, title in career_stats.PLAYER_RECORDS:
                with ui.column().classes("panel record-card gap-1"):
                    ui.label(title).classes("section-title")
                    top = career_stats.top_players(players, key)
                    if not top:
                        ui.label("Nobody yet.").classes("side-note")
                        continue
                    for rank, player in enumerate(top, start=1):
                        with ui.element("div").classes("record-line w-full"):
                            ui.label(str(rank)).classes("rank")
                            with ui.element("div").classes("who"):
                                if player["position"]:
                                    ui.label(player["position"]) \
                                        .classes(f"pos pos-{football.position_group(player['position'])}")
                                ui.label(player["name"]).classes("name")
                                count = player["season_count"]
                                ui.label(f"{count} {'season' if count == 1 else 'seasons'}").classes("season-count")
                            value = f"{player['rating']:.2f}" if key == "rating" else str(player[key])
                            ui.label(value).classes("value")

    def change_competition(competition: str | None) -> None:
        state["competition"] = competition or ALL_COMPETITIONS
        refresh()

    refresh()
