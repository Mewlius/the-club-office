# Trial: Player stats page with Godot

A trial to compare interface tools. It does not change the app in `03_App`.

## Launch (Windows)

1. Download **Godot 4.7** (the standard version, not ".NET") from godotengine.org and unzip it. There is nothing to install: the `.exe` is the editor.
2. Start Godot. In the project list, click **Import** and select `04_Essais/godot_player_stats/project.godot`, then **Import & Edit**.
3. Press **F5** (or the play button at the top right): the page opens in its own window.

The first opening creates a hidden `.godot` folder (a cache, ignored by Git).

## What it shows

The same page as the NiceGUI trial, read directly from the files written by `02_Lua/tco_session.lua`:

```text
Documents\TheClubOffice\exports\<club> - <save id>\<season>\
```

- career and season in the header, all competitions or one competition;
- filters: position, squad role, nationality, minimum appearances, search;
- squad summary;
- table sorted by clicking a column title;
- right panel: top goal contributions (click a bar to open the player), or the sheet of the player clicked in the table.

`Reload files` reads the folder again after a new export.

## Changing the layout

The layout is in `main.tscn`: open it in the editor (Scene panel on the left), select an element and change it in the Inspector on the right, or move it in the scene tree. The colours and fonts are in `theme.tres`.

## Files

- `exports_data.gd`: reads the exports folder.
- `main.gd`: fills the page and reacts to clicks.
- `bar_chart.gd`: the chart, drawn by hand (Godot has no ready-made chart).
- `main.tscn`, `theme.tres`: layout and look.

The font is Bahnschrift, installed with Windows 10 and 11.
