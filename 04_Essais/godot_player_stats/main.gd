extends Control
## The Club Office - interface trial with Godot: the Player stats page.
##
## Reads the files written by 02_Lua/tco_session.lua directly from
## Documents/TheClubOffice/exports (no manual import, no team id to type).
## The layout is in main.tscn (editable in the Godot editor), this script fills it.

const ALL_COMPETITIONS := "All competitions"
const ALL := "All"
const ROLES := ["Crucial", "Important", "Rotation", "Sporadic", "Prospect"]
const FOOT := {1: "Right", 2: "Left"}

const INK := Color("#15233F")
const MUTED := Color("#5B6B82")
const LINE := Color("#DCE2EA")
const TURF := Color("#1F7A4D")
const POSITION_COLORS := {
	"gk": Color("#C98A00"),
	"def": Color("#2D6CB5"),
	"mid": Color("#2E8A57"),
	"att": Color("#C7432E"),
}

## Column holding the player id (metadata), and column of the position badge
const ID_COLUMN := 1
const BADGE_COLUMN := 0

## Table columns: title, field, kind, width (0 = takes the free space)
const COLUMNS := [
	["Pos", "position", "pos", 58],
	["Player", "playername", "text", 0],
	["Age", "age", "int", 46],
	["OVR", "overall", "int", 48],
	["POT", "potential", "int", 48],
	["Growth", "growth_gap", "growth", 62],
	["Role", "squad_role", "text", 96],
	["Apps", "appearances", "int", 56],
	["AVG", "AVG", "dec", 54],
	["Goals", "goals", "int", 56],
	["Assists", "assists", "int", 64],
	["G+A", "goal_contributions", "int", 50],
	["MOTM", "MOTMs", "int", 58],
	["YC", "yellow_cards", "int", 40],
	["RC", "red_cards", "int", 40],
	["CS", "cleansheets", "int", 40],
]

var exports_root := ""
var careers: Array[String] = []
var career_dir := ""
var season := ""
var rows: Array[Dictionary] = []
var competition := ALL_COMPETITIONS
var selected_id: Variant = null
var sort_field := "appearances"
var sort_descending := true
var competition_group := ButtonGroup.new()
var _filling := false

@onready var header_bar: PanelContainer = %HeaderBar
@onready var page: MarginContainer = %Page
@onready var empty_state: Control = %EmptyState
@onready var empty_path: Label = %EmptyPath
@onready var career_option: OptionButton = %CareerOption
@onready var season_option: OptionButton = %SeasonOption
@onready var export_note: Label = %ExportNote
@onready var reload_button: Button = %ReloadButton
@onready var competition_bar: HBoxContainer = %CompetitionBar
@onready var position_option: OptionButton = %PositionOption
@onready var role_option: OptionButton = %RoleOption
@onready var nation_option: OptionButton = %NationOption
@onready var min_apps: SpinBox = %MinApps
@onready var search: LineEdit = %Search
@onready var summary: HBoxContainer = %Summary
@onready var table: Tree = %Table
@onready var panel_content: VBoxContainer = %PanelContent


func _ready() -> void:
	get_window().title = "Player stats - The Club Office"
	_setup_table()
	career_option.item_selected.connect(_on_career_selected)
	season_option.item_selected.connect(_on_season_selected)
	reload_button.pressed.connect(_reload_files)
	for option in [position_option, role_option, nation_option]:
		option.item_selected.connect(func(_index: int) -> void: _refresh())
	min_apps.value_changed.connect(func(_value: float) -> void: _refresh())
	search.text_changed.connect(func(_text: String) -> void: _refresh())
	table.column_title_clicked.connect(_on_column_title_clicked)
	table.item_selected.connect(_on_row_selected)

	exports_root = ExportsData.find_exports_root()
	careers = ExportsData.list_careers(exports_root)
	if careers.is_empty():
		header_bar.visible = false
		page.visible = false
		empty_state.visible = true
		empty_path.text = exports_root
		return

	_fill_careers(careers[0])


# ----------------------------------------------------------------------
# Career, season, competition
# ----------------------------------------------------------------------

func _fill_careers(keep: String) -> void:
	career_option.clear()
	for path in careers:
		career_option.add_item(ExportsData.career_label(path, careers))
	var index := maxi(careers.find(keep), 0)
	career_option.select(index)
	_on_career_selected(index)


func _on_career_selected(index: int) -> void:
	career_dir = careers[index]
	var seasons := ExportsData.list_seasons(career_dir)
	season_option.clear()
	for name in seasons:
		season_option.add_item(name)
	if seasons.is_empty():
		return
	season_option.select(seasons.size() - 1)
	_on_season_selected(seasons.size() - 1)


