"""Data files: the seasons of the selected career and the state of their copied files."""
from nicegui import ui

import layout
import settings
import store
import sync

STATUS_TEXT = {
    "new": "New",
    "updated": "Updated",
    "unchanged": "Up to date",
    "protected": "Not updated",
    "error": "Error",
}


def force(folder: str, season: str) -> None:
    sync.force_season(folder, season)
    ui.notify(f"{season} replaced with the export", type="positive", position="bottom-right")
    ui.navigate.reload()


def show_warnings(careers: list[dict]) -> None:
    """Seasons the last reading did not update, for every career (also shown on Home)."""
    problems = [line for line in sync.last_report if line["status"] in ("protected", "error")]

    for line in problems:
        career = next((c for c in careers if c["folder"] == line["folder"]), None)
        name = store.career_label(career, careers) if career else line["folder"]
        with ui.column().classes("warning w-full gap-1"):
            if line["status"] == "protected":
                ui.label(f"{name}, {line['season']}: the export was not copied").classes("title")
                ui.label(f"It looks older than the app's copy: {line['reason']}. "
                         "This happens when the game resets a season or when an older save is loaded. "
                         "The app keeps its copy.")
                ui.button("Use the export anyway", on_click=lambda l=line: force(l["folder"], l["season"])) \
                    .props("flat dense no-caps color=warning").classes("self-start")
            else:
                ui.label(f"{name}, {line['season']}: the files could not be copied").classes("title")
                ui.label(line["reason"] or "")


@ui.page("/data")
def data_files() -> None:
    with layout.frame("/data") as (career, selected_season):
        if career is None:
            return

        careers = store.list_careers()
        show_warnings(careers)

        details = [f"Team id {career.get('team_id')}"]
        if career.get("save_id"):
            details.append(f"save {career['save_id']}")

        with ui.row().classes("w-full items-end justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("Data files").classes("page-title")
                ui.label(", ".join(details)).classes("page-note")
            ui.link("Manage careers", "/careers").classes("home-note manage-link")

        last_status = {line["season"]: line["status"] for line in sync.last_report if line["folder"] == career["folder"]}

        with ui.element("div").classes("seasons w-full"):
            with ui.element("div").classes("season-row head"):
                for title in ["Season", "Matches played", "Appearances", "Last export (game)", "Files", "Last reading"]:
                    ui.label(title)

            for season in reversed(store.list_seasons(career["folder"])):
                summary = store.season_summary(career["folder"], season)
                row = ui.element("div").classes("season-row" + (" selected" if season == selected_season else ""))
                row.on("click", lambda s=season: layout.select_season(career["folder"], s))

                with row:
                    ui.label(season).classes("season-name")
                    for value, caption in [(summary["played"], "matches played"), (summary["appearances"], "appearances")]:
                        with ui.element("div"):
                            ui.label("-" if value is None else str(value)).classes("big")
                            ui.label(caption).classes("cell-caption")
                    with ui.element("div"):
                        ui.label(layout.format_game_date(summary["game_date"]))
                        ui.label("last export (game)").classes("cell-caption")
                    with ui.element("div").classes("files"):
                        for kind, present in summary["files"].items():
                            ui.label(settings.FILE_LABELS[kind]).classes("file " + ("ok" if present else "missing")) \
                                .tooltip("Copied" if present else "Not exported yet")
                    status = last_status.get(season)
                    ui.label(STATUS_TEXT.get(status, "-")).classes(f"status {status or ''}")

        ui.label("The app copies the files of Documents\\TheClubOffice\\exports when it starts "
                 "and when you click Reload files. Click a season to select it.").classes("page-note")
