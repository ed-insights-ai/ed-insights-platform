# Bead 10: Player Profile Page

**Date:** 2026-03-16
**Route:** `/explore/players/[school]/[name]`
**Reference:** DESIGN.md §4.x Player Profile, Explore Players leaderboard

## Overview

A "Trading Card" style deep-dive for an individual player. Shows career stats across
all seasons, KPI cards vs conference average, a radar chart vs conference peers, and
a game log for the selected season. Reachable from: player leaderboard, War Room top
contributors, roster table.

## URL Structure

No numeric player ID exists in the DB. Identity is `(school_abbreviation, player_name)`.

Route: `/explore/players/[school]/[name]`
- `school` = abbreviation (e.g. `HU`)
- `name` = URL-encoded player name (e.g. `Christian%20Ramos`)

Example: `/explore/players/HU/Christian%20Ramos`

Season selector on the page (default: most recent season with data).

## API Endpoints to Build

### 1. `GET /api/players/profile`

```
Query params:
  school: str (abbreviation, required)
  name: str (player name, required)
  season: int (optional, defaults to most recent season with data)

Response:
{
  "player_name": "Christian Ramos",
  "school_abbreviation": "HU",
  "school_name": "Harding",
  "gender": "men",

  // Career summary (all seasons combined)
  "career": {
    "seasons": 4,
    "games_played": 129,
    "goals": 57,
    "assists": 15,
    "shots": 435,
    "shots_on_goal": 179
  },

  // Per-season breakdown
  "seasons": [
    {
      "season_year": 2019,
      "games_played": 31,
      "goals": 29,
      "assists": 1,
      "shots": 127,
      "shots_on_goal": 77,
      "goals_per_90": 1.23,       // goals / (minutes/90) — if minutes=0, use games*90
      "shot_conversion": 22.8,    // goals/shots * 100
      "sog_accuracy": 60.6        // sog/shots * 100
    },
    ...
  ],

  // Current/selected season game log
  "game_log": [
    {
      "game_id": 123,
      "date": "2019-09-14",
      "opponent": "Oklahoma Baptist",
      "home_away": "H",
      "result": "W",
      "score": "3-1",
      "goals": 2,
      "assists": 0,
      "shots": 5,
      "shots_on_goal": 3,
      "minutes": 90,
      "is_starter": true
    },
    ...
  ],

  // Conference averages for selected season (same gender, same conf)
  "conf_averages": {
    "season_year": 2024,
    "goals_per_game": 0.38,
    "shot_conversion": 12.4,
    "sog_accuracy": 48.2,
    "assists_per_game": 0.19,
    "shots_per_game": 2.1
  },

  // Radar data: player vs conf average (percentile 0-100 among all players that season)
  "radar": {
    "goals_pct": 94,
    "assists_pct": 71,
    "shots_pct": 88,
    "sog_pct": 85,
    "shot_conversion_pct": 76
  }
}
```

**Implementation notes:**
- Query `player_game_stats` joined to `games` and `schools`
- Filter by `player_name` (exact match) + `school_id`
- Conference averages: aggregate all players in same gender+conference+season,
  divide totals by games_played to get per-game rates
- Radar percentiles: for each metric, rank this player among all players with
  `games_played >= 3` in that season, compute percentile (0-100)