func _on_season_selected(index: int) -> void:
	season = season_option.get_item_text(index)
	var season_dir := career_dir.path_join(season)
	rows = ExportsData.load_player_stats(season_dir)
	var state := ExportsData.read_state(season_dir)
	export_note.text = "Last export: %s in the game" % _format_game_date(state.get("game_date", ""))
	competition = ALL_COMPETITIONS
	selected_id = null
	_fill_competitions()
	_refresh_filters()
	_refresh()


func _fill_competitions() -> void:
	for child in competition_bar.get_children():
		child.queue_free()

	# Competitions ordered by matches played (the league first)
	var played := {}
	for row in rows:
		if row.get("row_type") == "COMPETITION" and str(row.get("competition", "")) != "":
			var name := str(row["competition"])
			played[name] = int(played.get(name, 0)) + int(_number(row.get("appearances")))
	var names: Array = played.keys()
	names.sort_custom(func(a, b) -> bool: return played[a] > played[b])

	for name in [ALL_COMPETITIONS] + names:
		var button := Button.new()
		button.text = name
		button.toggle_mode = true
		button.button_group = competition_group
		button.theme_type_variation = "Segment"
		button.button_pressed = name == competition
		button.pressed.connect(_on_competition.bind(name))
		competition_bar.add_child(button)


func _on_competition(name: String) -> void:
	competition = name
	_refresh_filters()
	_refresh()


func _reload_files() -> void:
	var keep_career := career_dir
	var keep_season := season
	careers = ExportsData.list_careers(exports_root)
	if careers.is_empty():
		return
	_fill_careers(keep_career)
	for i in season_option.item_count:
		if season_option.get_item_text(i) == keep_season and season_option.selected != i:
			season_option.select(i)
			_on_season_selected(i)


# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------

func _view_rows() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for row in rows:
		if competition == ALL_COMPETITIONS:
			if row.get("row_type") == "TOTAL":
				result.append(row)
		elif row.get("row_type") == "COMPETITION" and row.get("competition") == competition:
			result.append(row)
	return result


func _option_value(option: OptionButton) -> String:
	return option.get_item_text(option.selected) if option.selected >= 0 else ALL


func _filtered_rows() -> Array[Dictionary]:
	var position := _option_value(position_option)
	var role := _option_value(role_option)
	var nation := _option_value(nation_option)
	var text := search.text.strip_edges().to_lower()
	var result: Array[Dictionary] = []
	for row in _view_rows():
		if position != ALL and row.get("position") != position:
			continue
		if role != ALL and row.get("squad_role") != role:
			continue
		if nation != ALL and row.get("nationality") != nation:
			continue
		if _number(row.get("appearances")) < min_apps.value:
			continue
		if text != "" and not str(row.get("playername", "")).to_lower().contains(text):
			continue
		result.append(row)
	return result


func _set_options(option: OptionButton, values: Array, order: Callable) -> void:
	var keep := _option_value(option)
	var unique := {}
	for value in values:
		if value != null and str(value) != "":
			unique[str(value)] = true
	var sorted_values: Array = unique.keys()
	sorted_values.sort_custom(order)
	option.clear()
	option.add_item(ALL)
	for value in sorted_values:
		option.add_item(value)
	var index := sorted_values.find(keep)
	option.select(index + 1 if index >= 0 else 0)


func _refresh_filters() -> void:
	var view := _view_rows()
	_set_options(position_option, view.map(func(r): return r.get("position")),
		func(a, b) -> bool: return _position_rank(a) < _position_rank(b))
	_set_options(role_option, view.map(func(r): return r.get("squad_role")),
		func(a, b) -> bool: return _role_rank(a) < _role_rank(b))
	_set_options(nation_option, view.map(func(r): return r.get("nationality")),
		func(a, b) -> bool: return a < b)


# ----------------------------------------------------------------------
# Table, summary
# ----------------------------------------------------------------------

func _setup_table() -> void:
	table.columns = COLUMNS.size()
	table.column_titles_visible = true
	table.hide_root = true
	table.select_mode = Tree.SELECT_ROW
	for i in COLUMNS.size():
		var kind: String = COLUMNS[i][2]
		var width: int = COLUMNS[i][3]
		table.set_column_expand(i, width == 0)
		table.set_column_custom_minimum_width(i, width if width > 0 else 150)
		table.set_column_clip_content(i, true)
		var left := kind == "text" or kind == "pos"
		table.set_column_title_alignment(i, HORIZONTAL_ALIGNMENT_LEFT if left else HORIZONTAL_ALIGNMENT_RIGHT)
	_update_titles()


