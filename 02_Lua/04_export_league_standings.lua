-- =========================================================
-- The Club Office
-- 04_export_league_standings.lua
--
-- Exports league standings for the main competition
-- of one specific career team.
--
-- Output: TEAM_<teamid>_LEAGUE_STANDINGS_<season>.csv
-- =========================================================

MEMORY = require 'imports/core/memory'
require 'imports/other/helpers'
require 'imports/services/enums'

-- =========================================================
-- CONFIG
-- =========================================================

local SEASON_LABEL = "2026-2027"
local CAREER_TEAM_ID = 110313
local CSV_SEPARATOR = ";"

-- =========================================================
-- COLUMNS
-- =========================================================

local columns = {
    "season",
    "career_teamid",
    "competition",
    "compobjid",
    "position",
    "teamid",
    "teamname",
    "home_wins",
    "home_draws",
    "home_losses",
    "home_goals_for",
    "home_goals_against",
    "away_wins",
    "away_draws",
    "away_losses",
    "away_goals_for",
    "away_goals_against",
    "played",
    "wins",
    "draws",
    "losses",
    "goals_for",
    "goals_against",
    "goal_difference",
    "points"
}

-- =========================================================
-- HELPERS
-- =========================================================

local function csv_escape(value)
    if value == nil then
        return ""
    end

    value = tostring(value)

    if string.find(value, CSV_SEPARATOR) or string.find(value, "\"") or string.find(value, "\n") or string.find(value, "\r") then
        value = string.gsub(value, "\"", "\"\"")
        return "\"" .. value .. "\""
    end

    return value
end

function GetFCEDataManager()
    local IFCEInterface = GetPlugin(ENUM_djb2IFCEInterface_CLSS)
    return MEMORY:ReadMultilevelPointer(IFCEInterface, {0x18, 0x10, 0x08, 0x00})
end

function GetStandingsByIndex(idx)
    local StandingsData = {}

    local FCEDataManager = GetFCEDataManager()
    local StandingsDataList = MEMORY:ReadPointer(FCEDataManager + 0x88)

    local itemSize = 0x18
    local mBegin = MEMORY:ReadPointer(StandingsDataList + 0x28)

    local mCurrent = mBegin + (itemSize * idx)

    StandingsData["mId"] = MEMORY:ReadShort(mCurrent + 0x00)
    StandingsData["mCompObjId"] = MEMORY:ReadShort(mCurrent + 0x02)
    StandingsData["mTeamId"] = MEMORY:ReadInt(mCurrent + 0x04)
    StandingsData["mTeamIndex"] = MEMORY:ReadChar(mCurrent + 0x08)
    StandingsData["mHomeWins"] = MEMORY:ReadChar(mCurrent + 0x09)
    StandingsData["mHomeDraws"] = MEMORY:ReadChar(mCurrent + 0x0A)
    StandingsData["mHomeLosses"] = MEMORY:ReadChar(mCurrent + 0x0B)
    StandingsData["mHomeGoalsFor"] = MEMORY:ReadChar(mCurrent + 0x0C)
    StandingsData["mHomeGoalsAgainst"] = MEMORY:ReadChar(mCurrent + 0x0D)
    StandingsData["mAwayWins"] = MEMORY:ReadChar(mCurrent + 0x0E)
    StandingsData["mAwayDraws"] = MEMORY:ReadChar(mCurrent + 0x0F)
    StandingsData["mAwayLosses"] = MEMORY:ReadChar(mCurrent + 0x10)
    StandingsData["mAwayGoalsFor"] = MEMORY:ReadChar(mCurrent + 0x11)
    StandingsData["mAwayGoalsAgainst"] = MEMORY:ReadChar(mCurrent + 0x12)
    StandingsData["mPoints"] = MEMORY:ReadShort(mCurrent + 0x14)

    return StandingsData
end

