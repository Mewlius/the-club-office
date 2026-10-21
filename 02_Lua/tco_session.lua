-- =========================================================
-- The Club Office
-- tco_session.lua
--
-- Automatic export for The Club Office.
--
-- HOW TO USE
--   Once per play session, after loading your career:
--   F9 -> Lua Engine -> open this file -> Execute
--
-- WHAT IT DOES
--   * Finds the club you manage and the current season by itself:
--     nothing to edit between two seasons.
--   * Exports the four CSV files of the app right away, then again
--     before and after every match of your team, and once a week.
--   * Writes them to:
--       Documents\TheClubOffice\exports\<club> - <save id>\<season>\
--     One folder per career (save) and per season: a career or a
--     season never writes into the folder of another one.
--   * Keeps the previous versions of each file in
--       <season>\previous\
--   * Safety check: refuses to overwrite a season with data that
--     looks reset by the game (see check_season_progress below).
--   * Writes a log you can open with Notepad:
--       Documents\TheClubOffice\exports\tco_session_log.txt
--
--   Running it again in the same session does NOT add a second
--   listener: it simply exports again, right away.
--
--   Read only: this script never changes anything in the game.
--
-- The CSV columns and calculations are exactly the ones of the
-- manual scripts 01_ to 04_ (same folder), so the app imports
-- these files as before.
--
-- Only uses functions of the FC 26 Live Editor itself
-- (lua\libs\v2\imports\...).
-- =========================================================

-- =========================================================
-- SETTINGS
-- =========================================================

local SETTINGS = {
    -- Season label used in the CSV files and the folder name ("2026-2027").
    -- nil = computed from the in-game date (see SEASON_START_MONTH).
    -- To force it, write for example:  SEASON_LABEL_OVERRIDE = "2026-2027",
    SEASON_LABEL_OVERRIDE = nil,

    -- First month of a new season in the in-game calendar (7 = July).
    -- With 7: 14 March 2027 is in season 2026-2027,
    --         2 August 2027 is in season 2027-2028.
    SEASON_START_MONTH = 7,

    -- Export folder. nil = Documents\TheClubOffice\exports
    EXPORT_ROOT_OVERRIDE = nil,

    -- How many previous versions of each file are kept in <season>\previous\
    BACKUP_COUNT = 3,

    CSV_SEPARATOR = ";",

    -- DIAGNOSTIC: true = write EVERY game event to the log (number, name,
    -- in-game date). false = only the exports and a few useful events.
    LOG_ALL_EVENTS = false,
}

local SCRIPT_VERSION = "1.3"

-- =========================================================
-- LIVE EDITOR MODULES
-- =========================================================

local MEMORY = require 'imports/core/memory'
require 'imports/services/enums'
require 'imports/career_mode/enums'
require 'imports/career_mode/helpers'
require 'imports/other/helpers'

-- Career mode event NUMBERS, as seen in the game (FC 26) with the full
-- event log. The Live Editor has two lists of event names (enums.lua and
-- consts.lua) that disagree with each other and with the game in places,
-- so the script only relies on numbers observed in the game:
--   37  career menus, just before each match of the club
--   15  a day passes (the game passes a day by itself right after a match)
--   16  a week passes
--    7  end of the club's match: listed by the Live Editor but never seen
--       with a simulated match; still handled in case a played match sends it
local EVENTS = {
    BEFORE_MATCH = 37,
    DAY_PASSED = 15,
    WEEK_PASSED = 16,
    USER_MATCH_COMPLETED = 7,
}

-- Names of every event in the Live Editor's two lists, for the full log.
local ENUM_EVENT_NAMES = {}

for key, value in pairs(_G) do
    if type(key) == "string" and type(value) == "number" then
        local name = string.match(key, "^ENUM_CM_EVENT_MSG_(.+)$")

        if name then
            ENUM_EVENT_NAMES[value] = name
        end
    end
end

local function describe_event(event_id)
    local enum_name = ENUM_EVENT_NAMES[event_id]
    local const_name = nil

    if type(CONST_CM_EVENTS_NAMES) == "table" then
        const_name = CONST_CM_EVENTS_NAMES[event_id]
    end

    if enum_name == nil and const_name == nil then
        return "(no name)"
    end

    if const_name == nil or enum_name == const_name then
        return tostring(enum_name)
    end

    if enum_name == nil then
        return const_name
    end

    return enum_name .. " / or " .. const_name
end

-- Light log (LOG_ALL_EVENTS = false): only these events are written, to
-- follow the matches (37 before match, 45 simulation, 28 save, 26 back to
-- the menus), the end of a season (12, 13, 18, 19, 23, 24), save loading
-- (29), the transfer windows (97, 98, 101, 102) and the end-of-match events
-- that were never seen yet (7, 38, 39).
local LOGGED_EVENT_IDS = {}

for _, event_id in ipairs({ 7, 12, 13, 18, 19, 23, 24, 26, 28, 29, 37, 38, 39, 45, 97, 98, 101, 102 }) do
    LOGGED_EVENT_IDS[event_id] = true
end

-- =========================================================
-- SESSION STATE
-- =========================================================

local session = {
    version = SCRIPT_VERSION,
    export_root = nil,
    busy = false,
    export_pending = false,
    after_match_pending = false,
    last_export_game_date = nil,
    last_event_id = nil,
    last_event_repeats = 0,
}

-- =========================================================
-- FILES AND FOLDERS
-- =========================================================

local SEP = package.config:sub(1, 1) -- "\" on Windows

local LOG_FILE_NAME = "tco_session_log.txt"
local LOG_MAX_BYTES = 1024 * 1024

local function join_path(...)
    return table.concat({ ... }, SEP)
end

local function file_exists(path)
    local file = io.open(path, "rb")

    if file == nil then
        return false
    end

    file:close()
    return true
end

local function is_writable_dir(dir)
    local probe = join_path(dir, ".tco_write_test")
    local file = io.open(probe, "w")

    if file == nil then
        return false
    end

    file:close()
    os.remove(probe)
    return true
end

-- Creates the folder (and its parent folders) when it does not exist yet.
local function ensure_dir(dir)
    if is_writable_dir(dir) then
        return true
    end

    if type(os.execute) == "function" then
        if SEP == "\\" then
            os.execute('mkdir "' .. dir .. '" 2>nul')
        else
            os.execute('mkdir -p "' .. dir .. '"')
        end
    end

    return is_writable_dir(dir)
end