func _update_titles() -> void:
	for i in COLUMNS.size():
		var title: String = COLUMNS[i][0]
		if COLUMNS[i][1] == sort_field:
			title += " ↓" if sort_descending else " ↑"
		table.set_column_title(i, title)


func _on_column_title_clicked(column: int, mouse_button: int) -> void:
	if mouse_button != MOUSE_BUTTON_LEFT:
		return
	var field: String = COLUMNS[column][1]
	var kind: String = COLUMNS[column][2]
	if field == sort_field:
		sort_descending = not sort_descending
	else:
		sort_field = field
		# Numbers start with the biggest, names and positions with A / goalkeepers
		sort_descending = kind not in ["text", "pos"]
	_update_titles()
	_refresh()


func _sort_key(row: Dictionary) -> Variant:
	if sort_field == "position":
		return _position_rank(row.get("position"))
	var value: Variant = row.get(sort_field)
	if value is String:
		return value.to_lower()
	return _number(value)


func _sorted(list: Array[Dictionary]) -> Array[Dictionary]:
	var result := list.duplicate()
	result.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var key_a: Variant = _sort_key(a)
		var key_b: Variant = _sort_key(b)
		if key_a == key_b:
			return str(a.get("playername", "")) < str(b.get("playername", ""))
		return key_a > key_b if sort_descending else key_a < key_b)
	return result


func _refresh() -> void:
	var shown := _sorted(_filtered_rows())
	_fill_table(shown)
	_fill_summary(shown)
	if selected_id == null:
		_show_overview(shown)


func _fill_table(shown: Array[Dictionary]) -> void:
	_filling = true
	table.clear()
	var tree_root := table.create_item()
	for row in shown:
		var item := table.create_item(tree_root)
		for i in COLUMNS.size():
			var field: String = COLUMNS[i][1]
			var kind: String = COLUMNS[i][2]
			var value: Variant = row.get(field)
			match kind:
				"pos":
					# Drawn as a badge: the text and colour are kept aside, the cell itself stays empty
					item.set_cell_mode(i, TreeItem.CELL_MODE_CUSTOM)
					item.set_metadata(i, {
						"text": str(value),
						"color": POSITION_COLORS.get(row.get("pos_group"), POSITION_COLORS["mid"]),
					})
					item.set_custom_draw_callback(i, _draw_position_badge)
				"text":
					item.set_text(i, str(value) if value != null else "-")
				"dec":
					item.set_text(i, "%.2f" % value if value else "-")
					item.set_text_alignment(i, HORIZONTAL_ALIGNMENT_RIGHT)
				"growth":
					var growth := int(_number(value))
					item.set_text(i, "+%d" % growth if growth > 0 else str(growth))
					item.set_text_alignment(i, HORIZONTAL_ALIGNMENT_RIGHT)
					if growth > 0:
						item.set_custom_color(i, TURF)
				_:
					item.set_text(i, str(value) if value != null else "-")
					item.set_text_alignment(i, HORIZONTAL_ALIGNMENT_RIGHT)
		item.set_metadata(ID_COLUMN, row.get("playerid"))
		if row.get("playerid") == selected_id:
			item.select(0)
	_filling = false


## The position cell: a coloured badge (goalkeeper, defence, midfield, attack).
func _draw_position_badge(item: TreeItem, rect: Rect2) -> void:
	var font := table.get_theme_font("font", "SummaryValue")
	var badge_data: Dictionary = item.get_metadata(BADGE_COLUMN)
	var text: String = badge_data["text"]
	var badge := Rect2(rect.position.x + 6, rect.position.y + (rect.size.y - 20) / 2.0, 40, 20)
	var style := StyleBoxFlat.new()
	style.bg_color = badge_data["color"]
	style.set_corner_radius_all(3)
	table.draw_style_box(style, badge)
	var baseline := badge.position.y + (badge.size.y + font.get_ascent(13) - font.get_descent(13)) / 2.0
	table.draw_string(font, Vector2(badge.position.x, baseline), text, HORIZONTAL_ALIGNMENT_CENTER, badge.size.x, 13, Color.WHITE)


func _fill_summary(shown: Array[Dictionary]) -> void:
	for child in summary.get_children():
		child.queue_free()
	var used := 0
	for row in shown:
		if _number(row.get("appearances")) > 0:
			used += 1
	var facts := [
		[str(shown.size()), "players"],
		[str(used), "played"],
		[_mean(shown, "age"), "average age"],
		[_mean(shown, "overall"), "average OVR"],
		[_mean(shown, "potential"), "average POT"],
	]
	for fact in facts:
		var box := HBoxContainer.new()
		box.add_theme_constant_override("separation", 6)
		var value := Label.new()
		value.theme_type_variation = "SummaryValue"
		value.text = fact[0]
		var label := Label.new()
		label.theme_type_variation = "SummaryLabel"
		label.text = fact[1]
		label.size_flags_vertical = Control.SIZE_SHRINK_END
		box.add_child(value)
		box.add_child(label)
		summary.add_child(box)


