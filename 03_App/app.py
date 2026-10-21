import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"

CAREERS_FILE = DATA_DIR / "careers.json"
SEASONS_FILE = DATA_DIR / "seasons.json"

PLAYER_STATS_FILE = DATA_DIR / "imported_player_stats.json"
TRANSFERS_FILE = DATA_DIR / "imported_transfers.json"
FIXTURES_FILE = DATA_DIR / "imported_fixtures.json"
STANDINGS_FILE = DATA_DIR / "imported_standings.json"


# =========================================================
# CSV SCHEMAS
# =========================================================

CSV_SCHEMAS = {
    "season_player_stats": {
        "storage_file": PLAYER_STATS_FILE,
        "label": "Season Player Stats",
        "required_columns": [
            "season", "career_teamid", "teamid", "teamname", "playerid", "playername",
            "position", "second_position", "third_position", "fourth_position",
            "nationalityid", "nationality", "age", "birthdate", "overall", "potential",
            "growth_gap", "contract_end", "contract_status", "contract_duration_months",
            "squad_role_id", "squad_role", "is_retiring", "height", "weight",
            "preferred_foot", "skill_moves", "weak_foot", "playstyles", "competition",
            "compobjid", "appearances", "AVG", "MOTMs", "goals", "assists",
            "goal_contributions", "yellow_cards", "two_yellow", "red_cards", "saves",
            "goals_conceded", "cleansheets", "row_type",
        ],
    },
    "season_transfers": {
        "storage_file": TRANSFERS_FILE,
        "label": "Season Transfers",
        "required_columns": [
            "season", "career_teamid", "direction", "type", "date", "playerid",
            "playername", "position", "nationalityid", "nationality", "age", "overall",
            "potential", "growth_gap", "contract_end", "squad_role_id", "squad_role",
            "is_retiring", "teamfromid", "teamfromname", "teamtoid", "teamtoname",
            "fee", "total_deal_value", "exchangeplayerid", "exchangeplayername",
            "deal_note",
        ],
    },
    "team_fixtures": {
        "storage_file": FIXTURES_FILE,
        "label": "Team Fixtures",
        "required_columns": [
            "season", "career_teamid", "competition", "compobjid", "fixtureid", "date",
            "time", "match_group_id", "home_teamid", "home_teamname", "away_teamid",
            "away_teamname", "home_score", "away_score", "home_penalties",
            "away_penalties", "played", "is_home", "result",
        ],
    },
    "league_standings": {
        "storage_file": STANDINGS_FILE,
        "label": "League Standings",
        "required_columns": [
            "season", "career_teamid", "competition", "compobjid", "position", "teamid",
            "teamname", "home_wins", "home_draws", "home_losses", "home_goals_for",
            "home_goals_against", "away_wins", "away_draws", "away_losses",
            "away_goals_for", "away_goals_against", "played", "wins", "draws",
            "losses", "goals_for", "goals_against", "goal_difference", "points",
        ],
    },
}


# =========================================================
# DATA HELPERS
# =========================================================

def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    default_files = [
        CAREERS_FILE,
        SEASONS_FILE,
        PLAYER_STATS_FILE,
        TRANSFERS_FILE,
        FIXTURES_FILE,
        STANDINGS_FILE,
    ]

    for file_path in default_files:
        if not file_path.exists():
            file_path.write_text("[]", encoding="utf-8")


def load_json_list(path: Path) -> list[dict]:
    ensure_data_files()

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        st.error(
            f"Le fichier {path.name} est illisible ou corrompu. "
            f"Restaurez une sauvegarde depuis 03_App/backups/."
        )
        st.stop()