-- Documents\TheClubOffice\exports
-- (with a fallback for PCs where OneDrive holds the Documents folder)
local function find_export_root()
    if SETTINGS.EXPORT_ROOT_OVERRIDE ~= nil then
        return SETTINGS.EXPORT_ROOT_OVERRIDE
    end

    local profile = os.getenv("USERPROFILE") or os.getenv("HOME")
    local onedrive = os.getenv("OneDrive")
    local candidates = {}

    if profile then
        table.insert(candidates, join_path(profile, "Documents"))
    end

    if onedrive then
        table.insert(candidates, join_path(onedrive, "Documents"))
    end

    for _, documents in ipairs(candidates) do
        if is_writable_dir(documents) then
            return join_path(documents, "TheClubOffice", "exports")
        end
    end

    if profile then
        return join_path(profile, "Documents", "TheClubOffice", "exports")
    end

    return nil
end

local function log(message)
    if LOGGER and LOGGER.LogInfo then
        pcall(LOGGER.LogInfo, LOGGER, "[The Club Office] " .. message)
    end

    if session.export_root == nil then
        return
    end

    local path = join_path(session.export_root, LOG_FILE_NAME)

    -- Keep the log small: past 1 MB it starts again (the old one is kept as .old).
    local current = io.open(path, "r")

    if current then
        local size = current:seek("end")
        current:close()

        if size and size > LOG_MAX_BYTES then
            os.remove(path .. ".old")
            os.rename(path, path .. ".old")
        end
    end

    local file = io.open(path, "a")

    if file then
        file:write(os.date("%Y-%m-%d %H:%M:%S"), " | ", message, "\n")
        file:close()
    end
end

session.log = log

local function write_lines(path, lines)
    local file, open_error = io.open(path, "w")

    if file == nil then
        return false, open_error
    end

    local ok, write_error = file:write(table.concat(lines, "\n"), "\n")
    file:close()

    if not ok then
        return false, write_error
    end

    return true
end

-- previous\TEAM_..._2026-2027_prev1.csv
local function backup_name(file_name, number)
    return (string.gsub(file_name, "%.csv$", "")) .. "_prev" .. number .. ".csv"
end

-- Puts the new file (already written as .tmp) in place of the old one.
-- The old version goes to previous\ (prev1 = most recent), so nothing is
-- ever lost if something goes wrong.
local function replace_file(season_dir, tmp_path, final_path, file_name)
    local backup_used = nil

    if file_exists(final_path) then
        if SETTINGS.BACKUP_COUNT > 0 then
            local previous_dir = join_path(season_dir, "previous")

            if ensure_dir(previous_dir) then
                local function backup_path(number)
                    return join_path(previous_dir, backup_name(file_name, number))
                end

                os.remove(backup_path(SETTINGS.BACKUP_COUNT))

                for number = SETTINGS.BACKUP_COUNT - 1, 1, -1 do
                    if file_exists(backup_path(number)) then
                        os.rename(backup_path(number), backup_path(number + 1))
                    end
                end

                if os.rename(final_path, backup_path(1)) then
                    backup_used = backup_path(1)
                end
            end
        end

        if backup_used == nil and not os.remove(final_path) then
            os.remove(tmp_path)
            return false, "the old file could not be replaced (is it open in another program?)"
        end
    end

    local ok, rename_error = os.rename(tmp_path, final_path)

    if not ok then
        if backup_used then
            os.rename(backup_used, final_path)
        end

        os.remove(tmp_path)
        return false, rename_error
    end

    return true
end

-- =========================================================
-- STATE FILE (what was exported last, used by the safety check)
-- =========================================================

local STATE_KEYS = {
    "season",
    "teamid",
    "teamname",
    "played_matches",
    "total_appearances",
    "game_date",
    "exported_at",
    "reason",
    "script_version",
}

local function read_state(path)
    local state = {}
    local file = io.open(path, "r")

    if file == nil then
        return state
    end

    for line in file:lines() do
        local key, value = string.match(line, "^([%w_]+)=(.-)%s*$")

        if key then
            state[key] = value
        end
    end

    file:close()
    return state
end

