-- =========================================================
-- The Club Office
-- 01_export_season_player_stats.lua
--
-- Exports season player stats for one specific career team.
--
-- Logic:
-- - One row per player + competition when the player has appearances
-- - One TOTAL row per player with all competitions compiled
-- - Players with 0 appearances are exported with a TOTAL row only
--
-- Output: TEAM_<teamid>_SEASON_PLAYER_STATS_<season>.csv
-- =========================================================

require 'imports/other/helpers'

-- =========================================================
-- CONFIG
-- =========================================================

local SEASON_LABEL = "2026-2027"
local CAREER_TEAM_ID = 110313
local CSV_SEPARATOR = ";"

-- =========================================================
-- NATIONS CONFIG
-- =========================================================

local NATION_ID_FIELD = "nationid"
local NATION_NAME_FIELD = "nationname"

-- =========================================================
-- COLUMNS
-- =========================================================

local columns = {
    "season",
    "career_teamid",
    "teamid",
    "teamname",
    "playerid",
    "playername",
    "position",
    "second_position",
    "third_position",
    "fourth_position",
    "nationalityid",
    "nationality",
    "age",
    "birthdate",
    "overall",
    "potential",
    "growth_gap",
    "contract_end",
    "contract_status",
    "contract_duration_months",
    "squad_role_id",
    "squad_role",
    "is_retiring",
    "height",
    "weight",
    "preferred_foot",
    "skill_moves",
    "weak_foot",
    "playstyles",
    "competition",
    "compobjid",
    "appearances",
    "AVG",
    "MOTMs",
    "goals",
    "assists",
    "goal_contributions",
    "yellow_cards",
    "two_yellow",
    "red_cards",
    "saves",
    "goals_conceded",
    "cleansheets",
    "row_type"
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

local function get_squad_role_name(role_id)
    if role_id == 1 then
        return "Crucial"
    elseif role_id == 2 then
        return "Important"
    elseif role_id == 3 then
        return "Rotation"
    elseif role_id == 4 then
        return "Sporadic"
    elseif role_id == 5 then
        return "Prospect"
    end

    return "Unknown"
end

local function get_position_name(position_id)
    if position_id == nil then
        return ""
    end

    if position_id < 0 then
        return ""
    end

    return GetPlayerPrimaryPositionName(position_id)
end

local function calculate_age_from_birthdate(birthdate, current_date)
    if birthdate == nil or birthdate <= 0 then
        return ""
    end

    local normalized_birthdate = DATE:new()
    normalized_birthdate:FromGregorianDays(birthdate)

    local age = current_date.year - normalized_birthdate.year

    if current_date.month < normalized_birthdate.month then
        age = age - 1
    elseif current_date.month == normalized_birthdate.month and current_date.day < normalized_birthdate.day then
        age = age - 1
    end

    return age
end

local function create_empty_stats()
    return {
        app = 0,
        avg_raw_total = 0,
        avg = "0.00",
        motm = 0,
        goals = 0,
        assists = 0,
        goal_contributions = 0,
        yellow = 0,
        two_yellow = 0,
        red = 0,
        saves = 0,
        goals_conceded = 0,
        clean_sheets = 0
    }
end

local function add_stat_to_compiled(compiled, stat)
    local app = stat.app or 0

    compiled.app = compiled.app + app
    compiled.avg_raw_total = compiled.avg_raw_total + (stat.avg or 0)
    compiled.motm = compiled.motm + (stat.motm or 0)
    compiled.goals = compiled.goals + (stat.goals or 0)
    compiled.assists = compiled.assists + (stat.assists or 0)
    compiled.yellow = compiled.yellow + (stat.yellow or 0)
    compiled.two_yellow = compiled.two_yellow + (stat.two_yellow or 0)
    compiled.red = compiled.red + (stat.red or 0)
    compiled.saves = compiled.saves + (stat.saves or 0)
    compiled.goals_conceded = compiled.goals_conceded + (stat.goals_conceded or 0)
    compiled.clean_sheets = compiled.clean_sheets + (stat.clean_sheets or 0)
    compiled.goal_contributions = compiled.goals + compiled.assists
end

local function finalize_avg(stats)
    if stats.app > 0 then
        stats.avg = string.format("%0.2f", (stats.avg_raw_total / stats.app) / 10)
    else
        stats.avg = "0.00"
    end
end

-- =========================================================
-- GET NATIONS
-- =========================================================

function get_nations()
    local result = {}

    local nations_table = LE.db:GetTable("nations")

    if nations_table == nil then
        LOGGER:LogError("nations table not found. Nationality names will be empty.")
        return result
    end

    local current_record = nations_table:GetFirstRecord()

    while current_record > 0 do
        local nationid = nations_table:GetRecordFieldValue(current_record, NATION_ID_FIELD)
        local nationname = nations_table:GetRecordFieldValue(current_record, NATION_NAME_FIELD)

        if nationid ~= nil then
            result[nationid] = nationname
        end

        current_record = nations_table:GetNextValidRecord()
    end

    return result
end

-- =========================================================
-- GET CONTRACT DATA
-- =========================================================

function get_contracts()
    local result = {}

    local contract_table = LE.db:GetTable("career_playercontract")

    if contract_table == nil then
        LOGGER:LogError("career_playercontract table not found. Contract fields will be empty.")
        return result
    end

    local current_record = contract_table:GetFirstRecord()

    while current_record > 0 do
        local playerid = contract_table:GetRecordFieldValue(current_record, "playerid")

        if playerid ~= nil and playerid > 0 then
            local contract_status = contract_table:GetRecordFieldValue(current_record, "contract_status")
            local duration_months = contract_table:GetRecordFieldValue(current_record, "duration_months")
            local playerrole = contract_table:GetRecordFieldValue(current_record, "playerrole")

            result[playerid] = {
                contract_status = contract_status,
                duration_months = duration_months,
                squad_role_id = playerrole,
                squad_role = get_squad_role_name(playerrole)
            }
        end

        current_record = contract_table:GetNextValidRecord()
    end

    return result
end

-- =========================================================
-- GET TEAM PLAYERS
-- =========================================================

function get_team_players(nations, contracts)
    local result = {}

    local current_date = GetCurrentDate()

    local players_table = LE.db:GetTable("players")

    if players_table == nil then
        LOGGER:LogError("players table not found.")
        return result
    end

    local current_record = players_table:GetFirstRecord()

    while current_record > 0 do
        local playerid = players_table:GetRecordFieldValue(current_record, "playerid")
        local teamid = GetTeamIdFromPlayerId(playerid)

        if teamid == CAREER_TEAM_ID then
            local preferredposition1 = players_table:GetRecordFieldValue(current_record, "preferredposition1")
            local preferredposition2 = players_table:GetRecordFieldValue(current_record, "preferredposition2")
            local preferredposition3 = players_table:GetRecordFieldValue(current_record, "preferredposition3")
            local preferredposition4 = players_table:GetRecordFieldValue(current_record, "preferredposition4")

            local nationalityid = players_table:GetRecordFieldValue(current_record, "nationality")
            local nationality = nations[nationalityid] or ""

            local birthdate = players_table:GetRecordFieldValue(current_record, "birthdate")
            local age = calculate_age_from_birthdate(birthdate, current_date)

            local overall = players_table:GetRecordFieldValue(current_record, "overallrating")
            local potential = players_table:GetRecordFieldValue(current_record, "potential")
            local growth_gap = ""

            if overall ~= nil and potential ~= nil then
                growth_gap = potential - overall
            end

            local contract = contracts[playerid] or {}

            local player = {
                season = SEASON_LABEL,
                career_teamid = CAREER_TEAM_ID,
                teamid = teamid,
                teamname = GetTeamName(teamid),
                playerid = playerid,
                playername = GetPlayerName(playerid),

                position = get_position_name(preferredposition1),
                second_position = get_position_name(preferredposition2),
                third_position = get_position_name(preferredposition3),
                fourth_position = get_position_name(preferredposition4),

                nationalityid = nationalityid,
                nationality = nationality,

                age = age,
                birthdate = birthdate,

                overall = overall,
                potential = potential,
                growth_gap = growth_gap,

                contract_end = players_table:GetRecordFieldValue(current_record, "contractvaliduntil"),
                contract_status = contract.contract_status or "",
                contract_duration_months = contract.duration_months or "",
                squad_role_id = contract.squad_role_id or "",
                squad_role = contract.squad_role or "",

                is_retiring = players_table:GetRecordFieldValue(current_record, "isretiring"),

                height = players_table:GetRecordFieldValue(current_record, "height"),
                weight = players_table:GetRecordFieldValue(current_record, "weight"),
                preferred_foot = players_table:GetRecordFieldValue(current_record, "preferredfoot"),
                skill_moves = players_table:GetRecordFieldValue(current_record, "skillmoves"),
                weak_foot = players_table:GetRecordFieldValue(current_record, "weakfootabilitytypecode"),
                playstyles = players_table:GetRecordFieldValue(current_record, "playstyles"),

                competition_stats = {},
                total_stats = create_empty_stats()
            }

            result[playerid] = player
        end

        current_record = players_table:GetNextValidRecord()
    end

    return result
end

-- =========================================================
-- ADD PLAYER STATS
-- =========================================================

function add_stats_to_players(players)
    local all_stats = GetPlayersStats()

    for i = 1, #all_stats do
        local stat = all_stats[i]
        local playerid = stat.playerid
        local app = stat.app or 0

        if playerid > 0 and playerid < 4294967295 and app > 0 then
            local player = players[playerid]

            if player ~= nil then
                local compobjid = stat.compobjid or 0
                local compname = stat.compname or GetCompetitionNameByObjID(compobjid)

                local comp_stats = create_empty_stats()

                add_stat_to_compiled(comp_stats, stat)
                finalize_avg(comp_stats)

                player.competition_stats[compobjid] = {
                    competition = compname,
                    compobjid = compobjid,
                    stats = comp_stats
                }

                add_stat_to_compiled(player.total_stats, stat)
            end
        end
    end

    for playerid, player in pairs(players) do
        finalize_avg(player.total_stats)
    end

    return players
end

-- =========================================================
-- WRITE ROW
-- =========================================================

local function build_row(player, competition, compobjid, stats, row_type)
    return {
        player.season,
        player.career_teamid,
        player.teamid,
        player.teamname,
        player.playerid,
        player.playername,
        player.position,
        player.second_position,
        player.third_position,
        player.fourth_position,
        player.nationalityid,
        player.nationality,
        player.age,
        player.birthdate,
        player.overall,
        player.potential,
        player.growth_gap,
        player.contract_end,
        player.contract_status,
        player.contract_duration_months,
        player.squad_role_id,
        player.squad_role,
        player.is_retiring,
        player.height,
        player.weight,
        player.preferred_foot,
        player.skill_moves,
        player.weak_foot,
        player.playstyles,
        competition,
        compobjid,
        stats.app,
        stats.avg,
        stats.motm,
        stats.goals,
        stats.assists,
        stats.goal_contributions,
        stats.yellow,
        stats.two_yellow,
        stats.red,
        stats.saves,
        stats.goals_conceded,
        stats.clean_sheets,
        row_type
    }
end

local function write_csv_row(row)
    local escaped_row = {}

    for i = 1, #row do
        table.insert(escaped_row, csv_escape(row[i]))
    end

    io.write(table.concat(escaped_row, CSV_SEPARATOR))
    io.write("\n")
end

-- =========================================================
-- MAIN
-- =========================================================

assert(IsInCM(), "Script must be executed in career mode")

local nations = get_nations()
local contracts = get_contracts()

local players = get_team_players(nations, contracts)
players = add_stats_to_players(players)

local desktop_path = string.format("%s\\Desktop", os.getenv('USERPROFILE'))

local file_path = string.format(
    "%s\\TEAM_%d_SEASON_PLAYER_STATS_%s.csv",
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

local players_count = 0
local rows_count = 0
local competition_rows_count = 0
local total_rows_count = 0

for playerid, player in pairs(players) do
    players_count = players_count + 1

    -- Competition rows
    for compobjid, comp_data in pairs(player.competition_stats) do
        local row = build_row(
            player,
            comp_data.competition,
            comp_data.compobjid,
            comp_data.stats,
            "COMPETITION"
        )

        write_csv_row(row)

        rows_count = rows_count + 1
        competition_rows_count = competition_rows_count + 1
    end

    -- Total row
    local total_row = build_row(
        player,
        "ALL_COMPETITIONS",
        0,
        player.total_stats,
        "TOTAL"
    )

    write_csv_row(total_row)

    rows_count = rows_count + 1
    total_rows_count = total_rows_count + 1
end

io.close(file)

LOGGER:LogInfo("Done")
LOGGER:LogInfo("Players exported: " .. tostring(players_count))
LOGGER:LogInfo("Rows exported: " .. tostring(rows_count))
LOGGER:LogInfo("Competition rows: " .. tostring(competition_rows_count))
LOGGER:LogInfo("Total rows: " .. tostring(total_rows_count))
LOGGER:LogInfo("CSV exported to: " .. file_path)

MessageBox(
    "The Club Office",
    string.format(
        "Exported player stats\nPlayers: %d\nRows: %d\nCompetition rows: %d\nTotal rows: %d",
        players_count,
        rows_count,
        competition_rows_count,
        total_rows_count
    )
)