func _on_row_selected() -> void:
	if _filling:
		return
	var item := table.get_selected()
	if item != null:
		_show_player(item.get_metadata(ID_COLUMN))


# ----------------------------------------------------------------------
# Side panel: top contributors, or one player
# ----------------------------------------------------------------------

func _clear_panel() -> void:
	for child in panel_content.get_children():
		child.queue_free()


func _add_label(parent: Control, text: String, variation: String) -> Label:
	var label := Label.new()
	label.text = text
	label.theme_type_variation = variation
	parent.add_child(label)
	return label


func _show_overview(shown: Array[Dictionary] = []) -> void:
	selected_id = null
	if shown.is_empty() and table.get_root() != null:
		shown = _sorted(_filtered_rows())
	table.deselect_all()
	_clear_panel()
	_add_label(panel_content, "Top goal contributions", "SideTitle")

	var top: Array[Dictionary] = []
	for row in shown:
		if _number(row.get("goal_contributions")) > 0:
			top.append(row)
	top.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if _number(a.get("goal_contributions")) == _number(b.get("goal_contributions")):
			return _number(a.get("goals")) > _number(b.get("goals"))
		return _number(a.get("goal_contributions")) > _number(b.get("goal_contributions")))
	top = top.slice(0, 8)

	if top.is_empty():
		_add_label(panel_content, "No goals or assists yet in this view.", "Muted")
		return

	var names: Array[String] = []
	var goals: Array[int] = []
	var assists: Array[int] = []
	var ids: Array = []
	for row in top:
		names.append(str(row.get("playername", "")))
		goals.append(int(_number(row.get("goals"))))
		assists.append(int(_number(row.get("assists"))))
		ids.append(row.get("playerid"))
	var chart := BarChart.new()
	chart.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel_content.add_child(chart)
	chart.set_data(names, goals, assists)
	chart.bar_clicked.connect(func(index: int) -> void: _show_player(ids[index]))

	var note := _add_label(panel_content, "Click a player in the table or in the chart to open their sheet.", "Muted")
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART


func _show_player(player_id: Variant) -> void:
	var total: Dictionary = {}
	var competitions: Array[Dictionary] = []
	for row in rows:
		if row.get("playerid") != player_id:
			continue
		if row.get("row_type") == "TOTAL":
			total = row
		elif row.get("row_type") == "COMPETITION":
			competitions.append(row)
	if total.is_empty():
		return

	selected_id = player_id
	_select_row(player_id)
	_clear_panel()

	# Name, positions and close button, with the position colour on the left
	var card := PanelContainer.new()
	var card_style := StyleBoxFlat.new()
	card_style.bg_color = Color(1, 1, 1, 0)
	card_style.border_width_left = 6
	card_style.border_color = POSITION_COLORS.get(total.get("pos_group"), POSITION_COLORS["mid"])
	card_style.content_margin_left = 14
	card.add_theme_stylebox_override("panel", card_style)
	panel_content.add_child(card)

	var head := HBoxContainer.new()
	card.add_child(head)
	var identity := VBoxContainer.new()
	identity.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(identity)
	var player_name := _add_label(identity, str(total.get("playername", "")), "PlayerName")
	player_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var badges := HBoxContainer.new()
	badges.add_theme_constant_override("separation", 4)
	identity.add_child(badges)
	var first := true
	for key in ["position", "second_position", "third_position", "fourth_position"]:
		var position := str(total.get(key, ""))
		if position != "" and position != "<null>":
			badges.add_child(_badge(position, first))
			first = false
	var close := Button.new()
	close.text = "✕"
	close.tooltip_text = "Close"
	close.theme_type_variation = "CloseButton"
	close.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	close.pressed.connect(func() -> void: _show_overview())
	head.add_child(close)

	# Ratings
	var ratings := HBoxContainer.new()
	ratings.add_theme_constant_override("separation", 24)
	panel_content.add_child(ratings)
	var growth := int(_number(total.get("growth_gap")))
	for rating in [[str(total.get("overall", "-")), "OVR"], [str(total.get("potential", "-")), "POT"],
			["+%d" % growth if growth > 0 else str(growth), "growth"]]:
		var box := HBoxContainer.new()
		box.add_theme_constant_override("separation", 6)
		_add_label(box, rating[0], "RatingValue")
		var label := _add_label(box, rating[1], "RatingLabel")
		label.size_flags_vertical = Control.SIZE_SHRINK_END
		ratings.add_child(box)

	_add_facts("Profile", [
		["Nationality", total.get("nationality")],
		["Age", total.get("age")],
		["Height / weight", "%s cm / %s kg" % [total.get("height"), total.get("weight")]],
		["Preferred foot", FOOT.get(total.get("preferred_foot"), total.get("preferred_foot"))],
		["Skill moves", total.get("skill_moves")],
		["Weak foot", total.get("weak_foot")],
	])
	_add_facts("Contract", [
		["Squad role", total.get("squad_role")],
		["Contract until", total.get("contract_end")],
		["Length", "%s months" % total.get("contract_duration_months")],
		["Retiring", "Yes" if total.get("is_retiring") == 1 else "No"],
	])

	_add_label(panel_content, "This season", "SectionTitle")
	if competitions.is_empty():
		_add_label(panel_content, "No appearance this season.", "Muted")
		return
	var grid := GridContainer.new()
	grid.columns = 6
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 3)
	panel_content.add_child(grid)
	for title in ["Competition", "Apps", "AVG", "G", "A", "MOTM"]:
		var header := _add_label(grid, title, "CompHeader")
		if title != "Competition":
			header.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	var lines: Array[Dictionary] = competitions.duplicate()
	var total_line := total.duplicate()
	total_line["competition"] = "All competitions"
	lines.append(total_line)
	for line in lines:
		var variation := "CompTotal" if line.get("row_type") == "TOTAL" else "CompValue"
		var name_label := _add_label(grid, str(line.get("competition", "")), variation)
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_label.clip_text = true
		for key in ["appearances", "AVG", "goals", "assists", "MOTMs"]:
			var value: Variant = line.get(key)
			var text := ("%.2f" % value if value else "-") if key == "AVG" else str(value if value != null else "-")
			var cell := _add_label(grid, text, variation)
			cell.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT


func _add_facts(title: String, facts: Array) -> void:
	_add_label(panel_content, title, "SectionTitle")
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 3)
	panel_content.add_child(grid)
	for fact in facts:
		var key := _add_label(grid, fact[0], "FactKey")
		key.custom_minimum_size.x = 120
		var value: Variant = fact[1]
		_add_label(grid, str(value) if value != null and str(value) != "" else "-", "FactValue")


func _badge(position: String, primary: bool) -> PanelContainer:
	var badge := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.set_corner_radius_all(3)
	style.content_margin_left = 6
	style.content_margin_right = 6
	style.content_margin_top = 1
	style.content_margin_bottom = 1
	var label := Label.new()
	label.text = position
	label.theme_type_variation = "BadgeLabel"
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.custom_minimum_size.x = 30
	if primary:
		style.bg_color = POSITION_COLORS.get(ExportsData.POSITION_GROUPS.get(position, "mid"), POSITION_COLORS["mid"])
	else:
		style.bg_color = Color(1, 1, 1, 0)
		style.border_color = LINE
		style.set_border_width_all(1)
		label.add_theme_color_override("font_color", MUTED)
	badge.add_theme_stylebox_override("panel", style)
	badge.add_child(label)
	return badge


func _select_row(player_id: Variant) -> void:
	_filling = true
	var item := table.get_root().get_first_child() if table.get_root() != null else null
	while item != null:
		if item.get_metadata(ID_COLUMN) == player_id:
			item.select(0)
			table.scroll_to_item(item)
			break
		item = item.get_next()
	_filling = false


# ----------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------

func _number(value: Variant) -> float:
	return float(value) if value is int or value is float else 0.0


func _mean(list: Array[Dictionary], field: String) -> String:
	var total := 0.0
	var count := 0
	for row in list:
		var value: Variant = row.get(field)
		if value is int or value is float:
			total += value
			count += 1
	return "%.1f" % (total / count) if count > 0 else "-"


func _position_rank(position: Variant) -> int:
	var index := ExportsData.POSITION_ORDER.find(position)
	return index if index >= 0 else 99


func _role_rank(role: Variant) -> int:
	var index := ROLES.find(role)
	return index if index >= 0 else 99


func _format_game_date(text: String) -> String:
	var parts := text.split("-")
	if parts.size() != 3:
		return "unknown"
	var months := ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
	var month := parts[1].to_int()
	if month < 1 or month > 12:
		return "unknown"
	return "%d %s %s" % [parts[2].to_int(), months[month - 1], parts[0]]