local function write_state(path, state)
    local lines = {}

    for _, key in ipairs(STATE_KEYS) do
        if state[key] ~= nil then
            lines[#lines + 1] = key .. "=" .. tostring(state[key])
        end
    end

    local tmp_path = path .. ".tmp"

    if not write_lines(tmp_path, lines) then
        os.remove(tmp_path)
        return false
    end

    os.remove(path)
    return os.rename(tmp_path, path)
end

-- =========================================================
-- CSV HELPERS
-- =========================================================

local function csv_escape(value)
    if value == nil then
        return ""
    end

    value = tostring(value)

    local separator = SETTINGS.CSV_SEPARATOR

    if string.find(value, separator, 1, true) or string.find(value, "\"", 1, true)
        or string.find(value, "\n", 1, true) or string.find(value, "\r", 1, true) then
        value = string.gsub(value, "\"", "\"\"")
        return "\"" .. value .. "\""
    end

    return value
end

-- "count" is given so that an empty (nil) value in the middle of a row
-- can never shift the next columns.
local function csv_line(values, count)
    local escaped = {}

    for i = 1, count do
        escaped[i] = csv_escape(values[i])
    end

    return table.concat(escaped, SETTINGS.CSV_SEPARATOR)
end

local function csv_header(columns)
    return table.concat(columns, SETTINGS.CSV_SEPARATOR)
end

-- =========================================================
-- CONTEXT: club, season, in-game date
-- =========================================================

-- Identifier of the loaded save (Live Editor function GetSaveUID).
-- nil when this Live Editor does not have it.
local function get_save_uid()
    if type(GetSaveUID) ~= "function" then
        return nil
    end

    local ok, uid = pcall(GetSaveUID)

    if ok and type(uid) == "string" and string.match(uid, "^%w+$") then
        return uid
    end

    return nil
end

-- Keeps only simple characters, so the folder name works everywhere
-- (accents and symbols become "_").
local function safe_folder_name(text)
    local name = string.gsub(tostring(text), "[^%w%-%. ]", "_")
    name = string.gsub(name, "_+", "_")
    name = string.gsub(name, "^[%s%.]+", "")
    name = string.gsub(name, "[%s%.]+$", "")

    if name == "" then
        name = "Club"
    end

    return name
end

local function get_context()
    local team_id = tonumber(GetUserTeamID())

    if team_id == nil or team_id <= 0 then
        return nil, "could not find the club you manage"
    end

    team_id = math.floor(team_id)

    local date = GetCurrentDate()
    local year = date and tonumber(date.year)
    local month = date and tonumber(date.month)
    local day = date and tonumber(date.day)

    if year == nil or year < 1900 or month == nil or month < 1 or month > 12 then
        return nil, "could not read the in-game date"
    end

    year = math.floor(year)
    month = math.floor(month)
    day = math.floor(day or 0)

    local season = SETTINGS.SEASON_LABEL_OVERRIDE

    if season == nil then
        local first_year = year

        if month < SETTINGS.SEASON_START_MONTH then
            first_year = year - 1
        end

        season = string.format("%d-%d", first_year, first_year + 1)
    elseif not string.match(season, "^%d%d%d%d%-%d%d%d%d$") then
        return nil, "SEASON_LABEL_OVERRIDE must look like 2026-2027 (found: " .. tostring(season) .. ")"
    end

    local team_name = tostring(GetTeamName(team_id))
    local save_uid = get_save_uid()

    -- One folder per career: "<club> - <start of the save id>".
    -- Two saves with the same club get two different folders.
    local career_folder = safe_folder_name(team_name) .. " - " .. tostring(team_id)

    if save_uid ~= nil then
        career_folder = safe_folder_name(team_name) .. " - " .. string.sub(save_uid, 1, 8)
    end

    return {
        team_id = team_id,
        team_name = team_name,
        save_uid = save_uid,
        career_folder = career_folder,
        season = season,
        date = date,
        game_date = string.format("%04d-%02d-%02d", year, month, day),
    }
end

-- =========================================================
-- SHARED GAME DATA (same logic as the manual scripts)
-- =========================================================

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

local function load_nations()
    local result = {}
    local nations_table = LE.db:GetTable("nations")

    if nations_table == nil then
        log("WARNING: nations table not found, nationality names will be empty.")
        return result
    end

    local current_record = nations_table:GetFirstRecord()

    while current_record > 0 do
        local nationid = nations_table:GetRecordFieldValue(current_record, "nationid")
        local nationname = nations_table:GetRecordFieldValue(current_record, "nationname")

        if nationid ~= nil then
            result[nationid] = nationname
        end

        current_record = nations_table:GetNextValidRecord()
    end

    return result
end

local function load_contracts()
    local result = {}
    local contract_table = LE.db:GetTable("career_playercontract")

    if contract_table == nil then
        log("WARNING: career_playercontract table not found, contract fields will be empty.")
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

-- Fixtures and standings live in memory (not in the database).
local function get_fce_data_manager()
    local fce_interface = GetPlugin(ENUM_djb2IFCEInterface_CLSS)
    return MEMORY:ReadMultilevelPointer(fce_interface, { 0x18, 0x10, 0x08, 0x00 })
end

local function read_standing(standings_begin, idx)
    local StandingsData = {}
    local mCurrent = standings_begin + (0x18 * idx)

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

local function read_fixtures_memory()
    local fce_data_manager = get_fce_data_manager()

    if fce_data_manager == nil or fce_data_manager == 0 then
        error("fixtures data not found in the game (FCEDataManager)", 0)
    end

    local fixture_list = MEMORY:ReadPointer(fce_data_manager + 0x60)
    local standings_list = MEMORY:ReadPointer(fce_data_manager + 0x88)

    if fixture_list == 0 or standings_list == 0 then
        error("fixture or standings list not found in the game", 0)
    end

    local fixtures_begin = MEMORY:ReadPointer(fixture_list + 0x28)
    local standings_begin = MEMORY:ReadPointer(standings_list + 0x28)
    local max_items_count = MEMORY:ReadInt(fixture_list + 0x1C) - 1

    if max_items_count < -1 or max_items_count > 100000 then
        error("the fixture list looks invalid (size " .. tostring(max_items_count + 1) .. ")", 0)
    end

    if max_items_count >= 0 and (fixtures_begin == 0 or standings_begin == 0) then
        error("the fixture list looks invalid (empty pointer)", 0)
    end

    local fixtures = {}

    for i = 0, max_items_count do
        local mCurrent = fixtures_begin + (0x18 * i)
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

            table.insert(fixtures, FixtureData)
        end
    end

    return {
        fixtures = fixtures,
        standings_begin = standings_begin,
    }
end

-- Data read once per export and shared by the four files.
local function make_shared()
    local cache = {}
    local shared = {}

    function shared.nations()
        if cache.nations == nil then
            cache.nations = load_nations()
        end

        return cache.nations
    end

    function shared.contracts()
        if cache.contracts == nil then
            cache.contracts = load_contracts()
        end

        return cache.contracts
    end

    function shared.fixture_memory()
        if cache.fixture_error ~= nil then
            error(cache.fixture_error, 0)
        end

        if cache.fixture_memory == nil then
            local ok, result = pcall(read_fixtures_memory)

            if not ok then
                cache.fixture_error = tostring(result)
                error(cache.fixture_error, 0)
            end

            cache.fixture_memory = result
        end

        return cache.fixture_memory
    end

    return shared
end

-- =========================================================
-- 1) PLAYER STATS (same as 01_export_season_player_stats.lua)
-- =========================================================

local PLAYER_STATS_COLUMNS = {
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

local function build_stats_row(player, competition, compobjid, stats, row_type)
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

local function build_player_stats(ctx, shared)
    local players_table = LE.db:GetTable("players")

    if players_table == nil then
        error("players table not found", 0)
    end

    local nations = shared.nations()
    local contracts = shared.contracts()
    local current_date = ctx.date
    local players = {}

    -- Players of the managed club
    local current_record = players_table:GetFirstRecord()

    while current_record > 0 do
        local playerid = players_table:GetRecordFieldValue(current_record, "playerid")
        local teamid = GetTeamIdFromPlayerId(playerid)

        if teamid == ctx.team_id then
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

            players[playerid] = {
                season = ctx.season,
                career_teamid = ctx.team_id,
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
        end

        current_record = players_table:GetNextValidRecord()
    end

    -- Season stats (cumulative, per competition)
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

    for _, player in pairs(players) do
        finalize_avg(player.total_stats)
    end

    -- Rows: one per player + competition, then one TOTAL row per player
    local column_count = #PLAYER_STATS_COLUMNS
    local lines = { csv_header(PLAYER_STATS_COLUMNS) }
    local players_count = 0
    local rows_count = 0
    local total_appearances = 0

    for _, player in pairs(players) do
        players_count = players_count + 1

        for _, comp_data in pairs(player.competition_stats) do
            lines[#lines + 1] = csv_line(build_stats_row(
                player,
                comp_data.competition,
                comp_data.compobjid,
                comp_data.stats,
                "COMPETITION"
            ), column_count)

            rows_count = rows_count + 1
        end

        lines[#lines + 1] = csv_line(build_stats_row(
            player,
            "ALL_COMPETITIONS",
            0,
            player.total_stats,
            "TOTAL"
        ), column_count)

        rows_count = rows_count + 1
        total_appearances = total_appearances + player.total_stats.app
    end

    return {
        lines = lines,
        rows = rows_count,
        players = players_count,
        total_appearances = total_appearances,
        summary = string.format("%d rows, %d players, %d appearances", rows_count, players_count, total_appearances),
    }