def save_json_list(path: Path, data: list[dict]) -> None:
    ensure_data_files()

    temp_path = path.with_name(path.name + ".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    temp_path.replace(path)


def load_careers() -> list[dict]:
    return load_json_list(CAREERS_FILE)


def save_careers(careers: list[dict]) -> None:
    save_json_list(CAREERS_FILE, careers)


def load_seasons() -> list[dict]:
    return load_json_list(SEASONS_FILE)


def save_seasons(seasons: list[dict]) -> None:
    save_json_list(SEASONS_FILE, seasons)


def load_imported_dataframe(path: Path, career_id: str, season_id: str) -> pd.DataFrame:
    rows = load_json_list(path)

    filtered_rows = [
        row for row in rows
        if row.get("career_id") == career_id
        and row.get("season_id") == season_id
    ]

    return pd.DataFrame(filtered_rows)


def get_career_by_id(career_id: str) -> dict | None:
    for career in load_careers():
        if career["career_id"] == career_id:
            return career
    return None


def get_seasons_for_career(career_id: str) -> list[dict]:
    seasons = load_seasons()
    career_seasons = [
        season for season in seasons
        if season["career_id"] == career_id
    ]

    return sorted(career_seasons, key=lambda item: item["season_label"])


def create_career(
    career_name: str,
    club_name: str,
    teamid: int,
    source_game: str,
    starting_season: str,
    starting_division: str,
    currency: str,
    club_vision: str,
    notes: str,
) -> dict:
    return {
        "career_id": str(uuid.uuid4()),
        "career_name": career_name,
        "club_name": club_name,
        "teamid": teamid,
        "source_game": source_game,
        "starting_season": starting_season,
        "starting_division": starting_division,
        "currency": currency,
        "club_vision": club_vision,
        "notes": notes,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def create_season(
    career_id: str,
    season_label: str,
    division: str,
    board_objective: str,
    personal_objective: str,
    season_notes: str,
) -> dict:
    return {
        "season_id": str(uuid.uuid4()),
        "career_id": career_id,
        "season_label": season_label,
        "division": division,
        "board_objective": board_objective,
        "personal_objective": personal_objective,
        "season_notes": season_notes,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def remove_existing_import_rows(
    existing_rows: list[dict],
    career_id: str,
    season_id: str,
) -> list[dict]:
    return [
        row for row in existing_rows
        if not (
            row.get("career_id") == career_id
            and row.get("season_id") == season_id
        )
    ]


def import_csv_rows(
    df: pd.DataFrame,
    storage_file: Path,
    career: dict,
    season: dict,
    import_type: str,
) -> int:
    existing_rows = load_json_list(storage_file)

    kept_rows = remove_existing_import_rows(
        existing_rows=existing_rows,
        career_id=career["career_id"],
        season_id=season["season_id"],
    )

    imported_at = datetime.now().isoformat(timespec="seconds")
    new_rows = df.to_dict(orient="records")

    for row in new_rows:
        row["career_id"] = career["career_id"]
        row["season_id"] = season["season_id"]
        row["import_type"] = import_type
        row["imported_at"] = imported_at

    save_json_list(storage_file, kept_rows + new_rows)
    return len(new_rows)


# =========================================================
# SESSION HELPERS
# =========================================================

def set_current_career(career_id: str) -> None:
    st.session_state["current_career_id"] = career_id
    st.session_state["active_page"] = "Career Overview"


def get_current_career() -> dict | None:
    career_id = st.session_state.get("current_career_id")

    if not career_id:
        return None

    return get_career_by_id(career_id)


# =========================================================
# CSV VALIDATION
# =========================================================

def validate_csv_columns(df: pd.DataFrame, required_columns: list[str]) -> list[str]:
    return [
        column for column in required_columns
        if column not in df.columns
    ]


def validate_csv_context(df: pd.DataFrame, career: dict, season: dict) -> list[str]:
    errors = []

    if "career_teamid" in df.columns:
        csv_teamids = set(df["career_teamid"].dropna().astype(str).unique())
        expected_teamid = str(career["teamid"])

        if csv_teamids != {expected_teamid}:
            if len(csv_teamids) > 1:
                errors.append(
                    f"career_teamid: the CSV contains several clubs {sorted(csv_teamids)}. "
                    f"It must contain only {expected_teamid}."
                )
            else:
                errors.append(
                    f"career_teamid mismatch. Expected {expected_teamid}, found {sorted(csv_teamids)}"
                )

    if "season" in df.columns:
        csv_seasons = set(df["season"].dropna().astype(str).unique())
        expected_season = str(season["season_label"])

        if csv_seasons != {expected_season}:
            if len(csv_seasons) > 1:
                errors.append(
                    f"season: the CSV contains several seasons {sorted(csv_seasons)}. "
                    f"It must contain only {expected_season}."
                )
            else:
                errors.append(
                    f"season mismatch. Expected {expected_season}, found {sorted(csv_seasons)}"
                )

    return errors


# =========================================================
# CALCULATION HELPERS
# =========================================================

def to_numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(dtype="float64")
    return pd.to_numeric(df[column], errors="coerce").fillna(0)


def get_season_memory_key(career_id: str) -> str:
    # One remembered season per career, so two careers never get mixed up.
    return f"selected_season_{career_id}"


def remember_season(career_id: str, season_label: str) -> None:
    st.session_state[get_season_memory_key(career_id)] = season_label


def select_season(career: dict, seasons: list[dict]) -> dict:
    season_labels = {
        season["season_label"]: season
        for season in seasons
    }
    labels = list(season_labels.keys())

    # Start on the season remembered from the previous page,
    # or on the most recent season if nothing is remembered yet.
    remembered_label = st.session_state.get(get_season_memory_key(career["career_id"]))

    if remembered_label in labels:
        default_index = labels.index(remembered_label)
    else:
        default_index = len(labels) - 1

    selected_label = st.selectbox(
        "Season",
        options=labels,
        index=default_index,
    )

    remember_season(career["career_id"], selected_label)

    return season_labels[selected_label]


def get_selected_season(career: dict) -> dict | None:
    seasons = get_seasons_for_career(career["career_id"])

    if not seasons:
        return None

    return select_season(career, seasons)


def get_top_row(
    df: pd.DataFrame,
    column: str,
    minimum_column: str | None = None,
    minimum_value: int = 0,
) -> pd.Series | None:
    if df.empty or column not in df.columns:
        return None

    working_df = df.copy()
    working_df[column] = pd.to_numeric(working_df[column], errors="coerce").fillna(0)

    if minimum_column and minimum_column in working_df.columns:
        working_df[minimum_column] = pd.to_numeric(
            working_df[minimum_column],
            errors="coerce",
        ).fillna(0)
        working_df = working_df[working_df[minimum_column] >= minimum_value]

    if working_df.empty:
        return None

    return working_df.sort_values(column, ascending=False).iloc[0]


def format_player_stat(row: pd.Series | None, stat_column: str) -> str:
    if row is None:
        return "—"

    return f"{row.get('playername', 'Unknown')} ({row.get(stat_column, '0')})"


def format_money(value: float, currency: str) -> str:
    return f"{currency}{value:,.0f}"


def normalize_bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def prepare_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    working_df = df.copy()
    for column in columns:
        if column in working_df.columns:
            working_df[column] = pd.to_numeric(working_df[column], errors="coerce").fillna(0)
    return working_df


# =========================================================
# PAGES
# =========================================================

def render_home() -> None:
    st.title("The Club Office")
    st.subheader("FC 26 Career Companion")

    careers = load_careers()

    st.divider()

    if not careers:
        st.info("No career yet. Create your first career from the sidebar.")
        return

    st.header("Careers")

    for career in careers:
        career_seasons = get_seasons_for_career(career["career_id"])

        with st.container(border=True):
            col1, col2 = st.columns([4, 1])

            with col1:
                st.subheader(career["career_name"])
                st.write(f"**Club:** {career['club_name']}")
                st.write(f"**Team ID:** {career['teamid']}")
                st.write(f"**Source:** {career['source_game']}")
                st.write(f"**Starting season:** {career['starting_season']}")
                st.write(f"**Starting division:** {career['starting_division']}")
                st.write(f"**Club vision:** {career['club_vision']}")
                st.write(f"**Seasons:** {len(career_seasons)}")

            with col2:
                if st.button("Open", key=f"open_{career['career_id']}"):
                    set_current_career(career["career_id"])
                    st.rerun()


def render_create_career() -> None:
    st.title("Create Career")

    with st.form("create_career_form"):
        career_name = st.text_input("Career name", value="East Ham City Road to Premier League")
        club_name = st.text_input("Club name", value="East Ham City FC")
        teamid = st.number_input("Team ID", min_value=1, step=1, value=110313)
        source_game = st.text_input("Source game", value="FC 26")
        starting_season = st.text_input("Starting season", value="2026-2027")
        starting_division = st.text_input("Starting division", value="Premier League")
        currency = st.text_input("Currency", value="£")
        club_vision = st.text_input("Club vision", value="Lower League Realism")
        notes = st.text_area("Notes", value="")

        submitted = st.form_submit_button("Create career")

    if submitted:
        if not career_name.strip():
            st.error("Career name is required.")
            return

        if not club_name.strip():
            st.error("Club name is required.")
            return

        careers = load_careers()

        new_career = create_career(
            career_name=career_name.strip(),
            club_name=club_name.strip(),
            teamid=int(teamid),
            source_game=source_game.strip(),
            starting_season=starting_season.strip(),
            starting_division=starting_division.strip(),
            currency=currency.strip(),
            club_vision=club_vision.strip(),
            notes=notes.strip(),
        )

        careers.append(new_career)
        save_careers(careers)

        st.session_state["current_career_id"] = new_career["career_id"]

        st.success("Career created.")
        st.info("Go to Career Overview from the sidebar.")


def render_career_overview() -> None:
    career = get_current_career()

    if career is None:
        st.title("Career Overview")
        st.warning("No career selected. Go to Home and open a career.")
        return

    career_seasons = get_seasons_for_career(career["career_id"])

    st.title(career["career_name"])
    st.subheader("Career Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Club", career["club_name"])
        st.metric("Team ID", career["teamid"])

    with col2:
        st.metric("Source", career["source_game"])
        st.metric("Starting season", career["starting_season"])

    with col3:
        st.metric("Starting division", career["starting_division"])
        st.metric("Currency", career["currency"])

    with col4:
        st.metric("Seasons", len(career_seasons))
        st.metric("Club vision", career["club_vision"])

    st.divider()

    st.header("Notes")
    if career["notes"]:
        st.write(career["notes"])
    else:
        st.caption("No notes yet.")

    st.divider()

    st.header("Seasons")

    if not career_seasons:
        st.info("No season yet. Add one from the sidebar.")
        return

    for season in career_seasons:
        with st.container(border=True):
            st.subheader(season["season_label"])
            st.write(f"**Division:** {season['division']}")
            st.write(f"**Board objective:** {season['board_objective']}")
            st.write(f"**Personal objective:** {season['personal_objective']}")

            if season["season_notes"]:
                st.write(f"**Notes:** {season['season_notes']}")


def render_add_season() -> None:
    career = get_current_career()

    if career is None:
        st.title("Add Season")
        st.warning("No career selected. Go to Home and open a career first.")
        return

    st.title("Add Season")
    st.subheader(career["career_name"])

    with st.form("add_season_form"):
        season_label = st.text_input("Season", value=career["starting_season"])
        division = st.text_input("Division", value=career["starting_division"])
        board_objective = st.text_input("Board objective", value="")
        personal_objective = st.text_input("Personal objective", value="")
        season_notes = st.text_area("Season notes", value="")

        submitted = st.form_submit_button("Add season")

    if submitted:
        if not season_label.strip():
            st.error("Season label is required.")
            return

        seasons = load_seasons()

        existing = [
            season for season in seasons
            if season["career_id"] == career["career_id"]
            and season["season_label"] == season_label.strip()
        ]

        if existing:
            st.error("This season already exists for this career.")
            return

        new_season = create_season(
            career_id=career["career_id"],
            season_label=season_label.strip(),
            division=division.strip(),
            board_objective=board_objective.strip(),
            personal_objective=personal_objective.strip(),
            season_notes=season_notes.strip(),
        )

        seasons.append(new_season)
        save_seasons(seasons)
        remember_season(career["career_id"], new_season["season_label"])

        st.success("Season added.")
        st.json(new_season)


def render_import_csv() -> None:
    career = get_current_career()

    if career is None:
        st.title("Import CSV")
        st.warning("No career selected. Go to Home and open a career first.")
        return

    career_seasons = get_seasons_for_career(career["career_id"])

    if not career_seasons:
        st.title("Import CSV")
        st.warning("No season exists for this career. Add a season first.")
        return

    st.title("Import CSV")
    st.subheader(career["career_name"])

    selected_season = select_season(career, career_seasons)

    import_type = st.selectbox(
        "CSV type",
        options=list(CSV_SCHEMAS.keys()),
        format_func=lambda key: CSV_SCHEMAS[key]["label"],
    )

    uploaded_file = st.file_uploader(
        "Upload CSV",
        type=["csv"],
    )

    if uploaded_file is None:
        st.info("Upload one CSV file exported from the Lua scripts.")
        return

    schema = CSV_SCHEMAS[import_type]

    try:
        df = pd.read_csv(uploaded_file, sep=";", dtype=str)
    except Exception as error:
        st.error(f"Could not read CSV: {error}")
        return

    st.write("Preview")
    st.dataframe(df.head(20), width="stretch")

    missing_columns = validate_csv_columns(df, schema["required_columns"])
    context_errors = validate_csv_context(df, career, selected_season)

    if missing_columns:
        st.error("Missing columns:")
        st.write(missing_columns)
        return

    if context_errors:
        st.error("Context validation failed:")
        for error in context_errors:
            st.write(f"- {error}")
        return

    st.success("CSV validation OK.")
    st.write(f"Rows detected: **{len(df)}**")

    if st.button("Import CSV"):
        imported_count = import_csv_rows(
            df=df,
            storage_file=schema["storage_file"],
            career=career,
            season=selected_season,
            import_type=import_type,
        )

        st.success(f"Imported {imported_count} rows into {schema['storage_file'].name}.")



def render_season_dashboard() -> None:
    career = get_current_career()

    if career is None:
        st.title("Season Dashboard")
        st.warning("No career selected. Go to Create or Open Career first.")
        return

    season = get_selected_season(career)

    if season is None:
        st.title("Season Dashboard")
        st.warning("No season exists for this career. Add a season first.")
        return

    player_stats = load_imported_dataframe(
        PLAYER_STATS_FILE,
        career["career_id"],
        season["season_id"],
    )
    transfers = load_imported_dataframe(
        TRANSFERS_FILE,
        career["career_id"],
        season["season_id"],
    )
    fixtures = load_imported_dataframe(
        FIXTURES_FILE,
        career["career_id"],
        season["season_id"],
    )
    standings = load_imported_dataframe(
        STANDINGS_FILE,
        career["career_id"],
        season["season_id"],
    )

    st.title("Season Dashboard")
    st.caption(f"{career['club_name']} — {season['season_label']}")

    if player_stats.empty and transfers.empty and fixtures.empty and standings.empty:
        st.info("No imported data yet for this season.")
        return

    total_player_stats = pd.DataFrame()
    if not player_stats.empty and "row_type" in player_stats.columns:
        total_player_stats = player_stats[player_stats["row_type"] == "TOTAL"].copy()

    played_fixtures = pd.DataFrame()
    if not fixtures.empty and "played" in fixtures.columns:
        played_fixtures = fixtures[normalize_bool_series(fixtures["played"])].copy()

    career_standing = pd.DataFrame()
    if not standings.empty and "teamid" in standings.columns:
        career_standing = standings[
            standings["teamid"].astype(str) == str(career["teamid"])
        ].copy()

    # =====================================================
    # League and form
    # =====================================================

    st.divider()
    st.markdown("### Season status")

    league_position = "—"
    league_points = "—"
    league_record = "—"
    league_gd = "—"

    if not career_standing.empty:
        row = career_standing.iloc[0]
        league_position = str(row.get("position", "—"))
        league_points = str(row.get("points", "—"))
        league_record = f"{row.get('wins', '0')}-{row.get('draws', '0')}-{row.get('losses', '0')}"
        league_gd = str(row.get("goal_difference", "—"))

    matches_played = len(played_fixtures)
    wins = draws = losses = 0

    if not played_fixtures.empty and "result" in played_fixtures.columns:
        wins = int((played_fixtures["result"] == "W").sum())
        draws = int((played_fixtures["result"] == "D").sum())
        losses = int((played_fixtures["result"] == "L").sum())

    win_rate = "—"
    if matches_played > 0:
        win_rate = f"{round((wins / matches_played) * 100, 1)}%"

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("League position", league_position)
    col2.metric("Points", league_points)
    col3.metric("League record", league_record, help="Wins-Draws-Losses")
    col4.metric("Goal difference", league_gd)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Matches played", matches_played)
    col2.metric("Wins", wins)
    col3.metric("Draws", draws)
    col4.metric("Losses", losses)
    col5.metric("Win rate", win_rate)

    # =====================================================
    # Player leaders as table, not cards
    # =====================================================

    st.divider()
    st.markdown("### Player leaders")

    top_scorer = get_top_row(total_player_stats, "goals")
    top_assister = get_top_row(total_player_stats, "assists")
    best_avg = get_top_row(
        total_player_stats,
        "AVG",
        minimum_column="appearances",
        minimum_value=5,
    )
    most_apps = get_top_row(total_player_stats, "appearances")

    def leader_row(label: str, row: pd.Series | None, stat_column: str, suffix: str) -> dict:
        if row is None:
            return {"Category": label, "Player": "—", "Value": "—"}

        value = row.get(stat_column, "0")

        if isinstance(value, float):
            value_text = f"{value:.2f}" if stat_column == "AVG" else f"{value:.0f}"
        else:
            value_text = str(value)

        return {
            "Category": label,
            "Player": str(row.get("playername", "Unknown")),
            "Value": f"{value_text} {suffix}".strip(),
        }

    leaders_df = pd.DataFrame([
        leader_row("Top scorer", top_scorer, "goals", "goals"),
        leader_row("Top assister", top_assister, "assists", "assists"),
        leader_row("Best AVG", best_avg, "AVG", "AVG"),
        leader_row("Most used", most_apps, "appearances", "apps"),
    ])

    st.dataframe(leaders_df, width="stretch", hide_index=True, height=180)

    # =====================================================
    # Squad and transfers summary
    # =====================================================

    st.divider()
    st.markdown("### Squad and transfers")

    squad_size = len(total_player_stats)
    average_age = "—"
    average_overall = "—"
    average_potential = "—"
    contracts_risk = "—"

    if not total_player_stats.empty:
        average_age = round(to_numeric_series(total_player_stats, "age").mean(), 1)
        average_overall = round(to_numeric_series(total_player_stats, "overall").mean(), 1)
        average_potential = round(to_numeric_series(total_player_stats, "potential").mean(), 1)

        season_end_year = int(str(season["season_label"]).split("-")[-1])
        contract_end = to_numeric_series(total_player_stats, "contract_end")
        contracts_risk = int((contract_end <= season_end_year + 1).sum())

    transfers_in = transfers_out = loans_in = loans_out = 0
    money_spent = money_received = net_spend = 0

    if not transfers.empty:
        direction = transfers["direction"].astype(str)
        transfer_type = transfers["type"].astype(str)
        total_deal_value = pd.to_numeric(
            transfers["total_deal_value"],
            errors="coerce",
        ).fillna(0)

        transfers_in = int((direction == "IN").sum())
        transfers_out = int((direction == "OUT").sum())
        loans_in = int(((direction == "IN") & (transfer_type == "loan")).sum())
        loans_out = int(((direction == "OUT") & (transfer_type == "loan")).sum())

        money_spent = float(total_deal_value[direction == "IN"].sum())
        money_received = float(total_deal_value[direction == "OUT"].sum())
        net_spend = money_spent - money_received

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Squad size", squad_size)
    col2.metric("Average age", average_age)
    col3.metric("Average OVR", average_overall)
    col4.metric("Average POT", average_potential)
    col5.metric("Contracts risk", contracts_risk)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Transfers IN", transfers_in)
    col2.metric("Transfers OUT", transfers_out)
    col3.metric("Loans IN / OUT", f"{loans_in} / {loans_out}")
    col4.metric("Spent", format_money(money_spent, career["currency"]))
    col5.metric("Net spend", format_money(net_spend, career["currency"]))

    st.divider()
    st.markdown("### Imported data preview")
    st.caption("Raw imported data for quick validation.")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Fixtures",
        "Standings",
        "Player Stats",
        "Transfers",
    ])

    with tab1:
        if fixtures.empty:
            st.info("No fixtures imported.")
        else:
            st.dataframe(fixtures, width="stretch", hide_index=True)

    with tab2:
        if standings.empty:
            st.info("No standings imported.")
        else:
            st.dataframe(standings, width="stretch", hide_index=True)

    with tab3:
        if player_stats.empty:
            st.info("No player stats imported.")
        else:
            st.dataframe(player_stats, width="stretch", hide_index=True)

    with tab4:
        if transfers.empty:
            st.info("No transfers imported.")
        else:
            st.dataframe(transfers, width="stretch", hide_index=True)

def render_player_stats() -> None:
    career = get_current_career()

    if career is None:
        st.title("Player Stats")
        st.warning("No career selected. Go to Create or Open Career first.")
        return

    season = get_selected_season(career)

    if season is None:
        st.title("Player Stats")
        st.warning("No season exists for this career. Add a season first.")
        return

    st.title("Player Stats")
    st.caption(f"{career['club_name']} — {season['season_label']}")

    player_stats = load_imported_dataframe(
        PLAYER_STATS_FILE,
        career["career_id"],
        season["season_id"],
    )

    if player_stats.empty:
        st.info("No player stats imported for this season.")
        return

    numeric_columns = [
        "age",
        "overall",
        "potential",
        "growth_gap",
        "appearances",
        "AVG",
        "MOTMs",
        "goals",
        "assists",
        "goal_contributions",
        "yellow_cards",
        "two_yellow",
        "red_cards",
        "cleansheets",
        "contract_end",
    ]

    player_stats = prepare_numeric_columns(player_stats, numeric_columns)

    column_labels = {
        "playername": "Player",
        "position": "Pos",
        "second_position": "2nd pos",
        "third_position": "3rd pos",
        "fourth_position": "4th pos",
        "nationality": "Nationality",
        "age": "Age",
        "height": "Height",
        "weight": "Weight",
        "preferred_foot": "Preferred foot",
        "skill_moves": "Skill moves",
        "weak_foot": "Weak foot",
        "overall": "OVR",
        "potential": "POT",
        "growth_gap": "Growth",
        "squad_role": "Squad role",
        "contract_end": "Contract end",
        "contract_status": "Contract status",
        "contract_duration_months": "Contract months",
        "is_retiring": "Retiring",
        "appearances": "Apps",
        "AVG": "AVG",
        "goals": "Goals",
        "assists": "Assists",
        "goal_contributions": "G+A",
        "MOTMs": "MOTM",
        "yellow_cards": "YC",
        "two_yellow": "2YC",
        "red_cards": "RC",
        "cleansheets": "Clean sheets",
        "competition": "Competition",
        "row_type": "Row type",
    }

    def prepare_display_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        display_df = df[columns].copy()

        if "preferred_foot" in display_df.columns:
            display_df["preferred_foot"] = display_df["preferred_foot"].replace({
                1: "Right",
                2: "Left",
                "1": "Right",
                "2": "Left",
            })

        if "is_retiring" in display_df.columns:
            display_df["is_retiring"] = display_df["is_retiring"].replace({
                0: "No",
                1: "Yes",
                "0": "No",
                "1": "Yes",
            })

        display_df = display_df.rename(columns=column_labels)
        return display_df

    sort_options = {
        "Appearances": "appearances",
        "Goals": "goals",
        "Assists": "assists",
        "G+A": "goal_contributions",
        "AVG": "AVG",
        "OVR": "overall",
        "POT": "potential",
        "Growth": "growth_gap",
        "Age": "age",
    }

    st.divider()

    col1, col2 = st.columns([2, 2])

    with col1:
        view_mode = st.radio(
            "View",
            ["Totals", "By competition"],
            horizontal=True,
        )

    if view_mode == "Totals":
        working_df = player_stats[player_stats["row_type"] == "TOTAL"].copy()
    else:
        competition_df = player_stats[player_stats["row_type"] == "COMPETITION"].copy()
        competitions = sorted(
            competition_df["competition"].dropna().astype(str).unique().tolist()
        )

        with col2:
            selected_competition = st.selectbox(
                "Competition",
                options=competitions,
            )

        working_df = competition_df[
            competition_df["competition"].astype(str) == selected_competition
        ].copy()

    if working_df.empty:
        st.info("No data for this view.")
        return

    st.markdown("### Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        positions = ["All"] + sorted(
            working_df["position"].dropna().astype(str).unique().tolist()
        )
        selected_position = st.selectbox("Position", positions)

    with col2:
        roles = ["All"] + sorted(
            working_df["squad_role"].dropna().astype(str).unique().tolist()
        )
        selected_role = st.selectbox("Squad role", roles)

    with col3:
        nationalities = ["All"] + sorted(
            working_df["nationality"].dropna().astype(str).unique().tolist()
        )
        selected_nationality = st.selectbox("Nationality", nationalities)

    with col4:
        selected_sort_label = st.selectbox(
            "Sort by",
            list(sort_options.keys()),
        )
        sort_by = sort_options[selected_sort_label]

    col1, col2 = st.columns([1, 3])

    with col1:
        min_appearances = st.number_input(
            "Minimum appearances",
            min_value=0,
            step=1,
            value=0,
        )

    filtered_df = working_df.copy()

    if selected_position != "All":
        filtered_df = filtered_df[filtered_df["position"] == selected_position]

    if selected_role != "All":
        filtered_df = filtered_df[filtered_df["squad_role"] == selected_role]

    if selected_nationality != "All":
        filtered_df = filtered_df[filtered_df["nationality"] == selected_nationality]

    if "appearances" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["appearances"] >= min_appearances]

    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)

    st.divider()
    st.markdown("### Squad Summary")

    total_players = len(filtered_df)
    players_used = int((filtered_df["appearances"] > 0).sum()) if "appearances" in filtered_df.columns else 0
    average_age = round(filtered_df["age"].mean(), 1) if "age" in filtered_df.columns and not filtered_df.empty else "—"
    average_ovr = round(filtered_df["overall"].mean(), 1) if "overall" in filtered_df.columns and not filtered_df.empty else "—"
    average_pot = round(filtered_df["potential"].mean(), 1) if "potential" in filtered_df.columns and not filtered_df.empty else "—"

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Players", total_players)
    col2.metric("Players used", players_used)
    col3.metric("Average age", average_age)
    col4.metric("Average OVR", average_ovr)
    col5.metric("Average POT", average_pot)

    st.divider()
    st.markdown("### Main Player Table")
    st.caption("Clean view focused on profile, usage and output.")

    main_columns = [
        "playername",
        "position",
        "age",
        "nationality",
        "overall",
        "potential",
        "growth_gap",
        "squad_role",
        "contract_end",
        "appearances",
        "AVG",
        "goals",
        "assists",
        "goal_contributions",
        "MOTMs",
        "yellow_cards",
        "red_cards",
        "cleansheets",
    ]

    available_main_columns = [
        column for column in main_columns
        if column in filtered_df.columns
    ]

    st.dataframe(
        prepare_display_table(filtered_df, available_main_columns),
        width="stretch",
        hide_index=True,
    )

    st.divider()
    st.markdown("### Detailed Views")

    tab1, tab2, tab3 = st.tabs([
        "Profile",
        "Contract",
        "Competition rows",
    ])

    with tab1:
        profile_columns = [
            "playername",
            "position",
            "second_position",
            "third_position",
            "fourth_position",
            "nationality",
            "age",
            "height",
            "weight",
            "preferred_foot",
            "skill_moves",
            "weak_foot",
            "overall",
            "potential",
            "growth_gap",
        ]

        available_profile_columns = [
            column for column in profile_columns
            if column in filtered_df.columns
        ]

        st.dataframe(
            prepare_display_table(filtered_df, available_profile_columns),
            width="stretch",
            hide_index=True,
        )

    with tab2:
        contract_columns = [
            "playername",
            "position",
            "overall",
            "potential",
            "squad_role",
            "contract_end",
            "contract_status",
            "contract_duration_months",
            "is_retiring",
        ]

        available_contract_columns = [
            column for column in contract_columns
            if column in filtered_df.columns
        ]

        st.dataframe(
            prepare_display_table(filtered_df, available_contract_columns),
            width="stretch",
            hide_index=True,
        )

    with tab3:
        if view_mode == "By competition":
            st.info("You are already viewing one competition.")
            st.dataframe(
                prepare_display_table(filtered_df, available_main_columns),
                width="stretch",
                hide_index=True,
            )
        else:
            competition_rows = player_stats[player_stats["row_type"] == "COMPETITION"].copy()

            if competition_rows.empty:
                st.info("No competition rows available.")
            else:
                competition_rows = prepare_numeric_columns(competition_rows, numeric_columns)

                competition_columns = [
                    "playername",
                    "position",
                    "competition",
                    "appearances",
                    "AVG",
                    "goals",
                    "assists",
                    "goal_contributions",
                    "MOTMs",
                    "yellow_cards",
                    "red_cards",
                    "cleansheets",
                ]

                available_competition_columns = [
                    column for column in competition_columns
                    if column in competition_rows.columns
                ]

                st.dataframe(
                    prepare_display_table(competition_rows, available_competition_columns),
                    width="stretch",
                    hide_index=True,
                )

