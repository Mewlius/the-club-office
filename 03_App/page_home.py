"""Home: the selected season at a glance."""
from nicegui import ui

import layout
import page_data
import season_stats
import store


def stat(value, caption: str) -> None:
    with ui.element("div").classes("stat"):
        ui.label(str(value)).classes("value")
        ui.label(caption).classes("caption")


def result_chip(match: dict, big: bool = False):
    chip = ui.label(match["result"] or "?").classes(f"res res-{match['result']}")
    chip.tooltip(f"{match['score']} {'vs' if match['venue'] == 'H' else 'at'} {match['opponent']}, "
                 f"{match['competition']} {match['date_text']}".strip())
    return chip


def snapshot(summary: dict) -> None:
    league = summary["league"]
    form = summary["matches"]["form"]

    with ui.element("div").classes("panel w-full"):
        if league is None and not form:
            ui.label("No league table or result exported yet for this season.").classes("home-note")
            return

        with ui.element("div").classes("snapshot"):
            if league:
                stat(season_stats.ordinal(league["position"]) if isinstance(league["position"], int) else "-",
                     f"{league['competition']}, {league['teams']} teams")
                stat(f"{league['points']:.0f}", f"points in {league['played']:.0f} matches")
                stat(f"{league['wins']:.0f}-{league['draws']:.0f}-{league['losses']:.0f}", "won, drawn, lost")
                gd = league["goal_difference"]
                stat(f"+{gd:.0f}" if gd > 0 else f"{gd:.0f}",
                     f"goal difference ({league['goals_for']:.0f} scored, {league['goals_against']:.0f} conceded)")
            with ui.element("div").classes("stat"):
                with ui.element("div").classes("form"):
                    for match in form:
                        result_chip(match)
                    if not form:
                        ui.label("-").classes("value")
                ui.label("last 5 matches, all competitions").classes("caption")


def match_list(title: str, matches: list[dict], empty: str) -> None:
    ui.label(title).classes("panel-subtitle")
    if not matches:
        ui.label(empty).classes("home-note")
        return
    with ui.element("div").classes("w-full"):
        for match in matches:
            with ui.element("div").classes("match-row"):
                ui.label(match["date_text"]).classes("when")
                if match["played"]:
                    result_chip(match)
                else:
                    ui.element("div")
                with ui.column().classes("gap-0 min-w-0"):
                    with ui.row().classes("gap-1 no-wrap min-w-0"):
                        ui.label(match["opponent"]).classes("who")
                        ui.label(f"({match['venue']})").classes("venue")
                    ui.label(match["competition"]).classes("comp")
                ui.label(match["score"].split(" (")[0] if match["played"] else "").classes("score") \
                    .tooltip(match["score"] if "pens" in match["score"] else "")


def matches_panel(summary: dict) -> None:
    info = summary["matches"]
    with ui.column().classes("panel w-full gap-2"):
        ui.link("Matches", "/matches").classes("panel-title title-link")
        if not summary["has"]["fixtures"]:
            ui.label("No fixtures exported yet for this season.").classes("home-note")
            return
        match_list("Last results", info["last"], "No match played yet.")
        match_list("Next matches", info["next"], "No match left this season.")
        ui.link("All matches", "/matches").classes("home-note")


def leaders_panel(summary: dict) -> None:
    with ui.column().classes("panel w-full gap-2"):
        ui.link("Players of the season", "/player-stats").classes("panel-title title-link")
        if not summary["leaders"]:
            ui.label("No player stats exported yet for this season.").classes("home-note")
            return
        with ui.element("div").classes("w-full"):
            for leader in summary["leaders"]:
                with ui.element("div").classes("leader-row"):
                    ui.label(leader["label"]).classes("what")
                    with ui.element("div").classes("who"):
                        if leader["player"]:
                            ui.label(leader["position"] or "").classes(f"pos pos-{leader['group']}")
                            ui.label(leader["player"])
                        else:
                            ui.label("Nobody yet").classes("home-note")
                    ui.label(leader["value"]).classes("value")
        ui.link("All player stats", "/player-stats").classes("home-note")


def squad_panel(summary: dict) -> None:
    squad = summary["squad"]
    transfers = summary["transfers"]
    with ui.column().classes("panel w-full gap-2"):
        ui.label("Squad").classes("panel-title")
        if squad is None:
            ui.label("No player stats exported yet for this season.").classes("home-note")
        else:
            with ui.element("div").classes("facts"):
                for key, value in [("Players", squad["size"]), ("Average age", squad["age"]),
                                   ("Average OVR", squad["overall"]), ("Average POT", squad["potential"])]:
                    ui.label(key).classes("k")
                    ui.label(str(value))
            ending = squad["contracts_ending"]
            if squad["season_end"]:
                label = "contract ends" if len(ending) == 1 else "contracts end"
                ui.label(f"{len(ending)} {label} in {squad['season_end']}" if ending
                         else f"No contract ends in {squad['season_end']}").classes("panel-subtitle")
                if ending:
                    ui.label(", ".join(ending)).classes("names")

        ui.label("Transfer window").classes("panel-subtitle")
        if transfers is None:
            ui.label("No transfers exported yet for this season.").classes("home-note")
            return
        with ui.element("div").classes("facts"):
            arrivals = f"{transfers['in']}" + (f" (of which {transfers['loans_in']} on loan)" if transfers["loans_in"] else "")
            departures = f"{transfers['out']}" + (f" (of which {transfers['loans_out']} on loan)" if transfers["loans_out"] else "")
            ui.label("Arrivals").classes("k")
            ui.label(arrivals)
            ui.label("Departures").classes("k")
            ui.label(departures)
            ui.label("Spent").classes("k")
            ui.label(season_stats.money(transfers["spent"]))
            ui.label("Received").classes("k")
            ui.label(season_stats.money(transfers["received"]))
            ui.label("Net spend").classes("k")
            net = transfers["net_spend"]
            ui.label(season_stats.money(net)).classes("money-out" if net > 0 else "money-in" if net < 0 else "")


@ui.page("/")
def home() -> None:
    with layout.frame("/") as (career, season):
        if career is None:
            return

        page_data.show_warnings(store.list_careers())

        if season is None:
            ui.label("No season exported yet for this career.").classes("page-note")
            return

        summary = season_stats.season_summary(career, season)
        ui.label(f"Season {season}").classes("page-title")
        snapshot(summary)

        with ui.element("div").classes("home-grid w-full"):
            matches_panel(summary)
            leaders_panel(summary)
            squad_panel(summary)

        with ui.row().classes("gap-1 home-note"):
            ui.label(f"Last export: {layout.format_game_date(summary['state'].get('game_date'))} in the game.")
            ui.link("See the data files", "/data")
