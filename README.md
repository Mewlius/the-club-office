# The Club Office

The Club Office is a local Streamlit companion app for FC 26 career mode.

The app helps manage and review a football career save with local data, CSV imports, season dashboards, player statistics, fixtures, standings and transfers.

## Current status

This repository contains the first stable technical prototype of the app.

Current features:

- create or open a career
- add seasons to a career
- import CSV files exported from FC 26 / Lua scripts
- view a season dashboard
- view player statistics
- view fixtures
- view league standings
- view transfers

## App location

The main app is located in:

```text
03_App/
```

Main files:

```text
03_App/app.py
03_App/launch_app.bat
```

## How to launch the app

Open the folder:

```text
03_App/
```

Then double-click:

```text
launch_app.bat
```

This starts the Streamlit app in the browser.

## Lua export scripts

The CSV files come from Lua scripts run in the FC 26 Live Editor. They are in:

```text
02_Lua/
```

`tco_session.lua` exports the files automatically after every match. See `02_Lua/README.md`.

## Local data

The app stores local data in:

```text
03_App/data/
```

This folder is intentionally ignored by Git and must not be committed to GitHub.

The ignored local data includes career data, season data and imported CSV data converted to JSON.

## Files not committed to GitHub

These files and folders must stay local:

```text
03_App/data/
03_App/backups/
.venv/
*.csv
__pycache__/
*.pyc
.env
```

## Basic workflow

```text
1. Pull latest changes
2. Work locally
3. Test the app
4. Commit when stable
5. Push to GitHub
```

For now:

- no branches unless needed
- no direct code editing from GitHub web
- no local data committed
- one feature or fix at a time
- test after each meaningful change

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

The current app already includes career and season concepts through `career_id` and `season_id`.

CSV imports are attached to a selected career and season. The analysis pages use the selected season to display the relevant dashboard, player stats, fixtures, standings and transfers.

The next development steps should focus on stabilising the app, improving the import workflow, fiabilising multi-season usage and progressively refactoring `app.py`.
