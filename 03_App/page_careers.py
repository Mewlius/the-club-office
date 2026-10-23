"""Careers: every career (one per FC 26 save), to rename or delete them."""
from nicegui import app, ui

import careers
import layout
import settings
import store


def rename_dialog(career: dict, label: str) -> None:
    with ui.dialog() as dialog, ui.card().classes("dialog-card gap-3"):
        ui.label(f"Rename {label}").classes("side-title")
        field = ui.input("Name", value=career.get("display_name") or "", placeholder=career.get("club_name") or "") \
            .props(f"outlined dense autofocus maxlength={careers.MAX_NAME_LENGTH}").classes("w-full rename-field")
        ui.label("Leave it empty to show the club name again. The files and the game are not changed.") \
            .classes("side-note")

        def save() -> None:
            careers.rename_career(career["folder"], field.value)
            dialog.close()
            ui.notify("Career renamed", type="positive", position="bottom-right")
            ui.navigate.reload()

        field.on("keydown.enter", save)
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps")
            ui.button("Save", on_click=save).props("unelevated no-caps")
    dialog.open()


def delete_dialog(career: dict, label: str) -> None:
    with ui.dialog() as dialog, ui.card().classes("dialog-card gap-3"):
        ui.label(f"Delete {label}?").classes("side-title")
        ui.label("Its data in the app and its export folder will be moved to:")
        ui.label(str(settings.deleted_root())).classes("path")
        ui.label("Nothing is erased: you can move them back (a README.txt in the folder explains how). "
                 "If this save is loaded again in FC 26 with tco_session.lua, the career comes back.") \
            .classes("side-note")

        def delete() -> None:
            try:
                careers.delete_career(career["folder"])
            except (OSError, ValueError) as error:
                ui.notify(f"The career could not be deleted: {error}", type="negative", position="bottom-right",
                          multi_line=True)
                return
            # The career shown in the header: another one is picked
            if app.storage.general.get("career") == career["folder"]:
                app.storage.general.pop("career", None)
            dialog.close()
            ui.notify(f"{label} moved to the deleted folder", type="positive", position="bottom-right")
            ui.navigate.reload()

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps")
            ui.button("Delete career", on_click=delete).props("unelevated no-caps color=negative")
    dialog.open()


@ui.page("/careers")
def careers_page() -> None:
    with layout.frame("/careers") as (current, season):
        if current is None:
            return

        all_careers = store.list_careers()

        with ui.column().classes("gap-0"):
            ui.label("Careers").classes("page-title")
            ui.label("One career per FC 26 save. Rename a career, or delete the career of a save "
                     "you no longer use.").classes("page-note")

        with ui.element("div").classes("seasons careers w-full"):
            with ui.element("div").classes("career-row head"):
                for title in ["Career", "Club", "Save", "Seasons", "Last export (game)", ""]:
                    ui.label(title)

            for career in all_careers:
                label = store.career_label(career, all_careers)
                seasons = store.list_seasons(career["folder"])
                last = store.read_state(store.career_dir(career["folder"]) / seasons[-1]).get("game_date") if seasons else None
                selected = career["folder"] == current["folder"]

                with ui.element("div").classes("career-row" + (" selected" if selected else "")):
                    with ui.row().classes("items-center gap-2 no-wrap min-w-0"):
                        ui.label(label).classes("career-name")
                        if selected:
                            ui.label("shown").classes("file ok").tooltip("The career shown in the app")
                    ui.label(career.get("club_name") or "-").classes("career-cell")
                    ui.label(career.get("save_id") or "-").classes("career-cell")
                    ui.label(str(len(seasons))).classes("career-cell")
                    ui.label(layout.format_game_date(last)).classes("career-cell")
                    with ui.row().classes("gap-1 no-wrap justify-end"):
                        ui.button("Rename", icon="edit", on_click=lambda c=career, l=label: rename_dialog(c, l)) \
                            .props("flat dense no-caps")
                        ui.button("Delete", icon="delete", on_click=lambda c=career, l=label: delete_dialog(c, l)) \
                            .props("flat dense no-caps color=negative")

        ui.label(f"Deleted careers are kept in {settings.deleted_root()}.").classes("page-note")