end

-- =========================================================
-- 2) TRANSFERS (same as 02_export_season_transfers.lua)
-- =========================================================

local TRANSFERS_COLUMNS = {
    "season",
    "career_teamid",
    "direction",
    "type",
    "date",
    "playerid",
    "playername",
    "position",
    "nationalityid",
    "nationality",
    "age",
    "overall",
    "potential",
    "growth_gap",
    "contract_end",
    "squad_role_id",
    "squad_role",
    "is_retiring",
    "teamfromid",
    "teamfromname",
    "teamtoid",
    "teamtoname",
    "fee",
    "total_deal_value",
    "exchangeplayerid",
    "exchangeplayername",
    "deal_note"
}

-- Profiles are only read for the players of the club's transfers
-- (same values as the manual script, which read every player).
local function load_player_profiles(ctx, shared, needed)
    local result = {}

    if next(needed) == nil then
        return result
    end

    local players_table = LE.db:GetTable("players")

    if players_table == nil then
        log("WARNING: players table not found, transfer player details will be empty.")
        return result
    end

    local nations = shared.nations()
    local contracts = shared.contracts()
    local current_date = ctx.date

    local current_record = players_table:GetFirstRecord()

    while current_record > 0 do
        local playerid = players_table:GetRecordFieldValue(current_record, "playerid")

        if playerid ~= nil and playerid > 0 and playerid < 4294967295 and needed[playerid] then
            local preferredposition1 = players_table:GetRecordFieldValue(current_record, "preferredposition1")

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

            result[playerid] = {
                playerid = playerid,
                playername = GetPlayerName(playerid),
                position = get_position_name(preferredposition1),
                nationalityid = nationalityid,
                nationality = nationality,
                age = age,
                overall = overall,
                potential = potential,
                growth_gap = growth_gap,
                contract_end = players_table:GetRecordFieldValue(current_record, "contractvaliduntil"),
                squad_role_id = contract.squad_role_id or "",
                squad_role = contract.squad_role or "",
                is_retiring = players_table:GetRecordFieldValue(current_record, "isretiring")
            }
        end

        current_record = players_table:GetNextValidRecord()
    end

    return result
end

local function get_profile(profiles, playerid)
    if playerid == nil or playerid <= 0 then
        return {}
    end

    return profiles[playerid] or {}
end

