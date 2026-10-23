"""Careers: every career (one per FC 26 save), to rename it, give it an identity
(logo, banner, colours) or delete it."""
import base64

from nicegui import app, ui

import careers
import identity
import layout
import settings
import store

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}


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


def identity_dialog(career: dict, label: str) -> None:
    """Logo, banner, main and second colour of a career, with a live preview.
    Nothing is saved before Save."""
    folder = career["folder"]
    saved = identity.load_theme(folder)
    state = {
        "primary": identity.parse_colour(saved.get("primary")),
        "secondary": identity.parse_colour(saved.get("secondary")),
        # Images: None = unchanged, bytes = a new image, "remove" = removed
        "logo": None,
        "banner": None,
    }
    current = {kind: identity.image_url(folder, kind) for kind in identity.IMAGE_KINDS}
    statuses, inputs = {}, {}

    def image_src(kind: str) -> str | None:
        pending = state[kind]
        if isinstance(pending, bytes):
            mime = MIME[identity.image_extension(pending)]
            return f"data:{mime};base64,{base64.b64encode(pending).decode()}"
        if pending == "remove" or not current[kind]:
            return identity.app_logo_url() if kind == "logo" else None
        return current[kind]

    def refresh() -> None:
        colours = identity.colours({"primary": state["primary"], "secondary": state["secondary"]})
        logo, banner = image_src("logo"), image_src("banner")
        preview.clear()
        with preview:
            with ui.element("div").classes("bar").style(f"background-color: {colours['header']}"):
                if banner:  # the banner, then the see-through header colour over it (as in the header)
                    ui.image(banner).props("fit=cover no-spinner no-transition").classes("bar-banner")
                    ui.element("div").classes("bar-overlay") \
                        .style(f"background: {identity.header_overlay(colours['header'])}")
                if logo:
                    ui.image(logo).props("fit=contain no-spinner no-transition").classes("preview-logo")
                ui.label(store.career_name(career)).classes("name")
                ui.label("Standings").classes("menu").style(f"border-bottom-color: {colours['nav']}")
            with ui.element("div").classes("body").style(f"background: {colours['paper']}"):
                ui.label("1st").classes("figure").style(f"color: {colours['figures']}")
                ui.label("Overall").classes("chip").style(f"background: {colours['primary']}")
                ui.label("Your club").classes("row-sample").style(
                    f"background: {colours['highlight_soft']}; color: {colours['highlight']}; "
                    f"box-shadow: inset 4px 0 0 {colours['highlight']}")
        for kind, status in statuses.items():
            pending = state[kind]
            if isinstance(pending, bytes):
                status.set_text("New image (saved with Save)")
            elif pending == "remove" or not current[kind]:
                status.set_text("The app logo" if kind == "logo" and identity.app_logo_url() else "No image")
            else:
                status.set_text("Current image")

    async def receive(event, kind: str) -> None:
        data = await event.file.read()
        if identity.image_extension(data) is None:
            ui.notify("Choose a PNG, JPG or WEBP image", type="warning", position="bottom-right")
        else:
            state[kind] = data
            refresh()
        event.sender.reset()

    def remove(kind: str) -> None:
        state[kind] = "remove"
        refresh()

    def set_colour(key: str, value: str | None) -> None:
        state[key] = identity.parse_colour(value)
        refresh()

    def default_look() -> None:
        for key in ("primary", "secondary"):
            inputs[key].set_value("")
        for kind in identity.IMAGE_KINDS:
            state[kind] = "remove"
        refresh()

    def save() -> None:
        try:
            for kind in identity.IMAGE_KINDS:
                if isinstance(state[kind], bytes):
                    identity.set_image(folder, kind, state[kind])
                elif state[kind] == "remove":
                    identity.remove_image(folder, kind)
            identity.set_colours(folder, state["primary"], state["secondary"])
        except (OSError, ValueError) as error:
            ui.notify(f"The identity could not be saved: {error}", type="negative", position="bottom-right",
                      multi_line=True)
            return
        dialog.close()
        ui.notify("Identity saved", type="positive", position="bottom-right")
        ui.navigate.reload()

    with ui.dialog() as dialog, ui.card().classes("dialog-card identity-card gap-2"):
        ui.label(f"Identity of {label}").classes("side-title")
        ui.label("Everything is optional. The colours are adjusted so that the text stays readable.") \
            .classes("side-note")
        preview = ui.element("div").classes("identity-preview w-full")

        for kind, title in [("logo", "Logo"), ("banner", "Banner (behind the header)")]:
            ui.label(title).classes("section-title")
            with ui.row().classes("items-center gap-3 no-wrap w-full"):
                statuses[kind] = ui.label().classes(f"image-status {kind}-status")
                ui.upload(on_upload=lambda e, k=kind: receive(e, k), auto_upload=True,
                          max_file_size=identity.MAX_IMAGE_BYTES,
                          on_rejected=lambda: ui.notify("The image is too big (more than 5 MB)", type="warning",
                                                        position="bottom-right")) \
                    .props('accept=".png,.jpg,.jpeg,.webp" flat bordered label="Choose an image"') \
                    .classes(f"identity-upload {kind}-upload")
                ui.button("Remove", on_click=lambda k=kind: remove(k)).props("flat dense no-caps") \
                    .classes(f"remove-{kind}")

        for key, title in [("primary", "Main colour (header and page background)"),
                           ("secondary", "Second colour (highlights and big figures)")]:
            ui.label(title).classes("section-title")
            with ui.row().classes("items-center gap-2 w-full no-wrap"):
                swatches = ui.row().classes("gap-1")
                inputs[key] = ui.color_input("Colour code", value=state[key] or "",
                                             on_change=lambda e, k=key: set_colour(k, e.value)) \
                    .props("outlined dense clearable").classes(f"w-40 {key}-input")
            with swatches:
                for name, colour in identity.SWATCHES:
                    ui.button(on_click=lambda c=colour, k=key: inputs[k].set_value(c)) \
                        .props("round dense unelevated").style(f"background: {colour} !important") \
                        .classes(f"swatch {key}-swatch").tooltip(name)

        with ui.row().classes("w-full justify-between items-center"):
            ui.button("Default look", on_click=default_look).props("flat no-caps")
            with ui.row().classes("gap-2"):
                ui.button("Cancel", on_click=dialog.close).props("flat no-caps")
                ui.button("Save", on_click=save).props("unelevated no-caps")

    refresh()
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
            ui.label("One career per FC 26 save. Rename a career, give it a logo, a banner and colours, "
                     "or delete the career of a save you no longer use.").classes("page-note")

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
                        logo = identity.image_url(career["folder"], "logo")
                        if logo:
                            ui.image(logo).props("fit=contain no-spinner no-transition").classes("career-logo")
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
                        ui.button("Identity", icon="palette", on_click=lambda c=career, l=label: identity_dialog(c, l)) \
                            .props("flat dense no-caps")
                        ui.button("Delete", icon="delete", on_click=lambda c=career, l=label: delete_dialog(c, l)) \
                            .props("flat dense no-caps color=negative")

        ui.label(f"Deleted careers are kept in {settings.deleted_root()}.").classes("page-note")
