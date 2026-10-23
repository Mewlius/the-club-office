"""Copy the exports written by tco_session.lua into the app's own data.

Rules:
- a career is created automatically the first time its folder is seen;
- a file is copied when it is new or has changed;
- the replaced version is kept in <season>/previous/ (3 versions);
- SAFETY: if the export looks behind the app's copy (fewer matches played,
  or squad appearances back to zero), the season is NOT updated. It is
  reported as "protected" and can be replaced on purpose from the app;
- nothing is ever deleted from the app's copy, even if an export disappears.
"""
import re
import shutil
from datetime import datetime
from pathlib import Path

import settings
import store

STATE_PATTERN = "tco_state_TEAM_*.txt"

# Result of the last run, shown by the app
last_report: list[dict] = []
last_run: datetime | None = None


# ----------------------------------------------------------------------
# Career identity
# ----------------------------------------------------------------------

def _career_from_export(export_career: Path) -> dict:
    """Club name, team id and save id, read from the export folder."""
    folder = export_career.name
    club_name = folder.rsplit(" - ", 1)[0]
    save_id = folder.rsplit(" - ", 1)[1] if " - " in folder else ""
    team_id = None

    for season_dir in sorted(p for p in export_career.iterdir() if p.is_dir()):
        stats = store.find_file(season_dir, "player_stats")
        any_file = stats or next((store.find_file(season_dir, k) for k in settings.FILE_KINDS
                                  if store.find_file(season_dir, k)), None)

        if any_file and team_id is None:
            match = re.match(r"TEAM_(\d+)_", any_file.name)
            team_id = int(match.group(1)) if match else None

        if stats:
            rows = store.read_csv_raw(stats)

            # The real club name, with accents (the folder name has none)
            if rows and rows[0].get("teamname"):
                club_name = rows[0]["teamname"]
                break

    return {
        "folder": folder,
        "club_name": club_name,
        "team_id": team_id,
        "save_id": save_id,
        "first_seen": datetime.now().isoformat(timespec="seconds"),
    }


# ----------------------------------------------------------------------
# Safe copy
# ----------------------------------------------------------------------

def _backup(path: Path) -> None:
    """Keeps a copy of the file in previous/ (prev1 = most recent)."""
    previous = path.parent / "previous"
    previous.mkdir(exist_ok=True)

    def numbered(number: int) -> Path:
        return previous / f"{path.stem}_prev{number}{path.suffix}"

    numbered(settings.BACKUP_COUNT).unlink(missing_ok=True)

    for number in range(settings.BACKUP_COUNT - 1, 0, -1):
        if numbered(number).exists():
            numbered(number).replace(numbered(number + 1))

    shutil.copy2(path, numbered(1))


def _copy_safely(source: Path, target: Path) -> None:
    """Writes a .tmp file next to the target, then replaces it in one step."""
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        _backup(target)

    tmp = target.with_name(target.name + ".tmp")
    shutil.copyfile(source, tmp)
    tmp.replace(target)


def _same_content(a: Path, b: Path) -> bool:
    return a.exists() and b.exists() and a.read_bytes() == b.read_bytes()


# ----------------------------------------------------------------------
# Safety check
# ----------------------------------------------------------------------

def _behind(export_dir: Path, app_dir: Path) -> str | None:
    """Why the export looks older than the app's copy, or None."""
    new = store.season_progress(export_dir)
    old = store.season_progress(app_dir)

    if new["played"] is not None and old["played"] is not None and new["played"] < old["played"]:
        return f"the export has {new['played']} matches played, the app already has {old['played']}"

    if old["appearances"] and new["appearances"] == 0:
        return f"the export has no appearance, the app already has {old['appearances']}"

    return None


# ----------------------------------------------------------------------
# Sync
# ----------------------------------------------------------------------

def sync_season(export_season: Path, folder: str, force: bool = False) -> dict:
    season = export_season.name
    app_season = store.career_dir(folder) / season
    result = {"folder": folder, "season": season, "status": "unchanged", "changed": [], "reason": None}

    # Files that differ from the app's copy
    changes = []

    for kind in settings.FILE_KINDS:
        source = store.find_file(export_season, kind)

        if source is None:
            continue

        target = app_season / source.name
        current = store.find_file(app_season, kind) if app_season.is_dir() else None

        if current is not None and current.name != source.name:
            target = current  # same kind, keep the app's file name

        if not _same_content(source, target):
            changes.append((kind, source, target))

    states = sorted(export_season.glob(STATE_PATTERN))
    state_changes = [(s, app_season / s.name) for s in states if not _same_content(s, app_season / s.name)]

    if not changes and not state_changes:
        return result

    is_new = not (app_season.is_dir() and store.has_any_export(app_season))

    if not is_new and not force:
        reason = _behind(export_season, app_season)

        if reason:
            result.update(status="protected", reason=reason)
            return result

    for kind, source, target in changes:
        _copy_safely(source, target)
        result["changed"].append(kind)

    for source, target in state_changes:
        _copy_safely(source, target)

    result["status"] = "new" if is_new else "updated"
    return result


def sync_all(exports_root: Path | None = None) -> list[dict]:
    """Copies every new or changed export. Returns one line per season."""
    global last_report, last_run

    root = exports_root or settings.exports_root()
    report = []

    if root.is_dir():
        for export_career in sorted(p for p in root.iterdir() if p.is_dir()):
            seasons = sorted(p for p in export_career.iterdir() if p.is_dir() and store.has_any_export(p))

            if not seasons:
                continue

            folder = export_career.name

            if store.read_career(folder) is None:
                store.write_career(_career_from_export(export_career))

            for export_season in seasons:
                try:
                    report.append(sync_season(export_season, folder))
                except OSError as error:
                    report.append({"folder": folder, "season": export_season.name, "status": "error",
                                   "changed": [], "reason": str(error)})

    last_report = report
    last_run = datetime.now()
    return report


def force_season(folder: str, season: str, exports_root: Path | None = None) -> dict:
    """Replaces a protected season with the export, on purpose."""
    root = exports_root or settings.exports_root()
    result = sync_season(root / folder / season, folder, force=True)

    for index, line in enumerate(last_report):
        if line["folder"] == folder and line["season"] == season:
            last_report[index] = result

    return result
