"""Career management (Careers page): rename a career, delete it.

Deleting never erases anything: the app's copy of the career and its export
folder are moved together to Documents/TheClubOffice/deleted/, in a dated
folder, so they can be moved back. Without its export folder, the career is
not created again by the next reading of the exports.
"""
import shutil
from datetime import datetime
from pathlib import Path

import settings
import store
import sync

MAX_NAME_LENGTH = 40

RESTORE_NOTE = """This career was deleted from The Club Office on {when}.

To get it back, close the app, then move:
- the folder "app data" back to {app_dir}
- the folder "exports" back to {export_dir}
Then start the app again.
"""


def _check_folder(folder: str) -> None:
    """A career folder name, never a path (protects every other folder)."""
    if not folder or folder in (".", "..") or Path(folder).name != folder:
        raise ValueError(f"not a career folder: {folder!r}")


def rename_career(folder: str, name: str) -> dict:
    """Saves the display name of a career (empty: the club name again).
    Only career.json changes: the files and the game are not touched."""
    _check_folder(folder)
    career = store.read_career(folder)

    if career is None:
        raise ValueError(f"no career in {folder!r}")

    name = " ".join((name or "").split())[:MAX_NAME_LENGTH]

    if name and name != career.get("club_name"):
        career["display_name"] = name
    else:
        career.pop("display_name", None)

    store.write_career(career)
    return career


def delete_career(folder: str) -> Path:
    """Moves the app's copy of the career and its export folder to the deleted
    folder. Returns the dated folder they were moved to.

    The export folder goes first: if it cannot be moved (a file open in another
    program), nothing has changed. If the app's copy then cannot be moved, the
    career is still in the app and the deletion can be tried again."""
    _check_folder(folder)
    app_dir = store.career_dir(folder)
    export_dir = settings.exports_root() / folder

    if not app_dir.is_dir() and not export_dir.is_dir():
        raise ValueError(f"no career in {folder!r}")

    when = datetime.now()
    target = settings.deleted_root() / f"{folder} (deleted {when:%Y-%m-%d %H-%M-%S})"
    number = 2

    while target.exists():
        target = target.with_name(f"{folder} (deleted {when:%Y-%m-%d %H-%M-%S}) {number}")
        number += 1

    target.mkdir(parents=True)
    (target / "README.txt").write_text(
        RESTORE_NOTE.format(when=f"{when:%d %B %Y at %H:%M}", app_dir=app_dir, export_dir=export_dir),
        encoding="utf-8")

    if export_dir.is_dir():
        shutil.move(str(export_dir), str(target / "exports"))

    if app_dir.is_dir():
        shutil.move(str(app_dir), str(target / "app data"))

    # The last reading no longer has anything to say about this career
    sync.last_report[:] = [line for line in sync.last_report if line["folder"] != folder]
    return target
