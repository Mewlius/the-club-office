-- =========================================================
-- The Club Office
-- 03_export_team_fixtures.lua
--
-- Exports fixtures/results for one specific career team.
-- Output: TEAM_<teamid>_FIXTURES_<season>.csv
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
    "fixtureid",
    "date",
    "time",
    "match_group_id",
    "home_teamid",
    "home_teamname",
    "away_teamid",
    "away_teamname",
    "home_score",
    "away_score",
    "home_penalties",
    "away_penalties",
    "played",
    "is_home",
    "result"
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

local function bool_to_text(value)
    if value then
        return "true"
    end

    return "false"
end

local function get_match_result(is_played, is_home, home_score, away_score)
    if not is_played then
        return "TBD"
    end

    if is_home then
        if home_score > away_score then
            return "W"
        elseif home_score == away_score then
            return "D"
        else
            return "L"
        end
    else
        if away_score > home_score then
            return "W"
        elseif away_score == home_score then
            return "D"
        else
            return "L"
        end
    end
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

-- =========================================================
-- MAIN
-- =========================================================

assert(IsInCM(), "Script must be executed in career mode")

local desktop_path = string.format("%s\\Desktop", os.getenv('USERPROFILE'))

local file_path = string.format(
    "%s\\TEAM_%d_FIXTURES_%s.csv",
    desktop_path,
    CAREER_TEAM_ID,
    SEASON_LABEL
)

local fixtures = GetValidFixtures()

local file = io.open(file_path, "w+")

if file == nil then
    LOGGER:LogError("Could not create CSV file.")
    return
end

io.output(file)

io.write(table.concat(columns, CSV_SEPARATOR))
io.write("\n")

local exported_count = 0
local played_count = 0
local upcoming_count = 0

for i = 1, #fixtures do
    local FixtureData = fixtures[i]

    local compobjid = FixtureData["mCompObjId"]
    local compname = GetCompetitionNameByObjID(compobjid)

    local HomeStandingsData = GetStandingsByIndex(FixtureData["mHomeStandingId"])
    local AwayStandingsData = GetStandingsByIndex(FixtureData["mAwayStandingId"])

    local home_teamid = HomeStandingsData["mTeamId"]
    local away_teamid = AwayStandingsData["mTeamId"]

    local is_career_team_match = home_teamid == CAREER_TEAM_ID or away_teamid == CAREER_TEAM_ID

    if is_career_team_match then
        local home_teamname = GetTeamName(home_teamid)
        local away_teamname = GetTeamName(away_teamid)

        local played = FixtureData["mGameCompletion"]
        local is_home = home_teamid == CAREER_TEAM_ID

        local home_score = "TBD"
        local away_score = "TBD"
        local home_penalties = ""
        local away_penalties = ""

        if played then
            home_score = FixtureData["mHomeScore"]
            away_score = FixtureData["mAwayScore"]

            local raw_home_penalties = FixtureData["mHomePenalties"]
            local raw_away_penalties = FixtureData["mAwayPenalties"]

            if raw_home_penalties ~= nil and raw_home_penalties > 0 then
                home_penalties = raw_home_penalties
            end

            if raw_away_penalties ~= nil and raw_away_penalties > 0 then
                away_penalties = raw_away_penalties
            end

            played_count = played_count + 1
        else
            upcoming_count = upcoming_count + 1
        end

        local result = get_match_result(
            played,
            is_home,
            FixtureData["mHomeScore"],
            FixtureData["mAwayScore"]
        )

        local row = {
            SEASON_LABEL,
            CAREER_TEAM_ID,
            compname,
            compobjid,
            FixtureData["mId"],
            FixtureData["mDate"],
            FixtureData["mTime"],
            FixtureData["mMatchGroupId"],
            home_teamid,
            home_teamname,
            away_teamid,
            away_teamname,
            home_score,
            away_score,
            home_penalties,
            away_penalties,
            bool_to_text(played),
            bool_to_text(is_home),
            result
        }

        local escaped_row = {}

        for j = 1, #row do
            table.insert(escaped_row, csv_escape(row[j]))
        end

        io.write(table.concat(escaped_row, CSV_SEPARATOR))
        io.write("\n")

        exported_count = exported_count + 1
    end
end

io.close(file)

LOGGER:LogInfo("Done")
LOGGER:LogInfo("Exported fixtures: " .. tostring(exported_count))
LOGGER:LogInfo("Played fixtures: " .. tostring(played_count))
LOGGER:LogInfo("Upcoming fixtures: " .. tostring(upcoming_count))
LOGGER:LogInfo("CSV exported to: " .. file_path)

MessageBox(
    "The Club Office",
    string.format(
        "Exported %d fixtures\nPlayed: %d\nUpcoming: %d",
        exported_count,
        played_count,
        upcoming_count
    )
)