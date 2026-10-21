class_name BarChart
extends Control
## Horizontal stacked bars: goals + assists per player.
## Drawn by hand: Godot has no ready-made chart.

signal bar_clicked(index: int)

const INK := Color("#15233F")
const MUTED := Color("#5B6B82")
const ASSIST := Color("#93A6C2")
const HOVER := Color(0.08, 0.14, 0.25, 0.05)

const ROW_HEIGHT := 34.0
const BAR_HEIGHT := 14.0
const LEGEND_HEIGHT := 30.0
const FONT_SIZE := 13

var names: Array[String] = []
var goals: Array[int] = []
var assists: Array[int] = []
var _hover := -1


func _ready() -> void:
	mouse_filter = MOUSE_FILTER_STOP
	mouse_default_cursor_shape = CURSOR_POINTING_HAND


func set_data(new_names: Array[String], new_goals: Array[int], new_assists: Array[int]) -> void:
	names = new_names
	goals = new_goals
	assists = new_assists
	custom_minimum_size.y = LEGEND_HEIGHT + ROW_HEIGHT * names.size() + 6
	queue_redraw()


func _baseline(font: Font, center_y: float) -> float:
	return center_y + (font.get_ascent(FONT_SIZE) - font.get_descent(FONT_SIZE)) / 2.0


func _draw() -> void:
	var font := get_theme_font("font", "Label")

	# Legend
	draw_rect(Rect2(0, 6, 10, 10), INK)
	draw_string(font, Vector2(16, _baseline(font, 11)), "Goals", HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE, MUTED)
	draw_rect(Rect2(70, 6, 10, 10), ASSIST)
	draw_string(font, Vector2(86, _baseline(font, 11)), "Assists", HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE, MUTED)

	if names.is_empty():
		return

	var name_width := 0.0
	for player_name in names:
		name_width = maxf(name_width, font.get_string_size(player_name, HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE).x)
	name_width = minf(name_width, size.x * 0.45)

	var x0 := name_width + 10.0
	var x_max := size.x - 26.0
	var max_total := 1
	for i in names.size():
		max_total = maxi(max_total, goals[i] + assists[i])
	var unit := (x_max - x0) / max_total

	for i in names.size():
		var top := LEGEND_HEIGHT + i * ROW_HEIGHT
		var center := top + ROW_HEIGHT / 2.0
		if i == _hover:
			draw_rect(Rect2(0, top, size.x, ROW_HEIGHT), HOVER)
		draw_string(font, Vector2(0, _baseline(font, center)), names[i], HORIZONTAL_ALIGNMENT_RIGHT, name_width, FONT_SIZE, INK)
		var goals_width := goals[i] * unit
		var assists_width := assists[i] * unit
		draw_rect(Rect2(x0, center - BAR_HEIGHT / 2.0, goals_width, BAR_HEIGHT), INK)
		draw_rect(Rect2(x0 + goals_width, center - BAR_HEIGHT / 2.0, assists_width, BAR_HEIGHT), ASSIST)
		draw_string(font, Vector2(x0 + goals_width + assists_width + 6, _baseline(font, center)),
			str(goals[i] + assists[i]), HORIZONTAL_ALIGNMENT_LEFT, -1, FONT_SIZE, INK)


func _row_at(y: float) -> int:
	var index := int(floor((y - LEGEND_HEIGHT) / ROW_HEIGHT))
	return index if y >= LEGEND_HEIGHT and index < names.size() else -1


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		var index := _row_at(event.position.y)
		if index != _hover:
			_hover = index
			queue_redraw()
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var index := _row_at(event.position.y)
		if index >= 0:
			bar_clicked.emit(index)


func _notification(what: int) -> void:
	if what == NOTIFICATION_MOUSE_EXIT and _hover != -1:
		_hover = -1
		queue_redraw()
	elif what == NOTIFICATION_RESIZED:
		queue_redraw()