def render_fixtures() -> None:
    career = get_current_career()

    if career is None:
        st.title("Fixtures")
        st.warning("No career selected. Go to Create or Open Career first.")
        return

    season = get_selected_season(career)

    if season is None:
        st.title("Fixtures")
        st.warning("No season exists for this career. Add a season first.")
        return

    st.title("Fixtures")
    st.caption(f"{career['club_name']} — {season['season_label']}")

    fixtures = load_imported_dataframe(
        FIXTURES_FILE,
        career["career_id"],
        season["season_id"],
    )

    if fixtures.empty:
        st.info("No fixtures imported for this season.")
        return

    def clean_result(value: object) -> str:
        raw = str(value).strip().upper()
        mapping = {
            "W": "Win",
            "D": "Draw",
            "L": "Loss",
            "TBD": "TBD",
            "": "TBD",
            "NAN": "TBD",
        }
        return mapping.get(raw, raw.replace("_", " ").title())

    def result_badge(value: object, played: bool) -> str:
        if not played:
            return "⚪ TBD"

        raw = str(value).strip().upper()
        mapping = {
            "W": "🟢 W",
            "D": "🟡 D",
            "L": "🔴 L",
            "TBD": "⚪ TBD",
            "": "⚪ TBD",
            "NAN": "⚪ TBD",
        }
        return mapping.get(raw, f"⚪ {raw}")

    def format_date_value(value: object) -> str:
        raw = str(value).strip()
        if raw.endswith(".0"):
            raw = raw[:-2]
        if len(raw) == 8 and raw.isdigit():
            return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"
        return raw

    def format_time_value(value: object) -> str:
        raw = str(value).strip()
        if raw.endswith(".0"):
            raw = raw[:-2]
        raw = raw.zfill(4)
        if len(raw) == 4 and raw.isdigit():
            return f"{raw[:2]}:{raw[2:]}"
        return raw

    def prepare_fixture_display_table(df: pd.DataFrame) -> pd.DataFrame:
        display_df = df.copy()

        display_df["Date"] = display_df["date"].apply(format_date_value) if "date" in display_df.columns else ""
        display_df["Time"] = display_df["time"].apply(format_time_value) if "time" in display_df.columns else ""
        display_df["Competition"] = display_df["competition"].astype(str) if "competition" in display_df.columns else ""
        display_df["Venue"] = display_df["is_home_bool"].apply(lambda value: "Home" if value else "Away")

        if "home_teamname" in display_df.columns and "away_teamname" in display_df.columns:
            display_df["Match"] = (
                display_df["home_teamname"].astype(str)
                + " vs "
                + display_df["away_teamname"].astype(str)
            )
        else:
            display_df["Match"] = ""

        if "home_score" in display_df.columns and "away_score" in display_df.columns:
            display_df["Score"] = (
                display_df["home_score"].astype(str)
                + " - "
                + display_df["away_score"].astype(str)
            )
            display_df.loc[~display_df["played_bool"], "Score"] = "TBD"
        else:
            display_df["Score"] = "TBD"

        display_df["Result"] = display_df.apply(
            lambda row: result_badge(row.get("result", "TBD"), bool(row.get("played_bool", False))),
            axis=1,
        )
        display_df["Status"] = display_df["played_bool"].apply(lambda value: "Played" if value else "Upcoming")

        return display_df[
            ["Date", "Time", "Competition", "Venue", "Match", "Score", "Result", "Status"]
        ]

    working_df = fixtures.copy()

    if "date" in working_df.columns:
        working_df["date_numeric"] = pd.to_numeric(working_df["date"], errors="coerce").fillna(0)
        working_df = working_df.sort_values("date_numeric", ascending=True)

    if "played" in working_df.columns:
        working_df["played_bool"] = normalize_bool_series(working_df["played"])
    else:
        working_df["played_bool"] = False

    if "is_home" in working_df.columns:
        working_df["is_home_bool"] = normalize_bool_series(working_df["is_home"])
    else:
        working_df["is_home_bool"] = False

    st.divider()
    st.markdown("### Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        competitions = ["All"] + sorted(
            working_df["competition"].dropna().astype(str).unique().tolist()
        )
        selected_competition = st.selectbox("Competition", competitions)

    with col2:
        selected_status = st.selectbox(
            "Status",
            ["All", "Played", "Upcoming"],
        )

    with col3:
        selected_venue = st.selectbox(
            "Venue",
            ["All", "Home", "Away"],
        )

    with col4:
        result_options = ["All", "W", "D", "L", "TBD"]
        selected_result = st.selectbox(
            "Result",
            result_options,
            format_func=lambda value: "All" if value == "All" else clean_result(value),
        )

    filtered_df = working_df.copy()

    if selected_competition != "All":
        filtered_df = filtered_df[
            filtered_df["competition"].astype(str) == selected_competition
        ]

    if selected_status == "Played":
        filtered_df = filtered_df[filtered_df["played_bool"]]
    elif selected_status == "Upcoming":
        filtered_df = filtered_df[~filtered_df["played_bool"]]

    if selected_venue == "Home":
        filtered_df = filtered_df[filtered_df["is_home_bool"]]
    elif selected_venue == "Away":
        filtered_df = filtered_df[~filtered_df["is_home_bool"]]

    if selected_result != "All" and "result" in filtered_df.columns:
        if selected_result == "TBD":
            filtered_df = filtered_df[~filtered_df["played_bool"]]
        else:
            filtered_df = filtered_df[
                filtered_df["result"].astype(str).str.upper() == selected_result
            ]

    st.divider()
    st.markdown("### Summary")

    played_df = filtered_df[filtered_df["played_bool"]].copy()
    upcoming_df = filtered_df[~filtered_df["played_bool"]].copy()

    wins = draws = losses = 0

    if not played_df.empty and "result" in played_df.columns:
        wins = int((played_df["result"].astype(str).str.upper() == "W").sum())
        draws = int((played_df["result"].astype(str).str.upper() == "D").sum())
        losses = int((played_df["result"].astype(str).str.upper() == "L").sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Matches", len(filtered_df))
    col2.metric("Played", len(played_df))
    col3.metric("Upcoming", len(upcoming_df))
    col4.metric("Record W-D-L", f"{wins}-{draws}-{losses}")
    col5.metric("Win rate", f"{round((wins / len(played_df)) * 100, 1)}%" if len(played_df) > 0 else "—")

    st.divider()
    st.markdown("### Fixture List")
    st.caption("Fixtures are displayed as a clean season list. Result badges: 🟢 win, 🟡 draw, 🔴 loss, ⚪ upcoming.")

    display_table = prepare_fixture_display_table(filtered_df)
    table_height = min(1400, max(320, 36 * (len(display_table) + 1) + 20))

    st.dataframe(
        display_table,
        width="stretch",
        hide_index=True,
        height=table_height,
    )

def render_standings() -> None:
    career = get_current_career()

    if career is None:
        st.title("Standings")
        st.warning("No career selected. Go to Create or Open Career first.")
        return

    season = get_selected_season(career)

    if season is None:
        st.title("Standings")
        st.warning("No season exists for this career. Add a season first.")
        return

    st.title("Standings")
    st.caption(f"{career['club_name']} — {season['season_label']}")

    standings = load_imported_dataframe(
        STANDINGS_FILE,
        career["career_id"],
        season["season_id"],
    )

    if standings.empty:
        st.info("No standings imported for this season.")
        return

    working_df = standings.copy()

    numeric_columns = [
        "position",
        "played",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]

    working_df = prepare_numeric_columns(working_df, numeric_columns)

    if "position" in working_df.columns:
        working_df = working_df.sort_values("position", ascending=True)

    career_row = working_df[
        working_df["teamid"].astype(str) == str(career["teamid"])
    ]

    st.divider()
    st.markdown("### Club Position")

    if career_row.empty:
        st.warning("Career team not found in standings.")
    else:
        row = career_row.iloc[0]

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Position", int(row["position"]))
        col2.metric("Points", int(row["points"]))
        col3.metric("Record W-D-L", f"{int(row['wins'])}-{int(row['draws'])}-{int(row['losses'])}")
        col4.metric("Goal difference", int(row["goal_difference"]))
        col5.metric("Played", int(row["played"]))

    st.divider()
    st.markdown("### League Table")

    display_columns = [
        "position",
        "teamname",
        "played",
        "wins",
        "draws",
        "losses",
        "goals_for",
        "goals_against",
        "goal_difference",
        "points",
    ]

    available_columns = [
        column for column in display_columns
        if column in working_df.columns
    ]

    display_df = working_df[available_columns].copy()

    display_df = display_df.rename(columns={
        "position": "Pos",
        "teamname": "Team",
        "played": "Pld",
        "wins": "W",
        "draws": "D",
        "losses": "L",
        "goals_for": "GF",
        "goals_against": "GA",
        "goal_difference": "GD",
        "points": "Pts",
    })

    def highlight_career_team(row):
        if "Team" not in row:
            return [""] * len(row)

        team_name = str(row["Team"])
        career_team_name = str(career["club_name"])

        if team_name == career_team_name:
            return ["background-color: #23344a; color: white"] * len(row)

        return [""] * len(row)

    st.dataframe(
        display_df.style.apply(highlight_career_team, axis=1),
        width="stretch",
        hide_index=True,
        height=760,
    )

    st.divider()
    st.markdown("### League Insights")

    top_team = working_df.sort_values("points", ascending=False).iloc[0] if not working_df.empty else None
    best_attack = working_df.sort_values("goals_for", ascending=False).iloc[0] if "goals_for" in working_df.columns and not working_df.empty else None
    best_defense = working_df.sort_values("goals_against", ascending=True).iloc[0] if "goals_against" in working_df.columns and not working_df.empty else None

    col1, col2, col3 = st.columns(3)

    if top_team is not None:
        col1.metric("Top team", f"{top_team['teamname']} ({int(top_team['points'])} pts)")
    else:
        col1.metric("Top team", "—")

    if best_attack is not None:
        col2.metric("Best attack", f"{best_attack['teamname']} ({int(best_attack['goals_for'])})")
    else:
        col2.metric("Best attack", "—")

    if best_defense is not None:
        col3.metric("Best defense", f"{best_defense['teamname']} ({int(best_defense['goals_against'])})")
    else:
        col3.metric("Best defense", "—")


def render_transfers() -> None:
    career = get_current_career()

    if career is None:
        st.title("Transfers")
        st.warning("No career selected. Go to Create or Open Career first.")
        return

    season = get_selected_season(career)

    if season is None:
        st.title("Transfers")
        st.warning("No season exists for this career. Add a season first.")
        return

    st.title("Transfers")
    st.caption(f"{career['club_name']} — {season['season_label']}")

    transfers = load_imported_dataframe(
        TRANSFERS_FILE,
        career["career_id"],
        season["season_id"],
    )

    if transfers.empty:
        st.info("No transfers imported for this season.")
        return

    def section_title(title: str, subtitle: str = "") -> None:
        st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)

    def clean_transfer_type(value: object) -> str:
        raw = str(value).strip()
        mapping = {
            "loan": "Loan",
            "transfer": "Transfer",
            "free_agent": "Free agent",
            "freeagent": "Free agent",
            "pre_contract": "Pre-contract",
            "release_clause": "Release clause",
            "unknown": "Unknown",
            "": "Unknown",
        }
        return mapping.get(raw.lower(), raw.replace("_", " ").title())

    def clean_direction(value: object) -> str:
        raw = str(value).strip().upper()
        if raw in ["IN", "OUT"]:
            return raw
        return str(value).replace("_", " ").title()

    def format_date_value(value: object) -> str:
        raw = str(value).strip()
        if raw.endswith(".0"):
            raw = raw[:-2]
        if len(raw) == 8 and raw.isdigit():
            return f"{raw[6:8]}/{raw[4:6]}/{raw[0:4]}"
        return raw

    def format_money_value(value: object) -> str:
        amount = pd.to_numeric(pd.Series([value]), errors="coerce").fillna(0).iloc[0]
        return format_money(float(amount), career["currency"])

    def prepare_transfer_display_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        display_df = df[columns].copy()

        column_labels = {
            "date": "Date",
            "direction": "Direction",
            "type": "Type",
            "playername": "Player",
            "position": "Pos",
            "nationality": "Nationality",
            "age": "Age",
            "overall": "OVR",
            "potential": "POT",
            "growth_gap": "Growth",
            "teamfromname": "From",
            "teamtoname": "To",
            "fee": "Fee",
            "total_deal_value": "Deal value",
            "exchangeplayername": "Exchange player",
            "deal_note": "Note",
            "contract_end": "Contract end",
            "squad_role": "Squad role",
            "is_retiring": "Retiring",
        }

        if "date" in display_df.columns:
            display_df["date"] = display_df["date"].apply(format_date_value)

        if "direction" in display_df.columns:
            display_df["direction"] = display_df["direction"].apply(clean_direction)

        if "type" in display_df.columns:
            display_df["type"] = display_df["type"].apply(clean_transfer_type)

        for money_column in ["fee", "total_deal_value"]:
            if money_column in display_df.columns:
                display_df[money_column] = display_df[money_column].apply(format_money_value)

        if "is_retiring" in display_df.columns:
            display_df["is_retiring"] = display_df["is_retiring"].replace({
                0: "No",
                1: "Yes",
                "0": "No",
                "1": "Yes",
            })

        display_df = display_df.rename(columns=column_labels)
        return display_df

    working_df = transfers.copy()

    numeric_columns = [
        "date",
        "age",
        "overall",
        "potential",
        "growth_gap",
        "fee",
        "total_deal_value",
    ]

    working_df = prepare_numeric_columns(working_df, numeric_columns)

    if "date" in working_df.columns:
        working_df = working_df.sort_values("date", ascending=True)

    direction = working_df["direction"].astype(str) if "direction" in working_df.columns else pd.Series(dtype=str)
    transfer_type = working_df["type"].astype(str) if "type" in working_df.columns else pd.Series(dtype=str)
    total_deal_value = (
        pd.to_numeric(working_df["total_deal_value"], errors="coerce").fillna(0)
        if "total_deal_value" in working_df.columns
        else pd.Series(dtype="float64")
    )

    transfers_in = int((direction == "IN").sum())
    transfers_out = int((direction == "OUT").sum())
    loans_in = int(((direction == "IN") & (transfer_type == "loan")).sum())
    loans_out = int(((direction == "OUT") & (transfer_type == "loan")).sum())
    permanent_deals = int((transfer_type != "loan").sum())

    money_spent = float(total_deal_value[direction == "IN"].sum())
    money_received = float(total_deal_value[direction == "OUT"].sum())
    net_spend = money_spent - money_received

    incoming = working_df[working_df["direction"].astype(str) == "IN"].copy() if "direction" in working_df.columns else pd.DataFrame()
    outgoing = working_df[working_df["direction"].astype(str) == "OUT"].copy() if "direction" in working_df.columns else pd.DataFrame()

    # =====================================================
    # Summary
    # =====================================================

    section_title("Transfer Summary", "Season transfer activity and financial balance.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transfers IN", transfers_in)
    col2.metric("Transfers OUT", transfers_out)
    col3.metric("Loans IN / OUT", f"{loans_in} / {loans_out}")
    col4.metric("Total Deals", len(working_df))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Money Spent", format_money(money_spent, career["currency"]))
    col2.metric("Money Received", format_money(money_received, career["currency"]))
    col3.metric("Net Spend", format_money(net_spend, career["currency"]))
    col4.metric("Permanent Deals", permanent_deals)

    st.divider()

    # =====================================================
    # Notable deals
    # =====================================================

    section_title("Notable Deals", "Quick view of the most important transfer movements.")

    biggest_signing = None
    biggest_sale = None
    highest_potential_signing = None

    if not incoming.empty:
        biggest_signing = incoming.sort_values("total_deal_value", ascending=False).iloc[0]
        highest_potential_signing = incoming.sort_values("potential", ascending=False).iloc[0]

    if not outgoing.empty:
        biggest_sale = outgoing.sort_values("total_deal_value", ascending=False).iloc[0]

    def notable_deal_card(title: str, row: pd.Series | None, value_column: str, subtitle: str = "") -> None:
        with st.container(border=True):
            st.caption(title)

            if row is None:
                st.markdown("**—**")
                return

            player_name = str(row.get("playername", "Unknown"))
            position = str(row.get("position", ""))
            overall = str(row.get("overall", ""))
            potential = str(row.get("potential", ""))
            from_team = str(row.get("teamfromname", ""))
            to_team = str(row.get("teamtoname", ""))

            if value_column in ["fee", "total_deal_value"]:
                main_value = format_money_value(row.get(value_column, 0))
            else:
                main_value = str(row.get(value_column, "—"))

            st.markdown(f"**{player_name}**")
            st.caption(f"{position} · OVR {overall} · POT {potential}")

            if from_team or to_team:
                st.caption(f"{from_team} → {to_team}")

            st.markdown(f"**{main_value}**")

            if subtitle:
                st.caption(subtitle)

    col1, col2, col3 = st.columns(3)
    with col1:
        notable_deal_card("Biggest Signing", biggest_signing, "total_deal_value")
    with col2:
        notable_deal_card("Biggest Sale", biggest_sale, "total_deal_value")
    with col3:
        notable_deal_card("Highest Potential Signing", highest_potential_signing, "potential")

    st.divider()

    # =====================================================
    # Filters
    # =====================================================

    section_title("Filters", "Refine the transfer list.")

    sort_options = {
        "Date": "date",
        "Deal value": "total_deal_value",
        "Fee": "fee",
        "OVR": "overall",
        "POT": "potential",
        "Age": "age",
        "Growth": "growth_gap",
    }

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_direction = st.selectbox(
            "Direction",
            ["All", "IN", "OUT"],
        )

    with col2:
        raw_types = sorted(
            working_df["type"].dropna().astype(str).unique().tolist()
        )
        type_options = ["All"] + raw_types
        selected_type_label = st.selectbox(
            "Type",
            type_options,
            format_func=lambda value: "All" if value == "All" else clean_transfer_type(value),
        )

    with col3:
        positions = ["All"] + sorted(
            working_df["position"].dropna().astype(str).unique().tolist()
        )
        selected_position = st.selectbox("Position", positions)

    with col4:
        selected_sort_label = st.selectbox(
            "Sort by",
            list(sort_options.keys()),
        )
        sort_by = sort_options[selected_sort_label]

    filtered_df = working_df.copy()

    if selected_direction != "All":
        filtered_df = filtered_df[
            filtered_df["direction"].astype(str) == selected_direction
        ]

    if selected_type_label != "All":
        filtered_df = filtered_df[
            filtered_df["type"].astype(str) == selected_type_label
        ]

    if selected_position != "All":
        filtered_df = filtered_df[
            filtered_df["position"].astype(str) == selected_position
        ]

    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)

    st.divider()

    # =====================================================
    # Tables
    # =====================================================

    section_title("Transfer Table", "Clean view of incoming and outgoing moves.")

    table_view = st.radio(
        "Table view",
        ["All deals", "Arrivals", "Departures", "Loans"],
        horizontal=True,
    )

    table_df = filtered_df.copy()

    if table_view == "Arrivals":
        table_df = table_df[table_df["direction"].astype(str) == "IN"]
    elif table_view == "Departures":
        table_df = table_df[table_df["direction"].astype(str) == "OUT"]
    elif table_view == "Loans":
        table_df = table_df[table_df["type"].astype(str) == "loan"]

    display_columns = [
        "date",
        "direction",
        "type",
        "playername",
        "position",
        "nationality",
        "age",
        "overall",
        "potential",
        "growth_gap",
        "teamfromname",
        "teamtoname",
        "fee",
        "total_deal_value",
        "exchangeplayername",
        "deal_note",
    ]

    available_columns = [
        column for column in display_columns
        if column in table_df.columns
    ]

    st.dataframe(
        prepare_transfer_display_table(table_df, available_columns),
        width="stretch",
        hide_index=True,
    )