- `goals_per_90`: if `total_minutes = 0` for all games, fall back to `goals / games_played`
  (StatCrew doesn't always populate minutes for outfield players)

### 2. Add route to `apps/api/src/main.py`

Register new router: `from src.routers import players` + `app.include_router(players.router)`

Create `apps/api/src/routers/players.py` with the profile endpoint.

### 3. Update `apps/web/src/lib/api.ts`

Add `PlayerProfile` type and `getPlayerProfile(school, name, season?)` function.

## Frontend: `/explore/players/[school]/[name]/page.tsx`

### Layout

```
← Back to Players

┌──────────────────────────────────────────────────────────┐
│  IDENTITY HEADER                                          │
│  Christian Ramos  •  Harding Bisons  •  Forward           │
│  Career: 4 seasons  •  57G  15A  •  435 shots            │
│                           [Season: 2019 ▼]               │
└──────────────────────────────────────────────────────────┘

┌────────────┬────────────┬────────────┬────────────┐
│ GOALS/GAME │ SHOT CONV  │ SOG ACC    │ ASSISTS/G  │
│   0.94     │  22.8%     │  60.6%     │  0.03      │
│  +0.56 ▲  │  +10.4% ▲  │  +12.4% ▲  │  -0.16 ▼  │
│ vs conf avg│ vs conf avg│ vs conf avg│ vs conf avg│
└────────────┴────────────┴────────────┴────────────┘

┌─────────────────────────┬────────────────────────────────┐
│  RADAR CHART            │  CAREER STATS BY SEASON        │
│  (pentagon/spider)      │  Season | GP | G | A | Sh | SOG│
│  Goals / Assists /      │  2019   | 31 |29 | 1 |127 | 77 │
│  Shots / SOG /          │  2018   | 34 |14 | 8 |122 | 42 │
│  Shot Conv              │  2017   | 29 |10 | 5 | 89 | 32 │
│                         │  2016   | 35 | 4 | 1 | 97 | 28 │
│  Player — teal          │                                │
│  Conf Avg — dashed grey │                                │
└─────────────────────────┴────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  GAME LOG — 2019 Season                                   │
│  Date     │ Opponent       │ H/A │ Result │ G  A  Sh SOG │
│  Nov 2    │ Ouachita Bapt  │  H  │ W 3-1  │ 2  0   5   3 │
│  Oct 26   │ Rogers State   │  A  │ L 0-2  │ 0  0   2   1 │
│  ...                                                     │
└──────────────────────────────────────────────────────────┘
```

### Component Details

**Identity Header:**
- Player name in `text-2xl font-bold`
- School name + mascot, gender badge (teal=men, purple=women)
- Career summary line: `X seasons • YG ZA`
- Season selector dropdown (shows years with data, default = most recent)

**KPI Cards:**
- Use existing `ContextualMetricCard` component
- 4 cards: Goals/Game, Shot Conversion %, SOG Accuracy %, Assists/Game
- Delta vs conference average for selected season

**Radar Chart:**
- Use `recharts` `RadarChart` with `PolarGrid`, `PolarAngleAxis`, `Radar`
- 5 axes: Goals, Assists, Shots, Shot Conversion, SOG Accuracy
- Two series: player (teal fill, 0.3 opacity) + conf average (grey dashed, no fill)
- Values are **percentile ranks** (0-100) so all axes are comparable
- Label each axis with both the percentile and the raw value in tooltip

**Career Stats Table:**
- One row per season, newest first
- Columns: Season, GP, G, A, Sh, SOG, G/90, Conv%
- Click season row → updates season selector (and game log + KPIs)
- Highlight current selected season row

**Game Log:**
- Filtered to selected season
- Sorted by date descending
- Result badge (W/L/D colored) + score
- `game_id` links to `/dashboard/games/[id]`
- Starter indicated with small dot or `(S)` suffix

### Navigation wiring

Update these existing pages to link to player profile:
1. **`/explore/players/page.tsx`** — player name in leaderboard table → `/explore/players/[school]/[encoded_name]`
2. **`/dashboard/page.tsx`** (War Room top contributors) — player name → profile link
3. **`/dashboard/players/page.tsx`** (roster) — player name → profile link

## Out of Scope

- Player photos (no data source)
- Position-specific stats (GK save%, etc.) — future
- Player comparison tool — future bead
- Edit/claim player profile — future (auth feature)
- Pagination on game log (all games in a season is max ~35, acceptable)

## Data Constraints & Known Issues

- `total_minutes = 0` for most StatCrew (Harding) players — use games_played as proxy
  for per-90 calculations: `goals / games_played` instead of `goals / (minutes/90)`
- Player names are not normalized — "Shajani, Unaiz" (last, first format) exists in data
  alongside normal first-last format. Display as-is, no transformation needed.
- Same player name across different schools is treated as different players (correct behavior)
- If a player appears in only 1 game they still get a profile, radar chart will show limited data

## Acceptance Criteria

- [ ] `GET /api/players/profile?school=HU&name=Christian%20Ramos` returns valid profile
- [ ] `/explore/players/HU/Christian%20Ramos` renders without errors
- [ ] KPI cards show delta vs conference average
- [ ] Radar chart renders with 5 axes, player + conf avg series
- [ ] Career table shows all seasons with data
- [ ] Game log shows all games for selected season
- [ ] Season selector updates KPIs, game log
- [ ] Player names in leaderboard, War Room, and roster link to profile
- [ ] Back link goes to `/explore/players`
- [ ] `uv run pytest tests/ -v` passes (add at least 1 test for the new endpoint)

## Validation Commands

```bash
# API
curl "http://localhost:8000/api/players/profile?school=HU&name=Christian%20Ramos&season=2019"

# Tests
cd packages/pipeline && uv run pytest tests/ -v
cd apps/api && uv run pytest tests/ -v

# Lint
cd apps/api && uv run ruff check src/
cd apps/web && npm run lint
```

## Execution

```bash
cd ~/source/ed-insights-platform
claude --dangerously-skip-permissions "Implement docs/specs/ui-bead10-player-profile.md"
```
