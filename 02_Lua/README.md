# Lua export scripts

These scripts run inside the **FC 26 Live Editor** (F9 → Lua Engine) and export the four CSV files that The Club Office imports:

- season player stats
- season transfers
- team fixtures
- league standings

They only **read** the game. They use the Live Editor's own functions and nothing else.

## `tco_session.lua` (recommended)

Run it **once per play session**, after loading your career:
F9 → Lua Engine → open `tco_session.lua` → Execute.

What it does:

- finds the club you manage and the current season by itself (nothing to edit between seasons);
- exports the four files right away, then again **before and after every match of your team**, and **once a week** as a safety net;
- keeps the stats of the players who leave the club during the season (see below);
- shows a message with the club, the season and the folder, so you can check them (and the script version: 1.4).

Running it again in the same session does not add a second listener: it just exports again, right away.

### Where the files go

```text
Documents\TheClubOffice\exports\
    tco_session_log.txt                          log of everything the script did
    AFC Wimbledon - 686228de\                    one folder per career (club - save id)
        2025-2026\                               one folder per season
            TEAM_<id>_SEASON_PLAYER_STATS_2025-2026.csv
            TEAM_<id>_SEASON_TRANSFERS_2025-2026.csv
            TEAM_<id>_FIXTURES_2025-2026.csv
            TEAM_<id>_LEAGUE_STANDINGS_2025-2026.csv
            tco_state_TEAM_<id>.txt              what was exported last
            previous\                            the 3 previous versions of each file
```

The career folder is named after the club and the start of the save identifier (Live Editor `GetSaveUID`), so two saves with the same club never share files. Accents and symbols in the club name become `_`. If the Live Editor has no save identifier, the club id is used instead.

A career or a season never writes into the folder of another one.

### When it exports

The script reacts to the game's career events. Their numbers were checked in the game with the full event log, because the Live Editor's two lists of event names (`enums.lua` and `consts.lua`) disagree with each other and with FC 26 in places:

| Event | When | Export |
|---|---|---|
| 37 | career menus, just before a match | yes |
| 15 | a day passes (the game passes a day by itself right after a match) | yes, the first one after a match |
| 16 | a week passes | yes, unless an export already ran that in-game day |
| 7 | end of the club's match (never seen with a simulated match) | yes, if it ever comes |

The log also notes a few events (save, simulation, season start and end, transfer windows) to check the end of a season.

### Season label

The season is computed from the in-game date. A new season starts in July (`SEASON_START_MONTH = 7`), like the Live Editor's default career date (1 July). For example, 14 March 2027 is in season `2026-2027`.

If the label is ever wrong, set `SEASON_LABEL_OVERRIDE` at the top of the script (for example `"2026-2027"`).

The label must be exactly the same as the season label in the app.

### Safety check

Inside a season, the numbers only go up. If they suddenly collapse while the date is still in the same season, the game has most likely reset the season. In that case the script writes **nothing** and the log says `export BLOCKED by the safety check`:

- played matches of the club dropped by more than half, or
- squad appearances dropped to zero.

A small drop (for example after reloading an older save) is allowed.

A new career is a new save, so it gets its own folder.

### Settings (top of the script)

| Setting | Default | Meaning |
|---|---|---|
| `SEASON_LABEL_OVERRIDE` | `nil` | force the season label |
| `SEASON_START_MONTH` | `7` | first month of a season |
| `EXPORT_ROOT_OVERRIDE` | `nil` | use another export folder |
| `BACKUP_COUNT` | `3` | previous versions kept per file |
| `LOG_ALL_EVENTS` | `false` | diagnostic: `true` writes every game event to the log |

### Players who leave the club during the season

The game only lists a player with his current club. When a player leaves (sold, released, loaned out), the script reads its previous player stats file of the season and keeps his rows as they were in the last export before he left, with `left_club` = `true` (the last column of the file; `false` for the current squad). As the script exports after every match, these rows hold his whole season with the club.

- If he comes back to the club during the season, only his new rows are kept.
- A new season starts with an empty folder: the players who left are not carried into it.
- The safety check only counts the current squad, so a season reset by the game is still detected.

### Known limits

- The matches played while the script was not running are not exported until the next export. For a player who leaves the club before that, they are missing.
- The manual script `01_` has no `left_club` column: the app reads its files as the current squad.

## Manual scripts `01_` to `04_`

The original scripts, kept as a fallback. Each one exports one file.

Before running them, edit `SEASON_LABEL` and `CAREER_TEAM_ID` at the top of each file. They write to the Desktop.
