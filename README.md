# The Club Office

The Club Office is a local companion app for FC 26 career mode, built with Python and NiceGUI.

It keeps the memory of a career from one season to the next: the game erases the season stats, the app keeps them.

## How it works

1. In FC 26, `02_Lua/tco_session.lua` exports the career data to `Documents\TheClubOffice\exports` (before and after every match, and once a week).
2. The app copies these exports into its own data when it starts and when you click **Reload files**. Careers and seasons are found automatically: nothing to import, no team id to type.

## Current status

The app is being rebuilt with NiceGUI (milestone V1). Available now:

- careers and seasons found automatically from the exports;
- automatic copy, with a safety check: an export older than the app's copy is not copied (it can be used on purpose from the app);
- overview of the seasons of a career and of their files.

## How to launch the app

Double-click:

```text
03_App/launch_app.bat
```

The first time, it installs NiceGUI in `03_App/.venv` (internet needed). The app opens in the browser.

## App files

```text
03_App/
    launch_app.bat      start the app
    main.py             entry point
    settings.py         paths and constants
    sync.py             copy of the exports into the app's data
    store.py            reading of the app's data
    layout.py           header shared by every page
    theme.py            colours and fonts
    page_overview.py    Overview page
```

## Lua export scripts

The CSV files come from Lua scripts run in the FC 26 Live Editor. They are in:

```text
02_Lua/
```

`tco_session.lua` exports the files automatically before and after every match, and once a week. See `02_Lua/README.md`.

## Local data

The app keeps its copy of the exports in:

```text
03_App/data/careers/<club> - <save id>/<season>/
```

Each season folder keeps the 3 previous versions of each file in `previous/`.

This folder is intentionally ignored by Git and must not be committed to GitHub.

## Files not committed to GitHub

These files and folders must stay local:

```text
03_App/data/
03_App/backups/
.nicegui/
.venv/
*.csv
__pycache__/
*.pyc
.env
```

## Basic workflow

```text
1. Each change is made on its own branch, linked to an issue
2. A pull request is opened
3. The change is tested locally (GitHub Desktop: Pull, then launch_app.bat)
4. The pull request is merged with Squash and merge
```

## Roadmap

The GitHub milestones track the app roadmap:

```text
V0 - Technical Prototype
V1 - Usable App
V2 - Club Office Layer
V3 - Advanced Analytics
V4 - Multi-squad / Multi-save
V5 - Finance / Club Development
V6 - Scouting / Recruitment
V7 - Automation / IA
V8 - Export / Sharing
```

## Development notes

The app reads only the files written by `tco_session.lua`: there is no manual CSV import any more. The previous Streamlit app (`03_App/app.py`) was removed.

The next steps rebuild the pages one by one (player stats, dashboard, fixtures, standings, transfers), then career management and the visual identity per career.
