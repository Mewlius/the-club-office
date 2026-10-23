"""What the Home page shows about a season, computed from the app's copy.

Pure calculations (no interface): they read the four files of a season and
return plain dictionaries, so they can be tested and reused by other pages.
"""
from datetime import date

import football
import store


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------

def number(value) -> float:
    return value if isinstance(value, (int, float)) else 0


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def money(value) -> str:
    """15000000 -> 15.0M, 750000 -> 750K (in the club's currency)."""
    value = number(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{sign}{value / 1_000:.0f}K"
    return f"{sign}{value:.0f}"


def game_date(value) -> date | None:
    """A match date from the game, written as 20251207 (year, month, day).

    Any other format is not shown (the matches are still ordered by it)."""
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if not isinstance(value, int) or not 19000101 <= value <= 21001231:
        return None
    try:
        return date(value // 10000, value // 100 % 100, value % 100)
    except ValueError:
        return None


def short_date(value) -> str:
    parsed = game_date(value)
    return parsed.strftime("%d %b").lstrip("0") if parsed else ""


def _rows(folder: str, season: str, kind: str) -> list[dict] | None:
    path = store.find_file(store.career_dir(folder) / season, kind)
    return store.read_rows(path) if path else None


# ----------------------------------------------------------------------
# League position (standings file)
# ----------------------------------------------------------------------

def league(rows: list[dict] | None, team_id) -> dict | None:
    if not rows:
        return None
    club = next((r for r in rows if r.get("teamid") == team_id), None)
    if club is None:
        return None
    return {
        "competition": club.get("competition") or "League",
        "teams": len(rows),
        "position": club.get("position"),
        "points": number(club.get("points")),
        "played": number(club.get("played")),
        "wins": number(club.get("wins")),
        "draws": number(club.get("draws")),
        "losses": number(club.get("losses")),
        "goals_for": number(club.get("goals_for")),
        "goals_against": number(club.get("goals_against")),
        "goal_difference": number(club.get("goal_difference")),
    }


# ----------------------------------------------------------------------
# Matches (fixtures file)
# ----------------------------------------------------------------------

def _match(row: dict) -> dict:
    is_home = row.get("is_home") == "true"
    played = row.get("played") == "true"
    opponent = row.get("away_teamname") if is_home else row.get("home_teamname")
    score = ""
    if played:
        score = f"{row.get('home_score')}-{row.get('away_score')}"
        if row.get("home_penalties") not in (None, "") or row.get("away_penalties") not in (None, ""):
            score += f" ({row.get('home_penalties') or 0}-{row.get('away_penalties') or 0} pens)"
    return {
        "date": row.get("date"),
        "date_text": short_date(row.get("date")),
        "competition": row.get("competition") or "",
        "opponent": opponent or "",
        "venue": "H" if is_home else "A",
        "played": played,
        "result": row.get("result") if played else "",
        "score": score,
        "order": (number(row.get("date")), number(row.get("time")), number(row.get("fixtureid"))),
    }


def matches(rows: list[dict] | None) -> dict:
    """Last results (newest first), next matches (soonest first), form (oldest to newest)."""
    if not rows:
        return {"last": [], "next": [], "form": [], "played": 0}
    all_matches = sorted((_match(r) for r in rows), key=lambda m: m["order"])
    played = [m for m in all_matches if m["played"]]
    upcoming = [m for m in all_matches if not m["played"]]
    return {
        "last": list(reversed(played[-5:])),
        "next": upcoming[:3],
        "form": played[-5:],
        "played": len(played),
    }


# ----------------------------------------------------------------------
# Players (player stats file)
# ----------------------------------------------------------------------

def leaders(rows: list[dict] | None, club_matches: int) -> list[dict]:
    """Best players of the season (all competitions)."""
    totals = [r for r in (rows or []) if r.get("row_type") == "TOTAL"]
    if not totals:
        return []

    def best(key, label, rows_in=None, fmt=str):
        candidates = [r for r in (rows_in if rows_in is not None else totals) if number(r.get(key)) > 0]
        if not candidates:
            return {"label": label, "player": None, "value": "-", "position": None}
        top = max(candidates, key=lambda r: (number(r.get(key)), number(r.get("appearances"))))
        return {"label": label, "player": top.get("playername"), "value": fmt(top.get(key)),
                "position": top.get("position"), "group": football.position_group(top.get("position"))}

    # Average rating only counts players who played enough (a third of the club's matches, at least 3)
    minimum = max(3, round(club_matches / 3))
    regulars = [r for r in totals if number(r.get("appearances")) >= minimum]

    return [
        best("goals", "Top scorer"),
        best("assists", "Most assists"),
        best("AVG", f"Best rating (min. {minimum} apps)", regulars, lambda v: f"{v:.2f}"),
        best("MOTMs", "Most man of the match"),
        best("appearances", "Most appearances"),
    ]


def squad(rows: list[dict] | None, season: str) -> dict | None:
    totals = [r for r in (rows or []) if r.get("row_type") == "TOTAL"]
    if not totals:
        return None

    def mean(key):
        values = [r.get(key) for r in totals if isinstance(r.get(key), (int, float))]
        return f"{sum(values) / len(values):.1f}" if values else "-"

    try:
        season_end = int(season.split("-")[-1])
    except ValueError:
        season_end = None
    ending = sorted(
        (r for r in totals if season_end and isinstance(r.get("contract_end"), int) and r["contract_end"] <= season_end),
        key=lambda r: (football.position_rank(r.get("position")), str(r.get("playername"))),
    )
    return {
        "size": len(totals),
        "age": mean("age"),
        "overall": mean("overall"),
        "potential": mean("potential"),
        "contracts_ending": [r.get("playername") for r in ending],
        "season_end": season_end,
    }


# ----------------------------------------------------------------------
# Transfers (transfers file)
# ----------------------------------------------------------------------

def transfers(rows: list[dict] | None) -> dict | None:
    if rows is None:
        return None
    arrivals = [r for r in rows if r.get("direction") == "IN"]
    departures = [r for r in rows if r.get("direction") == "OUT"]
    spent = sum(number(r.get("fee")) for r in arrivals if r.get("type") != "loan")
    received = sum(number(r.get("fee")) for r in departures if r.get("type") != "loan")
    return {
        "in": len(arrivals),
        "out": len(departures),
        "loans_in": sum(1 for r in arrivals if r.get("type") == "loan"),
        "loans_out": sum(1 for r in departures if r.get("type") == "loan"),
        "spent": spent,
        "received": received,
        "net_spend": spent - received,
    }


# ----------------------------------------------------------------------
# Everything for the Home page
# ----------------------------------------------------------------------

def season_summary(career: dict, season: str) -> dict:
    folder = career["folder"]
    stats_rows = _rows(folder, season, "player_stats")
    fixture_rows = _rows(folder, season, "fixtures")
    match_info = matches(fixture_rows)
    return {
        "league": league(_rows(folder, season, "standings"), career.get("team_id")),
        "matches": match_info,
        "leaders": leaders(stats_rows, match_info["played"]),
        "squad": squad(stats_rows, season),
        "transfers": transfers(_rows(folder, season, "transfers")),
        "state": store.read_state(store.career_dir(folder) / season),
        "has": {
            "fixtures": fixture_rows is not None,
            "player_stats": stats_rows is not None,
        },
    }