local function get_succeeded_ai_club_transfers(out, storage)
    local obj_size = 0xB8

    local vec = MEMORY:ReadPointer(storage + 0x8)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local seller_accepted = MEMORY:ReadBool(current + 0x6E)
            local buyer_accepted = MEMORY:ReadBool(current + 0x6F)

            if seller_accepted or buyer_accepted then
                local final_fee = 0
                local exchange_value = 0

                if seller_accepted then
                    final_fee = MEMORY:ReadInt(MEMORY:ReadPointer(current + 0x28) - 0xC)
                else
                    local mLastReq = MEMORY:ReadPointer(current + 0x48)
                    final_fee = MEMORY:ReadInt(mLastReq - 0x14 + 0x0)
                    exchange_value = MEMORY:ReadInt(mLastReq - 0x14 + 0x4)
                end

                local key = string.format("T%d-%d-%d", playerid, buying_team, selling_team)

                out[key] = {
                    final_fee = final_fee,
                    exchange_value = exchange_value
                }
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_user_club_transfers(out, storage)
    local obj_size = 0xA0

    local vec = MEMORY:ReadPointer(storage + 0x28)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local mActionsBegin = MEMORY:ReadPointer(current + 0x58)
            local mActionsEnd = MEMORY:ReadPointer(current + 0x60)

            if mActionsBegin ~= mActionsEnd then
                local last_action = MEMORY:ReadChar(mActionsEnd - 0xC + 0x8)
                local seller_accepted = last_action == 0
                local buyer_accepted = last_action == 4

                if seller_accepted or buyer_accepted then
                    local final_fee = 0
                    local exchange_value = 0
                    local exchange_player = 0

                    if seller_accepted then
                        local mLastOff = MEMORY:ReadPointer(current + 0x20)
                        exchange_player = MEMORY:ReadInt(mLastOff - 0x28 + 0x0)
                        exchange_value = MEMORY:ReadInt(mLastOff - 0x28 + 0x4)
                        final_fee = MEMORY:ReadInt(mLastOff - 0x28 + 0xC)
                    else
                        local mLastReq = MEMORY:ReadPointer(current + 0x40)
                        exchange_player = MEMORY:ReadInt(mLastReq - 0x28 + 0x0)
                        exchange_value = MEMORY:ReadInt(mLastReq - 0x28 + 0x4)
                        final_fee = MEMORY:ReadInt(mLastReq - 0x28 + 0xC)
                    end

                    local key = string.format("T%d-%d-%d", playerid, buying_team, selling_team)

                    out[key] = {
                        final_fee = final_fee,
                        exchange_player = exchange_player,
                        exchange_value = exchange_value
                    }
                end
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_ai_player_transfers(out, storage)
    local obj_size = 0xB0

    local vec = MEMORY:ReadPointer(storage + 0x10)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local seller_accepted = MEMORY:ReadBool(current + 0x67)

            if seller_accepted then
                local last_action_idx = MEMORY:ReadChar(current + 0x6C)
                local last_action_date = MEMORY:ReadInt(current + 0x70 + (0xC * last_action_idx))

                local key = string.format("T%d-%d-%d", playerid, buying_team, selling_team)

                out[key] = {
                    playerid = playerid,
                    buying_team = buying_team,
                    selling_team = selling_team,
                    date = last_action_date,
                    type = "transfer"
                }
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_ai_player_exchanges(out, storage)
    local obj_size = 0xA8

    local vec = MEMORY:ReadPointer(storage + 0x40)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local seller_accepted = MEMORY:ReadBool(current + 0x67)

            if seller_accepted then
                local last_action_idx = MEMORY:ReadChar(current + 0x6B)
                local last_action_date = MEMORY:ReadInt(current + 0x6C + (0xC * (last_action_idx - 1)))

                local key = string.format("T%d-%d-%d", playerid, buying_team, selling_team)

                out[key] = {
                    playerid = playerid,
                    buying_team = buying_team,
                    selling_team = selling_team,
                    date = last_action_date,
                    type = "transfer"
                }
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_user_player_transfers(out, storage)
    local obj_size = 0x98

    local vec = MEMORY:ReadPointer(storage + 0x38)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local mActionsBegin = MEMORY:ReadPointer(current + 0x50)
            local mActionsEnd = MEMORY:ReadPointer(current + 0x58)

            if mActionsBegin ~= mActionsEnd then
                local last_action = MEMORY:ReadChar(mActionsEnd - 0xC + 0x8)
                local seller_accepted = last_action == 0
                local buyer_accepted = last_action == 4

                if seller_accepted or buyer_accepted then
                    local last_action_date = MEMORY:ReadInt(mActionsEnd - 0xC + 0x0)

                    local key = string.format("T%d-%d-%d", playerid, buying_team, selling_team)

                    out[key] = {
                        playerid = playerid,
                        buying_team = buying_team,
                        selling_team = selling_team,
                        date = last_action_date,
                        type = "transfer"
                    }
                end
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_user_player_exchanges(out, storage)
    local obj_size = 0x98

    local vec = MEMORY:ReadPointer(storage + 0x48)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local mActionsBegin = MEMORY:ReadPointer(current + 0x50)
            local mActionsEnd = MEMORY:ReadPointer(current + 0x58)

            if mActionsBegin ~= mActionsEnd then
                local last_action = MEMORY:ReadChar(mActionsEnd - 0xC + 0x8)
                local seller_accepted = last_action == 0
                local buyer_accepted = last_action == 4

                if seller_accepted or buyer_accepted then
                    local last_action_date = MEMORY:ReadInt(mActionsEnd - 0xC + 0x0)

                    local key = string.format("T%d-%d-%d", playerid, buying_team, selling_team)

                    out[key] = {
                        playerid = playerid,
                        buying_team = buying_team,
                        selling_team = selling_team,
                        date = last_action_date,
                        type = "transfer"
                    }
                end
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_ai_player_loans(out, storage)
    local obj_size = 0x98

    local vec = MEMORY:ReadPointer(storage + 0x20)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local seller_accepted = MEMORY:ReadBool(current + 0x52)

            if seller_accepted then
                local last_action_idx = MEMORY:ReadChar(current + 0x57)
                local last_action_date = MEMORY:ReadInt(current + 0x58 + (0xC * (last_action_idx - 1)))

                local key = string.format("L%d-%d-%d", playerid, buying_team, selling_team)

                out[key] = {
                    playerid = playerid,
                    buying_team = buying_team,
                    selling_team = selling_team,
                    date = last_action_date,
                    type = "loan"
                }
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_ai_club_loans(out, storage)
    local obj_size = 0xB8

    local vec = MEMORY:ReadPointer(storage + 0x18)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local seller_accepted = MEMORY:ReadBool(current + 0x72)
            local buyer_accepted = MEMORY:ReadBool(current + 0x73)

            if seller_accepted or buyer_accepted then
                local key = string.format("L%d-%d-%d", playerid, buying_team, selling_team)

                out[key] = {
                    final_fee = 0,
                    exchange_value = 0
                }
            end
        end

        current = current + obj_size
    end
end

local function get_succeeded_user_club_loans(out, storage)
    local obj_size = 0xF8

    local vec = MEMORY:ReadPointer(storage + 0x30)
    local mBegin = MEMORY:ReadPointer(vec + 0x0)
    local mEnd = MEMORY:ReadPointer(vec + 0x8)

    local current = mBegin

    while current < mEnd do
        local playerid = MEMORY:ReadInt(current + 0x0)
        local buying_team = MEMORY:ReadInt(current + 0x4)
        local selling_team = MEMORY:ReadInt(current + 0x8)

        if playerid > 0 and buying_team > 0 and selling_team > 0 then
            local mActionsBegin = MEMORY:ReadPointer(current + 0x50)
            local mActionsEnd = MEMORY:ReadPointer(current + 0x58)

            if mActionsBegin ~= mActionsEnd then
                local last_action = MEMORY:ReadChar(mActionsEnd - 0xC + 0x8)
                local seller_accepted = last_action == 0
                local buyer_accepted = last_action == 4

                if seller_accepted or buyer_accepted then
                    local key = string.format("L%d-%d-%d", playerid, buying_team, selling_team)

                    out[key] = {
                        final_fee = 0,
                        exchange_value = 0
                    }
                end
            end
        end

        current = current + obj_size
    end
end

