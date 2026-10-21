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
- exports the four files right away, then again **before every match of your team** (and after the match when the game sends its end-of-match events);
- shows a message with the club, the season and the folder, so you can check them.

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
| `LOG_ALL_EVENTS` | `true` | diagnostic: write every game event to the log (set to `false` once the tests are done) |

### Known limits

- A player who left the club during the season is no longer in the squad export (same as the manual script).

## Manual scripts `01_` to `04_`

The original scripts, kept as a fallback. Each one exports one file.

Before running them, edit `SEASON_LABEL` and `CAREER_TEAM_ID` at the top of each file. They write to the Desktop.
