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
- exports the four files right away, then again **after every match of your team**;
- shows a message with the club, the season and the folder, so you can check them.

Running it again in the same session does not add a second listener: it just exports again, right away.

### Where the files go

```text
Documents\TheClubOffice\exports\
    tco_session_log.txt                      log of everything the script did
    2026-2027\
        TEAM_<id>_SEASON_PLAYER_STATS_2026-2027.csv
        TEAM_<id>_SEASON_TRANSFERS_2026-2027.csv
        TEAM_<id>_FIXTURES_2026-2027.csv
        TEAM_<id>_LEAGUE_STANDINGS_2026-2027.csv
        tco_state_TEAM_<id>.txt              what was exported last
        previous\                            the 3 previous versions of each file
```

One folder per season: a season never writes into the folder of another season.

### Season label

The season is computed from the in-game date. A new season starts in July (`SEASON_START_MONTH = 7`), like the Live Editor's default career date (1 July). For example, 14 March 2027 is in season `2026-2027`.

If the label is ever wrong, set `SEASON_LABEL_OVERRIDE` at the top of the script (for example `"2026-2027"`).

The label must be exactly the same as the season label in the app.

### Safety check

Inside a season, the numbers only go up. If they suddenly collapse while the date is still in the same season, the game has most likely reset the season. In that case the script writes **nothing** and the log says `export BLOCKED by the safety check`:

- played matches of the club dropped by more than half, or
- squad appearances dropped to zero.

A small drop (for example after reloading an older save) is allowed.

If you restart a new career with the same club and the same season, rename the old season folder first, otherwise the safety check will protect the old files.

### Settings (top of the script)

| Setting | Default | Meaning |
|---|---|---|
| `SEASON_LABEL_OVERRIDE` | `nil` | force the season label |
| `SEASON_START_MONTH` | `7` | first month of a season |
| `EXPORT_ROOT_OVERRIDE` | `nil` | use another export folder |
| `BACKUP_COUNT` | `3` | previous versions kept per file |

### Known limits

- Two careers with the same club and the same season write to the same files.
- A player who left the club during the season is no longer in the squad export (same as the manual script).

## Manual scripts `01_` to `04_`

The original scripts, kept as a fallback. Each one exports one file.

Before running them, edit `SEASON_LABEL` and `CAREER_TEAM_ID` at the top of each file. They write to the Desktop.