local function build_transfers(ctx, shared)
    local transfer_mgr = GetManagerObjByTypeId(ENUM_FCEGameModesFCECareerModeTransferManager)

    if transfer_mgr == nil or transfer_mgr == 0 then
        error("transfer manager not found in the game", 0)
    end

    local neg_storage = MEMORY:ReadPointer(transfer_mgr + 0x1DD0)

    local player_negos = {}
    local club_negos = {}

    get_succeeded_ai_player_transfers(player_negos, neg_storage)
    get_succeeded_ai_player_exchanges(player_negos, neg_storage)
    get_succeeded_ai_player_loans(player_negos, neg_storage)

    get_succeeded_user_player_transfers(player_negos, neg_storage)
    get_succeeded_user_player_exchanges(player_negos, neg_storage)

    get_succeeded_ai_club_transfers(club_negos, neg_storage)
    get_succeeded_ai_club_loans(club_negos, neg_storage)

    get_succeeded_user_club_transfers(club_negos, neg_storage)
    get_succeeded_user_club_loans(club_negos, neg_storage)

    local needed = {}

    for _, player_nego in pairs(player_negos) do
        if player_nego.buying_team == ctx.team_id or player_nego.selling_team == ctx.team_id then
            needed[player_nego.playerid] = true
        end
    end

    local profiles = load_player_profiles(ctx, shared, needed)

    local column_count = #TRANSFERS_COLUMNS
    local lines = { csv_header(TRANSFERS_COLUMNS) }
    local exported_count = 0
    local incoming_count = 0
    local outgoing_count = 0

    for key, player_nego in pairs(player_negos) do
        local club_nego = club_negos[key] or {}

        local is_incoming = player_nego.buying_team == ctx.team_id
        local is_outgoing = player_nego.selling_team == ctx.team_id

        if is_incoming or is_outgoing then
            local direction = "IN"

            if is_outgoing then
                direction = "OUT"
            end

            if is_incoming then
                incoming_count = incoming_count + 1
            end

            if is_outgoing then
                outgoing_count = outgoing_count + 1
            end

            local profile = get_profile(profiles, player_nego.playerid)

            local exchangeplayerid = ""
            local exchangeplayername = ""

            if club_nego.exchange_player and club_nego.exchange_player > 0 then
                exchangeplayerid = club_nego.exchange_player
                exchangeplayername = GetPlayerName(club_nego.exchange_player)
            end

            local fee = club_nego.final_fee or 0
            local exchange_value = club_nego.exchange_value or 0
            local total_deal_value = fee + exchange_value

            lines[#lines + 1] = csv_line({
                ctx.season,
                ctx.team_id,
                direction,
                player_nego.type or "",
                player_nego.date or "",
                player_nego.playerid,
                profile.playername or GetPlayerName(player_nego.playerid),
                profile.position or "",
                profile.nationalityid or "",
                profile.nationality or "",
                profile.age or "",
                profile.overall or "",
                profile.potential or "",
                profile.growth_gap or "",
                profile.contract_end or "",
                profile.squad_role_id or "",
                profile.squad_role or "",
                profile.is_retiring or "",
                player_nego.selling_team,
                GetTeamName(player_nego.selling_team),
                player_nego.buying_team,
                GetTeamName(player_nego.buying_team),
                fee,
                total_deal_value,
                exchangeplayerid,
                exchangeplayername,
                ""
            }, column_count)

            exported_count = exported_count + 1
        end
    end

    return {
        lines = lines,
        rows = exported_count,
        summary = string.format("%d rows (IN %d, OUT %d)", exported_count, incoming_count, outgoing_count),
    }
end

-- =========================================================
-- 3) FIXTURES (same as 03_export_team_fixtures.lua)
-- =========================================================

local FIXTURES_COLUMNS = {
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

local function build_fixtures(ctx, shared)
    local memory = shared.fixture_memory()
    local fixtures = memory.fixtures

    local column_count = #FIXTURES_COLUMNS
    local lines = { csv_header(FIXTURES_COLUMNS) }
    local exported_count = 0
    local played_count = 0
    local upcoming_count = 0

    for i = 1, #fixtures do
        local FixtureData = fixtures[i]

        local compobjid = FixtureData["mCompObjId"]

        local HomeStandingsData = read_standing(memory.standings_begin, FixtureData["mHomeStandingId"])
        local AwayStandingsData = read_standing(memory.standings_begin, FixtureData["mAwayStandingId"])

        local home_teamid = HomeStandingsData["mTeamId"]
        local away_teamid = AwayStandingsData["mTeamId"]

        local is_career_team_match = home_teamid == ctx.team_id or away_teamid == ctx.team_id

        if is_career_team_match then
            local compname = GetCompetitionNameByObjID(compobjid)
            local home_teamname = GetTeamName(home_teamid)
            local away_teamname = GetTeamName(away_teamid)

            local played = FixtureData["mGameCompletion"]
            local is_home = home_teamid == ctx.team_id

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

            lines[#lines + 1] = csv_line({
                ctx.season,
                ctx.team_id,
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
            }, column_count)

            exported_count = exported_count + 1
        end
    end

    return {
        lines = lines,
        rows = exported_count,
        played = played_count,
        summary = string.format("%d rows (%d played, %d upcoming)", exported_count, played_count, upcoming_count),
    }
end

-- =========================================================
-- 4) LEAGUE STANDINGS (same as 04_export_league_standings.lua)
-- =========================================================

