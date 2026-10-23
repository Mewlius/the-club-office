"""Shared frame of every page: header with career, season, pages and reload."""
from contextlib import contextmanager
from datetime import date

from nicegui import app, ui

import settings
import store
import sync
import theme

# Pages shown in the header: (path, label). New pages are added here.
PAGES = [
    ("/", "Home"),
    ("/matches", "Matches"),
    ("/standings", "Standings"),
    ("/player-stats", "Player stats"),
    ("/transfers", "Transfers"),
    ("/history", "History"),
]


# ----------------------------------------------------------------------
# Selected career and season (remembered, even after closing the app)
# ----------------------------------------------------------------------

def current_career() -> dict | None:
    careers = store.list_careers()

    if not careers:
        return None

    folder = app.storage.general.get("career")
    return next((c for c in careers if c["folder"] == folder), careers[0])


def current_season(career: dict | None) -> str | None:
    if career is None:
        return None

    seasons = store.list_seasons(career["folder"])

    if not seasons:
        return None

    remembered = app.storage.general.get("seasons", {}).get(career["folder"])
    return remembered if remembered in seasons else seasons[-1]


def select_career(folder: str) -> None:
    app.storage.general["career"] = folder
    ui.navigate.reload()


def select_season(folder: str, season: str, go_to: str | None = None) -> None:
    """Remembers the season, then reloads the page (or opens the page go_to)."""
    seasons = dict(app.storage.general.get("seasons", {}))
    seasons[folder] = season
    app.storage.general["seasons"] = seasons
    if go_to:
        ui.navigate.to(go_to)
    else:
        ui.navigate.reload()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def format_game_date(text: str | None) -> str:
    try:
        return date.fromisoformat(text or "").strftime("%d %b %Y").lstrip("0")
    except ValueError:
        return "-"


def reload_files() -> None:
    report = sync.sync_all()
    changed = sum(1 for line in report if line["status"] in ("new", "updated"))
    protected = sum(1 for line in report if line["status"] in ("protected", "error"))

    if protected:
        ui.notify(f"{protected} season(s) not updated: see Home", type="warning", position="bottom-right")
    elif changed:
        ui.notify(f"{changed} season(s) updated", type="positive", position="bottom-right")
    else:
        ui.notify("Already up to date", position="bottom-right")

    ui.navigate.reload()


# ----------------------------------------------------------------------
# Frame
# ----------------------------------------------------------------------

@contextmanager
def frame(path: str, wide: bool = False):
    """Header + page column. Yields (career, season). wide: for pages with a big table."""
    theme.apply()
    careers = store.list_careers()
    career = current_career()
    season = current_season(career)

    with ui.header().classes("tco-header items-center no-wrap"):
        if career:
            ui.select(
                {c["folder"]: store.career_label(c, careers) for c in careers},
                value=career["folder"],
                on_change=lambda e: select_career(e.value),
            ).props("dark borderless dense options-dense behavior=menu").classes("club-select")

            seasons = store.list_seasons(career["folder"])
            ui.select(
                seasons,
                value=season,
                label="Season",
                on_change=lambda e: select_season(career["folder"], e.value),
            ).props("dark borderless dense options-dense behavior=menu label-color=grey-5").classes("season-select")

            with ui.row().classes("gap-5 no-wrap"):
                for page_path, label in PAGES:
                    link = ui.link(label, page_path).classes("nav-link")
                    if page_path == path:
                        link.classes("active")
        else:
            ui.label("The Club Office").classes("cond text-2xl font-bold")

        ui.space()

        if sync.last_run:
            ui.link(f"Files read at {sync.last_run:%H:%M}", "/data").classes("sync-note") \
                .tooltip("See the data files of each season")

        ui.button("Reload files", icon="refresh", on_click=reload_files).props("flat dense no-caps color=white")

    with ui.column().classes("page w-full gap-4" + (" wide" if wide else "")):
        if career is None:
            empty_state()
            yield None, None
        else:
            yield career, season


def empty_state() -> None:
    with ui.column().classes("empty gap-3"):
        ui.label("No career yet").classes("page-title")
        ui.label("The app shows the careers exported by tco_session.lua. None was found in this folder:")
        ui.label(str(settings.exports_root())).classes("path")
        ui.label("In FC 26, load your career and run 02_Lua/tco_session.lua (F9, Lua Engine, Execute). "
                 "Then click Reload files.").classes("page-note")
