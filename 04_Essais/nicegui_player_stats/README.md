# Trial: Player stats page with NiceGUI

A trial to compare interface tools. It does not change the app in `03_App`.

## Launch (Windows)

Double-click `lancer_essai.bat`.

The first time, it installs NiceGUI in a `.venv` folder next to it (internet needed, one or two minutes). Then the page opens in the browser.

## What it shows

The same information as the app's Player Stats page, read directly from the files written by `02_Lua/tco_session.lua`:

```text
Documents\TheClubOffice\exports\<club> - <save id>\<season>\
```

No import and no team id to type: the career and the season are picked from the header.

- all competitions or one competition;
- filters: position, squad role, nationality, minimum appearances, search;
- squad summary;
- table sorted by clicking a column title (position sorts goalkeepers, defence, midfield, attack);
- right panel: top goal contributions, or the sheet of the player clicked in the table or in the chart.

`Reload files` reads the folder again after a new export.

## Files

- `exports_data.py`: reads the exports folder. Independent of the interface tool, reusable by the app.
- `main.py`: the page.

The font is Bahnschrift, installed with Windows 10 and 11.