local STANDINGS_COLUMNS = {
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

-- The main competition is the one with the most fixtures of the club.
local function find_main_compobjid_for_team(ctx, memory)
    local comp_counts = {}
    local fixtures = memory.fixtures

    for i = 1, #fixtures do
        local fixture = fixtures[i]

        local home_standing = read_standing(memory.standings_begin, fixture["mHomeStandingId"])
        local away_standing = read_standing(memory.standings_begin, fixture["mAwayStandingId"])

        local home_teamid = home_standing["mTeamId"]
        local away_teamid = away_standing["mTeamId"]

        if home_teamid == ctx.team_id or away_teamid == ctx.team_id then
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

local function collect_standings_from_fixtures(memory, main_compobjid)
    local standings_by_teamid = {}
    local fixtures = memory.fixtures

    for i = 1, #fixtures do
        local fixture = fixtures[i]

        if fixture["mCompObjId"] == main_compobjid then
            local home_standing = read_standing(memory.standings_begin, fixture["mHomeStandingId"])
            local away_standing = read_standing(memory.standings_begin, fixture["mAwayStandingId"])

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

    for _, standing in pairs(standings_by_teamid) do
        local calculated = calculate_standing_row(standing)

        table.insert(rows, {
            standing = standing,
            calculated = calculated
        })
    end

    return rows
end

local function build_standings(ctx, shared)
    local memory = shared.fixture_memory()

    local main_compobjid = find_main_compobjid_for_team(ctx, memory)

    if main_compobjid == nil then
        return nil, "no competition found yet for the club"
    end

    local competition_name = GetCompetitionNameByObjID(main_compobjid)

    local rows = collect_standings_from_fixtures(memory, main_compobjid)

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

    local column_count = #STANDINGS_COLUMNS
    local lines = { csv_header(STANDINGS_COLUMNS) }

    for position = 1, #rows do
        local standing = rows[position].standing
        local calculated = rows[position].calculated

        local teamid = standing["mTeamId"]
        local teamname = GetTeamName(teamid)

        lines[#lines + 1] = csv_line({
            ctx.season,
            ctx.team_id,
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
        }, column_count)
    end

    return {
        lines = lines,
        rows = #rows,
        summary = string.format("%d teams (%s)", #rows, tostring(competition_name)),
    }
end

-- =========================================================
-- EXPORT
-- =========================================================

local EXPORT_PARTS = {
    { key = "stats", label = "player stats", file = "SEASON_PLAYER_STATS", build = build_player_stats },
    { key = "transfers", label = "transfers", file = "SEASON_TRANSFERS", build = build_transfers },
    { key = "fixtures", label = "fixtures", file = "FIXTURES", build = build_fixtures },
    { key = "standings", label = "standings", file = "LEAGUE_STANDINGS", build = build_standings },
}

-- SAFETY CHECK
-- Inside a season, the numbers only go up. When they suddenly collapse,
-- the game has most likely reset the season (new season starting) while
-- the in-game date still belongs to the old one. In that case nothing is
-- written, so the finished season is never overwritten.
--   * played matches of the club: must not drop by more than half
--     (a small drop is allowed, for example after reloading an older save)
--   * appearances of the squad: must not drop to zero
local function check_season_progress(previous, built)
    local old_played = tonumber(previous.played_matches)
    local new_played = built.fixtures and built.fixtures.played

    if old_played and new_played and old_played > 0 and new_played * 2 < old_played then
        return string.format("played matches dropped from %d to %d", old_played, new_played)
    end

    local old_apps = tonumber(previous.total_appearances)
    local new_apps = built.stats and built.stats.total_appearances

    if old_apps and new_apps and old_apps > 0 and new_apps == 0 then
        return string.format("squad appearances dropped from %d to 0", old_apps)
    end

    return nil
end

local function export_all(reason)
    local started_at = os.clock()

    local ctx, context_error = get_context()

    if ctx == nil then
        return { ok = false, error = context_error }
    end

    local season_dir = join_path(session.export_root, ctx.career_folder, ctx.season)

    if not ensure_dir(season_dir) then
        return { ok = false, ctx = ctx, error = "could not create the folder " .. season_dir }
    end

    local shared = make_shared()
    local built = {}
    local problems = {}

    for _, part in ipairs(EXPORT_PARTS) do
        local ok, result, note = pcall(part.build, ctx, shared)

        if not ok then
            problems[#problems + 1] = part.label .. ": ERROR " .. tostring(result)
        elseif result == nil then
            problems[#problems + 1] = part.label .. ": not exported (" .. tostring(note) .. ")"
        else
            result.file_name = string.format("TEAM_%d_%s_%s.csv", ctx.team_id, part.file, ctx.season)
            built[part.key] = result
        end
    end

    local state_path = join_path(season_dir, string.format("tco_state_TEAM_%d.txt", ctx.team_id))
    local previous = read_state(state_path)

    local blocked = check_season_progress(previous, built)

    if blocked then
        return {
            ok = false,
            blocked = true,
            ctx = ctx,
            season_dir = season_dir,
            error = blocked,
            problems = problems,
        }
    end

    -- 1) Write every new file next to the old one (.tmp)
    local ready = {}

    for _, part in ipairs(EXPORT_PARTS) do
        local result = built[part.key]

        if result then
            local final_path = join_path(season_dir, result.file_name)
            local tmp_path = final_path .. ".tmp"
            local ok, write_error = write_lines(tmp_path, result.lines)

            if ok then
                ready[#ready + 1] = { part = part, final_path = final_path, tmp_path = tmp_path }
            else
                os.remove(tmp_path)
                problems[#problems + 1] = part.label .. ": could not write the file (" .. tostring(write_error) .. ")"
                built[part.key] = nil
            end
        end
    end

    -- 2) Put them in place (old versions go to previous\)
    for _, item in ipairs(ready) do
        local ok, replace_error = replace_file(season_dir, item.tmp_path, item.final_path, built[item.part.key].file_name)

        if not ok then
            problems[#problems + 1] = item.part.label .. ": " .. tostring(replace_error)
            built[item.part.key] = nil
        end
    end

    local written = 0

    for _ in pairs(built) do
        written = written + 1
    end

    if written > 0 then
        write_state(state_path, {
            season = ctx.season,
            teamid = ctx.team_id,
            teamname = ctx.team_name,
            played_matches = built.fixtures and built.fixtures.played or previous.played_matches,
            total_appearances = built.stats and built.stats.total_appearances or previous.total_appearances,
            game_date = ctx.game_date,
            exported_at = os.date("%Y-%m-%d %H:%M:%S"),
            reason = reason,
            script_version = SCRIPT_VERSION,
        })
    end

    return {
        ok = written > 0,
        ctx = ctx,
        season_dir = season_dir,
        built = built,
        written = written,
        problems = problems,
        seconds = os.clock() - started_at,
        error = written == 0 and "no file could be written" or nil,
    }
end

local function describe_result(result)
    local parts = {}

    if result.built then
        for _, part in ipairs(EXPORT_PARTS) do
            local built = result.built[part.key]

            if built then
                parts[#parts + 1] = part.label .. " " .. built.summary
            end
        end
    end

    return parts
end

local function log_result(reason, result)
    local ctx = result.ctx
    local where = ""

    if ctx then
        where = string.format(" | %s | %s | club %d | game date %s", ctx.career_folder, ctx.season, ctx.team_id, ctx.game_date)
    end

    if result.blocked then
        log("export BLOCKED by the safety check (" .. reason .. ")" .. where .. " | " .. result.error
            .. " | the season files were NOT touched")
        return
    end

    if not result.ok then
        log("export FAILED (" .. reason .. ")" .. where .. " | " .. tostring(result.error))
    else
        local status = "OK"

        if result.problems and #result.problems > 0 then
            status = "PARTIAL"
        end

        log(string.format("export %s (%s)%s | %s | %.2f s", status, reason, where,
            table.concat(describe_result(result), " | "), result.seconds or 0))
    end

    if result.problems then
        for _, problem in ipairs(result.problems) do
            log("  problem: " .. problem)
        end
    end
end

local function export_now(reason)
    if session.busy then
        log("export skipped (" .. reason .. "): another export is still running")
        return nil
    end

    session.busy = true
    local ok, result = pcall(export_all, reason)
    session.busy = false

    if not ok then
        result = { ok = false, error = "unexpected error: " .. tostring(result) }
    end

    log_result(reason, result)

    if result.ok and result.ctx then
        session.last_export_game_date = result.ctx.game_date
    end

    return result
end

-- =========================================================
-- GAME EVENTS
-- =========================================================

local function game_date_text()
    local ok, text = pcall(function()
        local date = GetCurrentDate()
        return string.format("%04d-%02d-%02d", math.floor(date.year), math.floor(date.month), math.floor(date.day))
    end)

    if ok then
        return text
    end

    return "?"
end

local function event_line(event_id, where, in_career)
    local details = where

    if in_career then
        details = details .. ", game date " .. game_date_text()
    end

    return string.format("event %d %s (%s)", event_id, describe_event(event_id), details)
end

-- DIAGNOSTIC (LOG_ALL_EVENTS): one line per event. The same event received
-- several times in a row is written once, then "(repeated N more times)".
local function log_every_event(event_id, where, in_career)
    if event_id == session.last_event_id then
        session.last_event_repeats = session.last_event_repeats + 1
        return
    end

    if session.last_event_id ~= nil and session.last_event_repeats > 0 then
        log(string.format("  (event %d repeated %d more times)", session.last_event_id, session.last_event_repeats))
    end

    session.last_event_id = event_id
    session.last_event_repeats = 0

    log(event_line(event_id, where, in_career))
end

-- When to export (all numbers observed in the game, see EVENTS):
--   * just before each match (37), then again right after it: the game
--     passes a day by itself once the match is over (15);
--   * once a week (16), as a safety net, unless an export already ran on
--     the same in-game day;
--   * at the end of the club's match (7), if the game ever sends it.
-- During a match the game is not "in career mode" for the Live Editor (the
-- club and the in-game date cannot be read), so an export is only marked as
-- pending and runs on the first event received in the career menus.
function session.on_event(event_id)
    if event_id == nil then
        return
    end

    local in_career = IsInCM() and true or false
    local where = in_career and "in career menus" or "outside career menus"

    if SETTINGS.LOG_ALL_EVENTS then
        log_every_event(event_id, where, in_career)
    elseif LOGGED_EVENT_IDS[event_id] then
        log(event_line(event_id, where, in_career))
    end

    if event_id == EVENTS.BEFORE_MATCH then
        session.export_pending = "before match"
        session.after_match_pending = true
    elseif event_id == EVENTS.USER_MATCH_COMPLETED then
        session.export_pending = "match completed"
    elseif event_id == EVENTS.DAY_PASSED and session.after_match_pending and in_career then
        session.after_match_pending = false
        session.export_pending = "after match"
    elseif event_id == EVENTS.WEEK_PASSED and in_career then
        if session.last_export_game_date ~= game_date_text() then
            session.export_pending = "weekly"
        end
    end

    if session.export_pending and in_career then
        local reason = session.export_pending
        session.export_pending = false
        export_now(reason)
    end
end

-- =========================================================
-- MAIN
-- =========================================================

local function show_message(text)
    if MessageBox then
        MessageBox("The Club Office", text)
    end
end

local function build_launch_message(result, already_listening, listening)
    local lines = {}

    lines[#lines + 1] = "The Club Office export - script version " .. SCRIPT_VERSION
    lines[#lines + 1] = ""

    if already_listening then
        lines[#lines + 1] = "Automatic export was already ON (not added twice)."
    elseif listening then
        lines[#lines + 1] = "Automatic export is ON."
    else
        lines[#lines + 1] = "WARNING: automatic export is OFF (AddEventHandler is not available)."
        lines[#lines + 1] = "Only this manual export was done."
    end

    lines[#lines + 1] = ""

    if result and result.ctx then
        local ctx = result.ctx
        lines[#lines + 1] = string.format("Club: %s (%d)", ctx.team_name, ctx.team_id)
        lines[#lines + 1] = string.format("Season: %s   (game date %s)", ctx.season, ctx.game_date)
        lines[#lines + 1] = "Folder: " .. tostring(result.season_dir or session.export_root)
        lines[#lines + 1] = ""
    end

    if result == nil then
        lines[#lines + 1] = "No export now: another export is still running."
    elseif result.blocked then
        lines[#lines + 1] = "SAFETY CHECK: nothing was written."
        lines[#lines + 1] = "The season data looks reset by the game (" .. tostring(result.error) .. ")."
        lines[#lines + 1] = "The files of this season were not touched."
    elseif not result.ok then
        lines[#lines + 1] = "Export FAILED: " .. tostring(result.error)
    else
        lines[#lines + 1] = "Exported now:"

        for _, text in ipairs(describe_result(result)) do
            lines[#lines + 1] = "- " .. text
        end
    end

    if result and result.problems and #result.problems > 0 then
        lines[#lines + 1] = ""
        lines[#lines + 1] = "Problems:"

        for _, problem in ipairs(result.problems) do
            lines[#lines + 1] = "- " .. problem
        end
    end

    lines[#lines + 1] = ""

    if listening then
        lines[#lines + 1] = "Next exports: before and after every match of your team, and once a week."
    end

    if SETTINGS.LOG_ALL_EVENTS then
        lines[#lines + 1] = "Diagnostic: every game event is written to tco_session_log.txt."
    end

    lines[#lines + 1] = "Wrong season? See SEASON_LABEL_OVERRIDE at the top of the script."

    return table.concat(lines, "\n")
end

local function main()
    if not (IsInCM and IsInCM()) then
        show_message("Open your career first, then run tco_session.lua again.")
        return
    end

    session.export_root = find_export_root()

    if session.export_root == nil or not ensure_dir(session.export_root) then
        show_message("Could not create the export folder:\n" .. tostring(session.export_root)
            .. "\n\nNothing was exported.")
        return
    end

    local already_listening = _G.TCO_SESSION_LISTENING == true
    local listening = already_listening

    -- The listener always calls the newest session (re-running the script
    -- replaces it), so it is registered only once per game session.
    _G.TCO_SESSION = session

    if not already_listening and type(AddEventHandler) == "function" then
        AddEventHandler("post__CareerModeEvent", function(_, event_id)
            local current = _G.TCO_SESSION

            if current and current.on_event then
                local ok, event_error = pcall(current.on_event, tonumber(event_id))

                if not ok and current.log then
                    pcall(current.log, "event handler error: " .. tostring(event_error))
                end
            end
        end)

        _G.TCO_SESSION_LISTENING = true
        listening = true
    end

    local listener_text = "listener added"

    if already_listening then
        listener_text = "listener already active (not added twice)"
    elseif not listening then
        listener_text = "AddEventHandler not available: NO automatic export"
    end

    log(string.format("script started (version %s) | %s", SCRIPT_VERSION, listener_text))

    local result = export_now("script launched")
    show_message(build_launch_message(result, already_listening, listening))
end

main()
