"""What the pages show about a season, computed from the app's copy.

Pure calculations (no interface): they read the four files of a season and
return plain dictionaries, so they can be tested and reused by other pages
(Home, Matches, Standings, Transfers).
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


def long_date(value) -> str:
    """20260815 -> 15 Aug 2026 ("" when the date cannot be read)."""
    parsed = game_date(value)
    return f"{parsed.day} {parsed:%b %Y}" if parsed else ""


def season_rows(folder: str, season: str, kind: str) -> list[dict] | None:
    """The rows of one file of a season (None when it was not exported yet)."""
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
# League table (standings file)
# ----------------------------------------------------------------------

def standings(rows: list[dict] | None, side: str | None = None) -> list[dict]:
    """The league table, first team first.

    side None: the whole table, with the numbers and positions of the file.
    side "home" or "away": only those matches, from the file's home_ and away_
    columns. Points: 3 for a win, 1 for a draw. Teams level on points are
    ordered by goal difference, then goals scored (like the export script
    orders the whole table), then by name.
    """
    if not rows:
        return []

    if side is None:
        table = [{
            "teamid": row.get("teamid"),
            "team": row.get("teamname") or "",
            "position": row.get("position"),
            "played": number(row.get("played")),
            "wins": number(row.get("wins")),
            "draws": number(row.get("draws")),
            "losses": number(row.get("losses")),
            "goals_for": number(row.get("goals_for")),
            "goals_against": number(row.get("goals_against")),
            "goal_difference": number(row.get("goal_difference")),
            "points": number(row.get("points")),
        } for row in rows]
        return sorted(table, key=lambda line: line["position"] if isinstance(line["position"], int) else len(table) + 1)

    prefix = side + "_"
    table = []
    for row in rows:
        wins = number(row.get(prefix + "wins"))
        draws = number(row.get(prefix + "draws"))
        losses = number(row.get(prefix + "losses"))
        goals_for = number(row.get(prefix + "goals_for"))
        goals_against = number(row.get(prefix + "goals_against"))
        table.append({
            "teamid": row.get("teamid"),
            "team": row.get("teamname") or "",
            "played": wins + draws + losses,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "goal_difference": goals_for - goals_against,
            "points": 3 * wins + draws,
        })
    table.sort(key=lambda line: (-line["points"], -line["goal_difference"], -line["goals_for"], line["team"].lower()))
    for position, line in enumerate(table, start=1):
        line["position"] = position
    return table


def table_position(table: list[dict], team_id) -> dict | None:
    """Where the club is in a table, and its points gap ("gap") with the leader
    and the teams just above and just below.

    gap = club's points - other team's points (negative: behind).
    No leader when the club leads, no "above" when the team above is the leader
    (it is already the leader), no "below" when the club is last."""
    index = next((i for i, line in enumerate(table) if line["teamid"] == team_id), None)
    if index is None:
        return None
    club = table[index]

    def with_gap(line: dict) -> dict:
        return dict(line, gap=club["points"] - line["points"])

    return {
        "club": club,
        "teams": len(table),
        "leader": with_gap(table[0]) if index >= 1 else None,
        "above": with_gap(table[index - 1]) if index >= 2 else None,
        "below": with_gap(table[index + 1]) if index + 1 < len(table) else None,
    }


# ----------------------------------------------------------------------
# Matches (fixtures file)
# ----------------------------------------------------------------------

def _match(row: dict) -> dict:
    is_home = row.get("is_home") == "true"
    played = row.get("played") == "true"
    opponent = row.get("away_teamname") if is_home else row.get("home_teamname")
    score = ""
    penalties = ""
    goals_for = goals_against = None
    if played:
        score = f"{row.get('home_score')}-{row.get('away_score')}"
        if row.get("home_penalties") not in (None, "") or row.get("away_penalties") not in (None, ""):
            penalties = f"{row.get('home_penalties') or 0}-{row.get('away_penalties') or 0} pens"
            score += f" ({penalties})"
        home_goals, away_goals = row.get("home_score"), row.get("away_score")
        if isinstance(home_goals, int) and isinstance(away_goals, int):
            goals_for, goals_against = (home_goals, away_goals) if is_home else (away_goals, home_goals)
    return {
        "date": row.get("date"),
        "date_text": short_date(row.get("date")),
        "competition": row.get("competition") or "",
        "opponent": opponent or "",
        "venue": "H" if is_home else "A",
        "played": played,
        "result": row.get("result") if played else "",
        "score": score,
        "penalties": penalties,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "order": (number(row.get("date")), number(row.get("time")), number(row.get("fixtureid"))),
    }


def match_list(rows: list[dict] | None) -> list[dict]:
    """Every match of the club, in date order."""
    return sorted((_match(r) for r in rows or []), key=lambda m: m["order"])


def record(match_items: list[dict]) -> dict:
    """Played, won, drawn, lost, goals of a list of matches."""
    played = [m for m in match_items if m["played"]]
    return {
        "played": len(played),
        "wins": sum(1 for m in played if m["result"] == "W"),
        "draws": sum(1 for m in played if m["result"] == "D"),
        "losses": sum(1 for m in played if m["result"] == "L"),
        "goals_for": sum(m["goals_for"] or 0 for m in played),
        "goals_against": sum(m["goals_against"] or 0 for m in played),
        "to_play": len(match_items) - len(played),
    }


def biggest(match_items: list[dict], result: str) -> dict | None:
    """Biggest win ("W") or heaviest defeat ("L"): largest goal margin, then most goals."""
    candidates = [m for m in match_items if m["played"] and m["result"] == result and m["goals_for"] is not None]
    if not candidates:
        return None
    return max(candidates, key=lambda m: (abs(m["goals_for"] - m["goals_against"]),
                                          m["goals_for"] if result == "W" else m["goals_against"]))


def matches(rows: list[dict] | None) -> dict:
    """Last results (newest first), next matches (soonest first), form (oldest to newest)."""
    if not rows:
        return {"last": [], "next": [], "form": [], "played": 0}
    all_matches = match_list(rows)
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


def transfer_window(value) -> str | None:
    """Summer (July to December) or Winter (January to June), from the date of
    the transfer. None when the date cannot be read."""
    parsed = game_date(value)
    if parsed is None:
        return None
    return "Summer" if parsed.month >= 7 else "Winter"


def transfer_list(rows: list[dict] | None) -> list[dict]:
    """Every transfer of the club, in date order (unknown dates last)."""
    items = []
    for row in rows or []:
        arrival = row.get("direction") == "IN"
        items.append({
            "playerid": row.get("playerid"),
            "player": row.get("playername") or "",
            "position": row.get("position") or "",
            "group": football.position_group(row.get("position")),
            "age": row.get("age"),
            "overall": row.get("overall"),
            "potential": row.get("potential"),
            "direction": row.get("direction"),
            "loan": row.get("type") == "loan",
            # The other club: where he came from, or where he went
            "club": (row.get("teamfromname") if arrival else row.get("teamtoname")) or "",
            "fee": number(row.get("fee")),
            "deal_value": number(row.get("total_deal_value")),
            "exchange": row.get("exchangeplayername") or "",
            "date": row.get("date"),
            "date_text": long_date(row.get("date")),
            "window": transfer_window(row.get("date")),
        })

    def order(item):
        parsed = game_date(item["date"])
        return (parsed is None, parsed or date.min, item["player"].lower())

    return sorted(items, key=order)


def biggest_transfer(items: list[dict], direction: str) -> dict | None:
    """Biggest signing ("IN") or sale ("OUT") by fee, then by total deal value.
    Loans and deals without a fee are left out."""
    candidates = [t for t in items if t["direction"] == direction and not t["loan"] and t["fee"] > 0]
    if not candidates:
        return None
    return max(candidates, key=lambda t: (t["fee"], t["deal_value"]))


# ----------------------------------------------------------------------
# Everything for the Home page
# ----------------------------------------------------------------------

def season_summary(career: dict, season: str) -> dict:
    folder = career["folder"]
    stats_rows = season_rows(folder, season, "player_stats")
    fixture_rows = season_rows(folder, season, "fixtures")
    match_info = matches(fixture_rows)
    return {
        "league": league(season_rows(folder, season, "standings"), career.get("team_id")),
        "matches": match_info,
        "leaders": leaders(stats_rows, match_info["played"]),
        "squad": squad(stats_rows, season),
        "transfers": transfers(season_rows(folder, season, "transfers")),
        "state": store.read_state(store.career_dir(folder) / season),
        "has": {
            "fixtures": fixture_rows is not None,
            "player_stats": stats_rows is not None,
        },
    }