def render_create_or_open_career() -> None:
    st.title("Create or Open Career")
    st.subheader("The Club Office")

    st.write(
        "Open an existing FC 26 career companion, or create a new one."
    )

    careers = load_careers()

    st.divider()

    st.header("Open Existing Career")

    if not careers:
        st.info("No career yet. Create your first career below.")
    else:
        for career in careers:
            career_seasons = get_seasons_for_career(career["career_id"])

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.subheader(career["career_name"])
                    st.write(f"**Club:** {career['club_name']}")
                    st.write(f"**Team ID:** {career['teamid']}")
                    st.write(f"**Source:** {career['source_game']}")
                    st.write(f"**Seasons:** {len(career_seasons)}")

                with col2:
                    if st.button("Open Career", key=f"open_start_{career['career_id']}"):
                        set_current_career(career["career_id"])
                        st.rerun()

    st.divider()

    st.header("Create New Career")

    with st.form("create_career_start_form"):
        career_name = st.text_input("Career name", value="East Ham City Road to Premier League")
        club_name = st.text_input("Club name", value="East Ham City FC")
        teamid = st.number_input("Team ID", min_value=1, step=1, value=110313)
        source_game = st.text_input("Source game", value="FC 26")
        starting_season = st.text_input("Starting season", value="2026-2027")
        starting_division = st.text_input("Starting division", value="Premier League")
        currency = st.text_input("Currency", value="£")
        club_vision = st.text_input("Club vision", value="Lower League Realism")
        notes = st.text_area("Notes", value="")

        submitted = st.form_submit_button("Create and Open Career")

    if submitted:
        if not career_name.strip():
            st.error("Career name is required.")
            return

        if not club_name.strip():
            st.error("Club name is required.")
            return

        careers = load_careers()

        new_career = create_career(
            career_name=career_name.strip(),
            club_name=club_name.strip(),
            teamid=int(teamid),
            source_game=source_game.strip(),
            starting_season=starting_season.strip(),
            starting_division=starting_division.strip(),
            currency=currency.strip(),
            club_vision=club_vision.strip(),
            notes=notes.strip(),
        )

        careers.append(new_career)
        save_careers(careers)

        set_current_career(new_career["career_id"])

        st.success("Career created.")
        st.rerun()
        
