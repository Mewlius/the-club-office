class_name ExportsData
extends RefCounted
## Reads the files written by 02_Lua/tco_session.lua.
##
## Folder layout:
##   Documents/TheClubOffice/exports/<club> - <save id>/<season>/TEAM_<id>_SEASON_PLAYER_STATS_<season>.csv

const INT_COLUMNS := [
	"playerid", "teamid", "career_teamid", "age", "overall", "potential", "growth_gap",
	"contract_end", "contract_duration_months", "height", "weight", "preferred_foot",
	"skill_moves", "weak_foot", "is_retiring", "compobjid", "appearances", "MOTMs", "goals",
	"assists", "goal_contributions", "yellow_cards", "two_yellow", "red_cards", "saves",
	"goals_conceded", "cleansheets",
]

const DECIMAL_COLUMNS := ["AVG"]

const POSITION_GROUPS := {
	"GK": "gk",
	"SW": "def", "RWB": "def", "RB": "def", "RCB": "def", "CB": "def", "LCB": "def", "LB": "def", "LWB": "def",
	"RDM": "mid", "CDM": "mid", "LDM": "mid", "RM": "mid", "RCM": "mid", "CM": "mid", "LCM": "mid",
	"LM": "mid", "RAM": "mid", "CAM": "mid", "LAM": "mid",
	"RF": "att", "CF": "att", "LF": "att", "RW": "att", "RS": "att", "ST": "att", "LS": "att", "LW": "att",
}

## Goalkeepers first, then defence, midfield, attack (the usual squad sheet order)
const POSITION_ORDER := [
	"GK", "SW", "RWB", "RB", "RCB", "CB", "LCB", "LB", "LWB", "RDM", "CDM", "LDM", "RM", "RCM",
	"CM", "LCM", "LM", "RAM", "CAM", "LAM", "RF", "CF", "LF", "RW", "RS", "ST", "LS", "LW",
]


## Same rule as tco_session.lua: the Documents folder (OneDrive included).
static func find_exports_root() -> String:
	var override := OS.get_environment("TCO_EXPORTS")
	if override != "":
		return override

	var candidates: Array[String] = [OS.get_system_dir(OS.SYSTEM_DIR_DOCUMENTS)]
	var profile := OS.get_environment("USERPROFILE")
	if profile != "":
		candidates.append(profile.path_join("Documents"))
	var onedrive := OS.get_environment("OneDrive")
	if onedrive != "":
		candidates.append(onedrive.path_join("Documents"))

	for documents in candidates:
		var exports := documents.path_join("TheClubOffice").path_join("exports")
		if DirAccess.dir_exists_absolute(exports):
			return exports

	return candidates[0].path_join("TheClubOffice").path_join("exports")


static func _sorted_dirs(path: String) -> Array[String]:
	var result: Array[String] = []
	var dir := DirAccess.open(path)
	if dir == null:
		return result
	for name in dir.get_directories():
		result.append(name)
	result.sort()
	return result


static func stats_file(season_dir: String) -> String:
	var dir := DirAccess.open(season_dir)
	if dir == null:
		return ""
	var files := Array(dir.get_files())
	files.sort()
	for file_name in files:
		if String(file_name).match("TEAM_*_SEASON_PLAYER_STATS_*.csv"):
			return season_dir.path_join(file_name)
	return ""


## Career folders that contain at least one season with player stats.
static func list_careers(root: String) -> Array[String]:
	var careers: Array[String] = []
	for career in _sorted_dirs(root):
		var career_dir := root.path_join(career)
		for season in _sorted_dirs(career_dir):
			if stats_file(career_dir.path_join(season)) != "":
				careers.append(career_dir)
				break
	return careers


static func list_seasons(career_dir: String) -> Array[String]:
	var seasons: Array[String] = []
	for season in _sorted_dirs(career_dir):
		if stats_file(career_dir.path_join(season)) != "":
			seasons.append(season)
	return seasons


## "AFC Wimbledon - 686228de" -> "AFC Wimbledon", unless two careers share the club.
static func career_label(career_dir: String, all_careers: Array[String]) -> String:
	var folder := career_dir.get_file()
	var club := folder.get_slice(" - ", 0)
	var same_club := 0
	for other in all_careers:
		if other.get_file().get_slice(" - ", 0) == club:
			same_club += 1
	return club if same_club == 1 else folder


static func _convert(column: String, value: String) -> Variant:
	if column in DECIMAL_COLUMNS:
		return snappedf(value.to_float(), 0.01) if value.is_valid_float() else null
	if column in INT_COLUMNS:
		if value.is_valid_int():
			return value.to_int()
		if value.is_valid_float():
			return int(value.to_float())
		return null
	return value


static func load_player_stats(season_dir: String) -> Array[Dictionary]:
	var rows: Array[Dictionary] = []
	var path := stats_file(season_dir)
	if path == "":
		return rows
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return rows

	var header := file.get_csv_line(";")
	while not file.eof_reached():
		var values := file.get_csv_line(";")
		if values.size() < header.size():
			continue
		var row := {}
		for i in header.size():
			row[header[i]] = _convert(header[i], values[i])
		row["pos_group"] = POSITION_GROUPS.get(row.get("position", ""), "mid")
		rows.append(row)
	return rows


## What tco_session.lua exported last (tco_state_TEAM_<id>.txt).
static func read_state(season_dir: String) -> Dictionary:
	var state := {}
	var dir := DirAccess.open(season_dir)
	if dir == null:
		return state
	for file_name in dir.get_files():
		if not file_name.match("tco_state_TEAM_*.txt"):
			continue
		var file := FileAccess.open(season_dir.path_join(file_name), FileAccess.READ)
		if file == null:
			continue
		while not file.eof_reached():
			var line := file.get_line()
			if "=" in line:
				state[line.get_slice("=", 0).strip_edges()] = line.substr(line.find("=") + 1).strip_edges()
	return state
