"""Paths and constants shared by the whole app."""
import os
from pathlib import Path

APP_DIR = Path(__file__).parent

# The app's own copy of the exports (one folder per career, then per season).
DATA_DIR = Path(os.environ.get("TCO_DATA", APP_DIR / "data" / "careers"))

# The four files written by 02_Lua/tco_session.lua, by kind.
# The marker is the middle of the file name: TEAM_<id>_<MARKER>_<season>.csv
FILE_KINDS = {
    "player_stats": "SEASON_PLAYER_STATS",
    "transfers": "SEASON_TRANSFERS",
    "fixtures": "FIXTURES",
    "standings": "LEAGUE_STANDINGS",
}

FILE_LABELS = {
    "player_stats": "Player stats",
    "transfers": "Transfers",
    "fixtures": "Fixtures",
    "standings": "Standings",
}

# Previous versions of each file kept in the app's copy (<season>/previous/).
BACKUP_COUNT = 3

# Logos, banners and colours: assets/careers/<career>/ (theme.json, never on
# GitHub) and the app's own logo in assets/app/ (used when a career has none).
ASSETS_DIR = Path(os.environ.get("TCO_ASSETS", APP_DIR / "assets"))


def careers_assets_dir() -> Path:
    return ASSETS_DIR / "careers"


def app_assets_dir() -> Path:
    return ASSETS_DIR / "app"


def exports_root() -> Path:
    """Documents/TheClubOffice/exports, found the same way as tco_session.lua."""
    override = os.environ.get("TCO_EXPORTS")

    if override:
        return Path(override)

    candidates = []

    if os.environ.get("USERPROFILE"):
        candidates.append(Path(os.environ["USERPROFILE"]) / "Documents")

    if os.environ.get("OneDrive"):
        candidates.append(Path(os.environ["OneDrive"]) / "Documents")

    candidates.append(Path.home() / "Documents")

    for documents in candidates:
        exports = documents / "TheClubOffice" / "exports"

        if exports.is_dir():
            return exports

    return candidates[0] / "TheClubOffice" / "exports"


def deleted_root() -> Path:
    """Documents/TheClubOffice/deleted: where deleted careers go (nothing is erased)."""
    return exports_root().parent / "deleted"
