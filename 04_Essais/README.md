# Interface trials

The same page (Player stats) built with two different tools, to choose what comes after Streamlit. Nothing here changes the app in `03_App`.

| | `nicegui_player_stats` | `godot_player_stats` |
|---|---|---|
| Language | Python (like the current app) | GDScript (Godot's language) |
| Opens in | the browser | its own window |
| Launch | double-click `lancer_essai.bat` | open `project.godot` in Godot 4.7, press F5 |
| Tables, charts | ready-made | built by hand (chart drawn in code) |
| Changing the layout | in the code | with the mouse in the Godot editor, or in the code |

Both read the files written by `02_Lua/tco_session.lua` directly from `Documents\TheClubOffice\exports`: no import and no team id to type.
