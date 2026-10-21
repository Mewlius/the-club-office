"""Read the files written by 02_Lua/tco_session.lua.

Folder layout:
    Documents/TheClubOffice/exports/<club> - <save id>/<season>/TEAM_<id>_SEASON_PLAYER_STATS_<season>.csv

This part does not depend on the interface tool: it can be reused by any
version of the app (for example to import the files automatically).
"""
import csv
import os
from pathlib import Path

NUMERIC_COLUMNS = {
    "playerid", "teamid", "career_teamid", "age", "overall", "potential", "growth_gap",
    "contract_end", "contract_duration_months", "height", "weight", "preferred_foot",
    "skill_moves", "weak_foot", "is_retiring", "compobjid", "appearances", "MOTMs", "goals",
    "assists", "goal_contributions", "yellow_cards", "two_yellow", "red_cards", "saves",
    "goals_conceded", "cleansheets",
}

DECIMAL_COLUMNS = {"AVG"}

POSITION_GROUPS = {
    "GK": "gk",
    "SW": "def", "RWB": "def", "RB": "def", "RCB": "def", "CB": "def", "LCB": "def", "LB": "def", "LWB": "def",
    "RDM": "mid", "CDM": "mid", "LDM": "mid", "RM": "mid", "RCM": "mid", "CM": "mid", "LCM": "mid",
    "LM": "mid", "RAM": "mid", "CAM": "mid", "LAM": "mid",
    "RF": "att", "CF": "att", "LF": "att", "RW": "att", "RS": "att", "ST": "att", "LS": "att", "LW": "att",
}

# Goalkeepers first, then defence, midfield, attack (the usual squad sheet order)
POSITION_ORDER = ["GK", "SW", "RWB", "RB", "RCB", "CB", "LCB", "LB", "LWB", "RDM", "CDM", "LDM",
                  "RM", "RCM", "CM", "LCM", "LM", "RAM", "CAM", "LAM", "RF", "CF", "LF", "RW",
                  "RS", "ST", "LS", "LW"]


def find_exports_root() -> Path:
    """Same rule as tco_session.lua: Documents, or the OneDrive Documents folder."""
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


def stats_file(season_dir: Path) -> Path | None:
    files = sorted(season_dir.glob("TEAM_*_SEASON_PLAYER_STATS_*.csv"))
    return files[0] if files else None


def list_careers(root: Path) -> list[Path]:
    """Career folders that contain at least one season with player stats."""
    if not root.is_dir():
        return []

    careers = []

    for career in sorted(p for p in root.iterdir() if p.is_dir()):
        if any(stats_file(season) for season in career.iterdir() if season.is_dir()):
            careers.append(career)

    return careers


def career_label(career: Path, all_careers: list[Path]) -> str:
    """'AFC Wimbledon - 686228de' -> 'AFC Wimbledon', unless two careers share the club."""
    club = career.name.rsplit(" - ", 1)[0]
    same_club = [c for c in all_careers if c.name.rsplit(" - ", 1)[0] == club]
    return club if len(same_club) == 1 else career.name


def list_seasons(career: Path) -> list[str]:
    return sorted(p.name for p in career.iterdir() if p.is_dir() and stats_file(p))


def _convert(column: str, value: str):
    if column in DECIMAL_COLUMNS:
        try:
            return round(float(value), 2)
        except ValueError:
            return None

    if column in NUMERIC_COLUMNS:
        try:
            return int(float(value))
        except ValueError:
            return None

    return value


def load_player_stats(season_dir: Path) -> list[dict]:
    path = stats_file(season_dir)

    if path is None:
        return []

    with open(path, newline="", encoding="utf-8", errors="replace") as file:
        rows = [
            {column: _convert(column, value or "") for column, value in row.items()}
            for row in csv.DictReader(file, delimiter=";")
        ]

    for row in rows:
        row["pos_group"] = POSITION_GROUPS.get(row.get("position") or "", "mid")

    return rows


def read_state(season_dir: Path) -> dict:
    """What tco_session.lua exported last (tco_state_TEAM_<id>.txt)."""
    state = {}

    for path in season_dir.glob("tco_state_TEAM_*.txt"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                state[key.strip()] = value.strip()

    return state