function GetValidFixtures()
    local result = {}

    local FCEDataManager = GetFCEDataManager()
    local FixtureDataList = MEMORY:ReadPointer(FCEDataManager + 0x60)

    local itemSize = 0x18
    local mBegin = MEMORY:ReadPointer(FixtureDataList + 0x28)
    local max_items_count = MEMORY:ReadInt(FixtureDataList + 0x1C) - 1

    local mCurrent = 0

    for i = 0, max_items_count do
        mCurrent = mBegin + (itemSize * i)

        local is_used = MEMORY:ReadBool(mCurrent + 0x14)

        if is_used then
            local FixtureData = {}

            FixtureData["mDate"] = MEMORY:ReadInt(mCurrent + 0x00)
            FixtureData["mTime"] = MEMORY:ReadShort(mCurrent + 0x04)
            FixtureData["mId"] = MEMORY:ReadShort(mCurrent + 0x06)
            FixtureData["mCompObjId"] = MEMORY:ReadShort(mCurrent + 0x08)
            FixtureData["mHomeStandingId"] = MEMORY:ReadShort(mCurrent + 0x0A)
            FixtureData["mAwayStandingId"] = MEMORY:ReadShort(mCurrent + 0x0C)
            FixtureData["mMatchGroupId"] = MEMORY:ReadChar(mCurrent + 0x0E)
            FixtureData["mHomeScore"] = MEMORY:ReadChar(mCurrent + 0x0F)
            FixtureData["mHomePenalties"] = MEMORY:ReadChar(mCurrent + 0x10)
            FixtureData["mAwayScore"] = MEMORY:ReadChar(mCurrent + 0x11)
            FixtureData["mAwayPenalties"] = MEMORY:ReadChar(mCurrent + 0x12)
            FixtureData["mGameCompletion"] = MEMORY:ReadBool(mCurrent + 0x13)

            table.insert(result, FixtureData)
        end
    end

    return result
end

local function calculate_standing_row(standing)
    local home_wins = standing["mHomeWins"] or 0
    local home_draws = standing["mHomeDraws"] or 0
    local home_losses = standing["mHomeLosses"] or 0
    local home_goals_for = standing["mHomeGoalsFor"] or 0
    local home_goals_against = standing["mHomeGoalsAgainst"] or 0

    local away_wins = standing["mAwayWins"] or 0
    local away_draws = standing["mAwayDraws"] or 0
    local away_losses = standing["mAwayLosses"] or 0
    local away_goals_for = standing["mAwayGoalsFor"] or 0
    local away_goals_against = standing["mAwayGoalsAgainst"] or 0

    local wins = home_wins + away_wins
    local draws = home_draws + away_draws
    local losses = home_losses + away_losses
    local played = wins + draws + losses

    local goals_for = home_goals_for + away_goals_for
    local goals_against = home_goals_against + away_goals_against
    local goal_difference = goals_for - goals_against

    return {
        home_wins = home_wins,
        home_draws = home_draws,
        home_losses = home_losses,
        home_goals_for = home_goals_for,
        home_goals_against = home_goals_against,
        away_wins = away_wins,
        away_draws = away_draws,
        away_losses = away_losses,
        away_goals_for = away_goals_for,
        away_goals_against = away_goals_against,
        played = played,
        wins = wins,
        draws = draws,
        losses = losses,
        goals_for = goals_for,
        goals_against = goals_against,
        goal_difference = goal_difference,
        points = standing["mPoints"] or 0
    }
end

local function find_main_compobjid_for_team(fixtures)
    local comp_counts = {}

    for i = 1, #fixtures do
        local fixture = fixtures[i]

        local home_standing = GetStandingsByIndex(fixture["mHomeStandingId"])
        local away_standing = GetStandingsByIndex(fixture["mAwayStandingId"])

        local home_teamid = home_standing["mTeamId"]
        local away_teamid = away_standing["mTeamId"]

        if home_teamid == CAREER_TEAM_ID or away_teamid == CAREER_TEAM_ID then
            local compobjid = fixture["mCompObjId"]

            if comp_counts[compobjid] == nil then
                comp_counts[compobjid] = 0
            end

            comp_counts[compobjid] = comp_counts[compobjid] + 1
        end
    end

    local main_compobjid = nil
    local highest_count = 0

    for compobjid, count in pairs(comp_counts) do
        if count > highest_count then
            highest_count = count
            main_compobjid = compobjid
        end
    end

    return main_compobjid, highest_count
end