def sidebar_nav_button(label: str, page_name: str) -> None:
    is_active = st.session_state.get("active_page") == page_name
    button_type = "primary" if is_active else "secondary"

    if st.sidebar.button(label, width="stretch", type=button_type):
        st.session_state["active_page"] = page_name
        st.rerun()


# =========================================================
# MAIN
# =========================================================

def main() -> None:
    st.set_page_config(
        page_title="The Club Office",
        page_icon="⚽",
        layout="wide",
    )

    ensure_data_files()

    if "active_page" not in st.session_state:
        st.session_state["active_page"] = "Create or Open Career"

    current_career = get_current_career()

    if current_career is None:
        st.session_state["active_page"] = "Create or Open Career"

    st.sidebar.title("The Club Office")

    if current_career is None:
        st.sidebar.caption("No active career")
        sidebar_nav_button("Create or Open Career", "Create or Open Career")

    else:
        st.sidebar.caption("Active Career")
        st.sidebar.markdown(f"**{current_career['club_name']}**")
        st.sidebar.caption(f"Team ID: {current_career['teamid']}")

        st.sidebar.divider()

        st.sidebar.markdown("### Club")
        sidebar_nav_button("Career Overview", "Career Overview")

        st.sidebar.divider()

        st.sidebar.markdown("### Setup")
        sidebar_nav_button("Add Season", "Add Season")
        sidebar_nav_button("Import CSV", "Import CSV")

        st.sidebar.divider()

        st.sidebar.markdown("### Season Analysis")
        sidebar_nav_button("Season Dashboard", "Season Dashboard")
        sidebar_nav_button("Player Stats", "Player Stats")
        sidebar_nav_button("Fixtures", "Fixtures")
        sidebar_nav_button("Standings", "Standings")
        sidebar_nav_button("Transfers", "Transfers")

        st.sidebar.divider()

        st.sidebar.markdown("### Other")

        if not st.session_state.get("confirm_change_career", False):
            if st.sidebar.button("Change Career", width="stretch"):
                st.session_state["confirm_change_career"] = True
                st.rerun()
        else:
            st.sidebar.warning("Are you sure you want to change career?")

            col1, col2 = st.sidebar.columns(2)

            with col1:
                if st.button("Yes", width="stretch"):
                    st.session_state.pop("current_career_id", None)
                    st.session_state["active_page"] = "Create or Open Career"
                    st.session_state["confirm_change_career"] = False
                    st.rerun()

            with col2:
                if st.button("No", width="stretch"):
                    st.session_state["confirm_change_career"] = False
                    st.rerun()

    page = st.session_state["active_page"]

    if page == "Create or Open Career":
        render_create_or_open_career()
    elif page == "Career Overview":
        render_career_overview()
    elif page == "Add Season":
        render_add_season()
    elif page == "Import CSV":
        render_import_csv()
    elif page == "Season Dashboard":
        render_season_dashboard()
    elif page == "Player Stats":
        render_player_stats()
    elif page == "Fixtures":
        render_fixtures()
    elif page == "Standings":
        render_standings()
    elif page == "Transfers":
        render_transfers()


if __name__ == "__main__":
    main()
