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
- Home: the season at a glance (league position, form, results and next matches, players of the season, squad, transfer window);
- Matches: fixtures and results by competition, with filters, record, home and away, biggest win and defeat;
- Standings: the league table (overall, home or away), with the club's position and the points gaps around it;
- Player stats: the squad by competition, with filters, chart and player sheet. The players who left the club during the season keep their stats (marked Left, filter Players: All, Current or Left);
- Transfers: the arrivals and departures of the season (all, summer or winter window), fees, net spend, biggest signing and sale;
- History: the career season by season, and the all-time records (players and club), for all competitions or one;
- Data files: the state of the copied files of each season;
- Careers (from Data files): rename a career, give it an identity (logo, banner, main and second colour), or delete the career of a save you no longer use (moved to `Documents\TheClubOffice\deleted`, nothing is erased).

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
    careers.py          rename and delete a career
    identity.py         logo, banner and colours of a career (theme.json)
    store.py            reading of the app's data
    layout.py           header shared by every page
    theme.py            colours and fonts
    football.py         positions, squad roles, feet
    season_stats.py     season calculations (Home, Matches, Standings, Transfers)
    career_stats.py     career calculations, every season together (History)
    page_home.py        Home page
    page_matches.py     Matches page
    page_standings.py   Standings page
    page_player_stats.py  Player stats page
    page_transfers.py   Transfers page
    page_history.py     History page
    page_data.py        Data files page
    page_careers.py     Careers page
```

## Lua export scripts

The CSV files come from Lua scripts run in the FC 26 Live Editor. They are in:

```text
02_Lua/
```

`tco_session.lua` exports the files automatically before and after every match, and once a week. Since version 1.4, it also keeps the stats of the players who leave the club during the season. See `02_Lua/README.md`.

## Local data

The app keeps its copy of the exports in:

```text
03_App/data/careers/<club> - <save id>/<season>/
```

Each season folder keeps the 3 previous versions of each file in `previous/`.

This folder is intentionally ignored by Git and must not be committed to GitHub.

A career deleted on the Careers page is not erased: its copy in the app, its export folder and its identity are moved together to `Documents\TheClubOffice\deleted\<club> - <save id> (deleted <date>)\`, with a `README.txt` that explains how to move them back.

## Career identity

On the Careers page, the button **Identity** gives a career a logo, a banner and two colours. Everything is optional: a career without them keeps the default look.

- **Logo** (PNG, JPG or WEBP): in the header and on Home.
- **Banner**: behind the header, darkened so that the text stays readable.
- **Main colour**: the header, and a very pale version for the page background.
- **Second colour**: the highlights (menu, your club's row, chosen buttons) and the big figures.

Any colour can be chosen (or a shortcut): the app adjusts it so that the text stays readable. The choices are kept in `03_App/assets/careers/<career>/theme.json`, with the images. This folder is never committed to GitHub.

The logo of the app itself can be put in `03_App/assets/app/logo.png`: it is shown for every career without a logo of its own.

## Files not committed to GitHub

These files and folders must stay local:

```text
03_App/data/
03_App/backups/
03_App/assets/careers/
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

The next steps: the closing checklist of V1 (#12).