local function collect_standings_from_fixtures(fixtures, main_compobjid)
    local standings_by_teamid = {}

    for i = 1, #fixtures do
        local fixture = fixtures[i]

        if fixture["mCompObjId"] == main_compobjid then
            local home_standing = GetStandingsByIndex(fixture["mHomeStandingId"])
            local away_standing = GetStandingsByIndex(fixture["mAwayStandingId"])

            local home_teamid = home_standing["mTeamId"]
            local away_teamid = away_standing["mTeamId"]

            if home_teamid ~= nil and home_teamid > 0 then
                standings_by_teamid[home_teamid] = home_standing
            end

            if away_teamid ~= nil and away_teamid > 0 then
                standings_by_teamid[away_teamid] = away_standing
            end
        end
    end

    local rows = {}

    for teamid, standing in pairs(standings_by_teamid) do
        local calculated = calculate_standing_row(standing)

        table.insert(rows, {
            standing = standing,
            calculated = calculated
        })
    end

    return rows
end

-- =========================================================
-- MAIN
-- =========================================================

assert(IsInCM(), "Script must be executed in career mode")

local fixtures = GetValidFixtures()

local main_compobjid, fixture_count = find_main_compobjid_for_team(fixtures)

if main_compobjid == nil then
    LOGGER:LogError("Could not identify main competition for team " .. tostring(CAREER_TEAM_ID))
    MessageBox("The Club Office", "Could not identify main competition.")
    return
end

local competition_name = GetCompetitionNameByObjID(main_compobjid)

local rows = collect_standings_from_fixtures(fixtures, main_compobjid)

table.sort(rows, function(a, b)
    local ca = a.calculated
    local cb = b.calculated

    if ca.points ~= cb.points then
        return ca.points > cb.points
    end

    if ca.goal_difference ~= cb.goal_difference then
        return ca.goal_difference > cb.goal_difference
    end

    return ca.goals_for > cb.goals_for
end)

local desktop_path = string.format("%s\\Desktop", os.getenv('USERPROFILE'))

local file_path = string.format(
    "%s\\TEAM_%d_LEAGUE_STANDINGS_%s.csv",
    desktop_path,
    CAREER_TEAM_ID,
    SEASON_LABEL
)

local file = io.open(file_path, "w+")

if file == nil then
    LOGGER:LogError("Could not create CSV file.")
    return
end

io.output(file)

io.write(table.concat(columns, CSV_SEPARATOR))
io.write("\n")

for position = 1, #rows do
    local standing = rows[position].standing
    local calculated = rows[position].calculated

    local teamid = standing["mTeamId"]
    local teamname = GetTeamName(teamid)

    local row = {
        SEASON_LABEL,
        CAREER_TEAM_ID,
        competition_name,
        main_compobjid,
        position,
        teamid,
        teamname,
        calculated.home_wins,
        calculated.home_draws,
        calculated.home_losses,
        calculated.home_goals_for,
        calculated.home_goals_against,
        calculated.away_wins,
        calculated.away_draws,
        calculated.away_losses,
        calculated.away_goals_for,
        calculated.away_goals_against,
        calculated.played,
        calculated.wins,
        calculated.draws,
        calculated.losses,
        calculated.goals_for,
        calculated.goals_against,
        calculated.goal_difference,
        calculated.points
    }

    local escaped_row = {}

    for j = 1, #row do
        table.insert(escaped_row, csv_escape(row[j]))
    end

    io.write(table.concat(escaped_row, CSV_SEPARATOR))
    io.write("\n")
end

io.close(file)

LOGGER:LogInfo("Done")
LOGGER:LogInfo("Main competition: " .. tostring(competition_name))
LOGGER:LogInfo("Main compobjid: " .. tostring(main_compobjid))
LOGGER:LogInfo("Career team fixtures in main competition: " .. tostring(fixture_count))
LOGGER:LogInfo("Standing rows exported: " .. tostring(#rows))
LOGGER:LogInfo("CSV exported to: " .. file_path)

MessageBox(
    "The Club Office",
    string.format(
        "Exported standings\nCompetition: %s\nTeams: %d",
        competition_name,
        #rows
    )
)