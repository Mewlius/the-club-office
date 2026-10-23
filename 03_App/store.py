"""Read the app's own copy of the exports (data/careers/...).

Layout:
    data/careers/<club> - <save id>/career.json
    data/careers/<club> - <save id>/<season>/TEAM_<id>_<KIND>_<season>.csv
    data/careers/<club> - <save id>/<season>/tco_state_TEAM_<id>.txt
"""
import csv
import json
from pathlib import Path

import settings

NUMERIC_COLUMNS = {
    "playerid", "teamid", "career_teamid", "age", "overall", "potential", "growth_gap",
    "contract_end", "contract_duration_months", "height", "weight", "preferred_foot",
    "skill_moves", "weak_foot", "is_retiring", "compobjid", "appearances", "MOTMs", "goals",
    "assists", "goal_contributions", "yellow_cards", "two_yellow", "red_cards", "saves",
    "goals_conceded", "cleansheets", "position", "home_teamid", "away_teamid", "fixtureid",
    "points", "wins", "draws", "losses", "goals_for", "goals_against", "goal_difference",
    "fee", "total_deal_value", "date", "time", "match_group_id", "home_score", "away_score",
    "home_penalties", "away_penalties", "exchangeplayerid", "teamfromid", "teamtoid", "squad_role_id",
    # "played" is a number in the standings ("true"/"false" in the fixtures stays text)
    "played", "home_wins", "home_draws", "home_losses", "home_goals_for", "home_goals_against",
    "away_wins", "away_draws", "away_losses", "away_goals_for", "away_goals_against",
}
DECIMAL_COLUMNS = {"AVG"}


# ----------------------------------------------------------------------
# Files
# ----------------------------------------------------------------------

def find_file(season_dir: Path, kind: str) -> Path | None:
    marker = settings.FILE_KINDS[kind]
    files = sorted(season_dir.glob(f"TEAM_*_{marker}_*.csv"))
    return files[0] if files else None


def has_any_export(season_dir: Path) -> bool:
    return any(find_file(season_dir, kind) for kind in settings.FILE_KINDS)


def read_csv_raw(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8", errors="replace") as file:
        return list(csv.DictReader(file, delimiter=";"))


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
            return value or None

    return value


def read_rows(path: Path) -> list[dict]:
    """CSV rows with numbers converted (for the pages)."""
    return [{column: _convert(column, value or "") for column, value in row.items()} for row in read_csv_raw(path)]


def read_state(season_dir: Path) -> dict:
    """What tco_session.lua exported last (tco_state_TEAM_<id>.txt)."""
    state = {}

    for path in season_dir.glob("tco_state_TEAM_*.txt"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                state[key.strip()] = value.strip()

    return state


def season_progress(season_dir: Path) -> dict:
    """How far the season is: matches played by the club, appearances of the
    current squad (players who left the club are not counted)."""
    played = None
    appearances = None

    fixtures = find_file(season_dir, "fixtures")

    if fixtures:
        played = sum(1 for row in read_csv_raw(fixtures) if row.get("played") == "true")

    stats = find_file(season_dir, "player_stats")

    if stats:
        appearances = 0

        for row in read_csv_raw(stats):
            if row.get("row_type") == "TOTAL" and row.get("left_club") != "true":
                try:
                    appearances += int(float(row.get("appearances") or 0))
                except ValueError:
                    pass

    return {"played": played, "appearances": appearances}


# ----------------------------------------------------------------------
# Careers and seasons (app copy)
# ----------------------------------------------------------------------

def career_dir(folder: str) -> Path:
    return settings.DATA_DIR / folder


def read_career(folder: str) -> dict | None:
    path = career_dir(folder) / "career.json"

    if not path.exists():
        return None

    try:
        career = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    career["folder"] = folder
    return career


def write_career(career: dict) -> None:
    """Atomic write: a .tmp file first, then it replaces the old one."""
    path = career_dir(career["folder"]) / "career.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(career, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def list_careers() -> list[dict]:
    if not settings.DATA_DIR.is_dir():
        return []

    careers = [read_career(p.name) for p in settings.DATA_DIR.iterdir() if p.is_dir()]
    careers = [c for c in careers if c]
    return sorted(careers, key=lambda c: (c.get("club_name", "").lower(), c["folder"]))


def career_label(career: dict, careers: list[dict]) -> str:
    """The club name, plus the save id when two careers share the club."""
    same_club = [c for c in careers if c.get("club_name") == career.get("club_name")]

    if len(same_club) > 1:
        return f"{career.get('club_name')} ({career.get('save_id') or career['folder']})"

    return career.get("club_name") or career["folder"]


def list_seasons(folder: str) -> list[str]:
    base = career_dir(folder)

    if not base.is_dir():
        return []

    return sorted(p.name for p in base.iterdir() if p.is_dir() and has_any_export(p))


def season_summary(folder: str, season: str) -> dict:
    season_dir = career_dir(folder) / season
    state = read_state(season_dir)
    progress = season_progress(season_dir)
    return {
        "season": season,
        "files": {kind: find_file(season_dir, kind) is not None for kind in settings.FILE_KINDS},
        "game_date": state.get("game_date"),
        "played": progress["played"],
        "appearances": progress["appearances"],
    }
