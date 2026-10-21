-- =========================================================
-- The Club Office
-- 02_export_season_transfers.lua
--
-- Exports current season transfer history for one specific team.
--
-- Output: TEAM_<teamid>_SEASON_TRANSFERS_<season>.csv
-- =========================================================

require 'imports/career_mode/enums'
require 'imports/career_mode/helpers'
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

local function write_csv_row(row)
    local escaped_row = {}

    for i = 1, #row do
        table.insert(escaped_row, csv_escape(row[i]))
    end

    io.write(table.concat(escaped_row, CSV_SEPARATOR))
    io.write("\n")
end

-- =========================================================
-- PLAYER PROFILE HELPERS
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
            local playerrole = contract_table:GetRecordFieldValue(current_record, "playerrole")

            result[playerid] = {
                squad_role_id = playerrole,
                squad_role = get_squad_role_name(playerrole)
            }
        end

        current_record = contract_table:GetNextValidRecord()
    end

    return result
end

function get_player_profiles(nations, contracts)
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

        if playerid ~= nil and playerid > 0 and playerid < 4294967295 then
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

-- =========================================================
-- TRANSFER MEMORY EXTRACTION
-- Original logic adapted from working transfer history script
-- =========================================================

function get_succeeded_ai_club_transfers(out, storage)
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

function get_succeeded_user_club_transfers(out, storage)
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

function get_succeeded_ai_player_transfers(out, storage)
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

function get_succeeded_ai_player_exchanges(out, storage)
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

function get_succeeded_user_player_transfers(out, storage)
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

function get_succeeded_user_player_exchanges(out, storage)
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

function get_succeeded_ai_player_loans(out, storage)
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

function get_succeeded_ai_club_loans(out, storage)
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

function get_succeeded_user_club_loans(out, storage)
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

-- =========================================================
-- MAIN
-- =========================================================

assert(IsInCM(), "Script must be executed in career mode")

local nations = get_nations()
local contracts = get_contracts()
local profiles = get_player_profiles(nations, contracts)

local transfer_mgr = GetManagerObjByTypeId(ENUM_FCEGameModesFCECareerModeTransferManager)
assert(transfer_mgr ~= 0, "Cant find FCEGameModesFCECareerModeTransferManager")

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

local desktop_path = string.format("%s\\Desktop", os.getenv('USERPROFILE'))

local file_path = string.format(
    "%s\\TEAM_%d_SEASON_TRANSFERS_%s.csv",
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

local exported_count = 0
local incoming_count = 0
local outgoing_count = 0

for key, player_nego in pairs(player_negos) do
    local club_nego = club_negos[key] or {}

    local is_incoming = player_nego.buying_team == CAREER_TEAM_ID
    local is_outgoing = player_nego.selling_team == CAREER_TEAM_ID

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

        local row = {
            SEASON_LABEL,
            CAREER_TEAM_ID,
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
        }

        write_csv_row(row)

        exported_count = exported_count + 1
    end
end

io.close(file)

LOGGER:LogInfo("Done")
LOGGER:LogInfo("Transfers exported: " .. tostring(exported_count))
LOGGER:LogInfo("Incoming: " .. tostring(incoming_count))
LOGGER:LogInfo("Outgoing: " .. tostring(outgoing_count))
LOGGER:LogInfo("CSV exported to: " .. file_path)

MessageBox(
    "The Club Office",
    string.format(
        "Exported transfers\nTotal: %d\nIN: %d\nOUT: %d",
        exported_count,
        incoming_count,
        outgoing_count
    )
)