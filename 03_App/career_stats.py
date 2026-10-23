"""What the History page shows: the career season by season and the all-time records.

Pure calculations (no interface), from the app's copy of every season of a
career. A player is followed from one season to the next by his playerid.
"""
import season_stats
import store

# Best average rating: only the players with at least this many matches
MIN_RATING_APPS = 50

# Player records: (key, title)
PLAYER_RECORDS = [
    ("goals", "Top scorers"),
    ("assists", "Most assists"),
    ("appearances", "Most appearances"),
    ("MOTMs", "Most man of the match"),
    ("rating", f"Best average rating (min. {MIN_RATING_APPS} matches)"),
    ("cleansheets", "Most clean sheets (goalkeepers)"),
]

number = season_stats.number


def load_career(folder: str) -> list[dict]:
    """The four files of every season of the career, oldest season first."""
    return [{
        "season": season,
        "standings": season_stats.season_rows(folder, season, "standings"),
        "fixtures": season_stats.season_rows(folder, season, "fixtures"),
        "player_stats": season_stats.season_rows(folder, season, "player_stats"),
        "transfers": season_stats.season_rows(folder, season, "transfers"),
    } for season in store.list_seasons(folder)]


# ----------------------------------------------------------------------
# Season by season
# ----------------------------------------------------------------------

def best_of_season(totals: list[dict], key: str) -> dict | None:
    """Top scorer ("goals") or top assists ("assists") of a season, players who left included."""
    candidates = [r for r in totals if number(r.get(key)) > 0]
    if not candidates:
        return None
    top = max(candidates, key=lambda r: (number(r.get(key)), number(r.get("appearances"))))
    return {"player": top.get("playername") or "", "value": number(top.get(key))}


def season_lines(seasons: list[dict], team_id) -> list[dict]:
    """One line per season, oldest first. The last season is "in progress"
    while it still has matches to play."""
    lines = []
    for index, data in enumerate(seasons):
        totals = [r for r in data["player_stats"] or [] if r.get("row_type") == "TOTAL"]
        record = season_stats.record(season_stats.match_list(data["fixtures"])) if data["fixtures"] is not None else None
        transfers = season_stats.transfers(data["transfers"])
        latest = index == len(seasons) - 1
        lines.append({
            "season": data["season"],
            "league": season_stats.league(data["standings"], team_id),
            "record": record,
            "top_scorer": best_of_season(totals, "goals"),
            "top_assists": best_of_season(totals, "assists"),
            "net_spend": transfers["net_spend"] if transfers else None,
            "in_progress": latest and (record is None or record["to_play"] > 0),
        })
    return lines


def best_season(lines: list[dict]) -> dict | None:
    """The season with the most league points (then the better position, then goal difference)."""
    candidates = [line for line in lines if line["league"]]
    if not candidates:
        return None

    def strength(line):
        position = line["league"]["position"]
        return (line["league"]["points"], -(position if isinstance(position, int) else 999),
                line["league"]["goal_difference"])

    return max(candidates, key=strength)


# ----------------------------------------------------------------------
# All-time records
# ----------------------------------------------------------------------

def competitions(seasons: list[dict]) -> list[str]:
    """Every competition played by the club, the one with the most matches first."""
    counts = {}
    for data in seasons:
        for row in data["fixtures"] or []:
            if row.get("competition"):
                counts[row["competition"]] = counts.get(row["competition"], 0) + 1
        for row in data["player_stats"] or []:
            if row.get("row_type") == "COMPETITION" and row.get("competition"):
                counts.setdefault(row["competition"], 0)
    return sorted(counts, key=lambda name: (-counts[name], name.lower()))


def player_careers(seasons: list[dict], competition: str | None = None) -> list[dict]:
    """Every player's numbers with the club, all seasons added up.

    competition None: all competitions (TOTAL rows); otherwise only that
    competition. The name and position are the most recent ones. The
    average rating is weighted by the matches of each season."""
    players = {}
    for data in seasons:  # oldest first: the most recent name and position win
        for row in data["player_stats"] or []:
            if competition is None:
                if row.get("row_type") != "TOTAL":
                    continue
            elif row.get("row_type") != "COMPETITION" or row.get("competition") != competition:
                continue
            playerid = row.get("playerid")
            if playerid is None:
                continue
            player = players.setdefault(playerid, {
                "playerid": playerid, "appearances": 0, "goals": 0, "assists": 0, "MOTMs": 0,
                "cleansheets": 0, "rating_points": 0.0, "seasons": set(),
            })
            appearances = number(row.get("appearances"))
            player["name"] = row.get("playername") or ""
            player["position"] = row.get("position") or ""
            player["appearances"] += appearances
            for key in ("goals", "assists", "MOTMs", "cleansheets"):
                player[key] += number(row.get(key))
            player["rating_points"] += number(row.get("AVG")) * appearances
            if appearances > 0:
                player["seasons"].add(data["season"])

    for player in players.values():
        player["rating"] = player["rating_points"] / player["appearances"] if player["appearances"] else 0
        player["season_count"] = len(player["seasons"])
    return list(players.values())


def top_players(players: list[dict], key: str, count: int = 5) -> list[dict]:
    """The best players for one record (most matches first when level, then by name)."""
    if key == "rating":
        candidates = [p for p in players if p["appearances"] >= MIN_RATING_APPS and p["rating"] > 0]
    elif key == "cleansheets":
        candidates = [p for p in players if p["position"] == "GK" and p["cleansheets"] > 0]
    else:
        candidates = [p for p in players if p[key] > 0]
    return sorted(candidates, key=lambda p: (-p[key], -p["appearances"], p["name"].lower()))[:count]


def biggest_win(seasons: list[dict], competition: str | None = None) -> dict | None:
    """Biggest win of the career (largest goal margin, then most goals scored)."""
    matches = []
    for data in seasons:
        for match in season_stats.match_list(data["fixtures"]):
            if competition is None or match["competition"] == competition:
                matches.append(dict(match, season=data["season"]))
    return season_stats.biggest(matches, "W")


def biggest_deal(seasons: list[dict], direction: str) -> dict | None:
    """Biggest signing ("IN") or sale ("OUT") of the career, by fee."""
    deals = []
    for data in seasons:
        for transfer in season_stats.transfer_list(data["transfers"]):
            deals.append(dict(transfer, season=data["season"]))
    return season_stats.biggest_transfer(deals, direction)
