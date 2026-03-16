# Bead 11: Team Profile + Explore Teams Browser

**Date:** 2026-03-16
**Routes:** `/explore/teams` + `/explore/teams/[abbr]`
**Reference:** DESIGN.md §4.7 All Teams, ADR-007 (GAC membership)

## Overview

Two pages:
1. **`/explore/teams`** — Browse all GAC schools. Grid of team cards, filtered by
   gender (uses global GenderContext). Each card shows school name, record, form badges.
   Click → Team Profile.

2. **`/explore/teams/[abbr]`** — Deep-dive on a single school. Season record, KPI cards
   vs conference average, GF/GA trend chart, top scorers, recent results.
   This is the "scouting report" page — answers "who is this team?"

This completes the L1→L2 navigation: Conference Overview → Team Profile → Player Profile.

## API Endpoints to Build

### 1. `GET /api/teams/[abbr]/profile`

```
Path param: abbr (school abbreviation, e.g. FHSU)
Query params:
  season: int (optional, defaults to most recent season with data)

Response:
{
  "abbreviation": "FHSU",
  "name": "Fort Hays State",
  "mascot": "Tigers",
  "gender": "men",
  "conference": "GAC",

  // Selected season record
  "season": {
    "year": 2024,
    "games_played": 21,
    "wins": 13,
    "losses": 4,
    "draws": 4,
    "goals_for": 59,
    "goals_against": 26,
    "goal_diff": 33,
    "points": 43,
    "ppg": 2.05,
    "form": [
      { "result": "W", "game_id": 2202417 },
      ...
    ],                    // last 5 results
    "conf_rank": 1        // position in GAC standings this season
  },

  // KPI vs conference average
  "kpis": {
    "goals_per_game": 2.81,
    "goals_per_game_delta": 1.41,     // vs conf avg
    "shot_conversion": 14.4,
    "shot_conversion_delta": 3.2,
    "goals_against_per_game": 1.24,
    "goals_against_per_game_delta": -0.8,   // negative = better defense
    "clean_sheets": 7,
    "conf_avg_goals_per_game": 1.40,
    "conf_avg_shot_conversion": 11.2,
    "conf_avg_goals_against_per_game": 2.04
  },

  // GF vs GA per game for trend chart
  "results_by_game": [
    {
      "game_id": 2202401,
      "date": "2024-08-24",
      "opponent": "Colorado Mesa",
      "home_away": "H",
      "home_score": 3,
      "away_score": 0,
      "goals_for": 3,
      "goals_against": 0,
      "result": "W"
    },
    ...
  ],

  // Top 5 scorers this season
  "top_scorers": [
    {
      "player_name": "Alex Doe",
      "goals": 12,
      "assists": 4,
      "games_played": 21,
      "goals_per_game": 0.57
    },
    ...
  ],

  // Available seasons (for selector)
  "available_seasons": [2024, 2023, 2022, 2021, 2020, 2019]
}
```

**Implementation notes:**
- Reuse the existing standings query pattern from `conferences.py` for record + form
- Conference averages: query all schools in same gender+conference+season
- Top scorers: query `player_game_stats` joined to `games` for this school+season,
  group by player_name, sum goals/assists, order by goals desc, limit 5
- `conf_rank`: count schools with more points in same gender+conference+season + 1
- `available_seasons`: distinct season_years with games for this school

Create `apps/api/src/routers/teams.py` and register in `main.py`.

### 2. Update `apps/web/src/lib/api.ts`

Add `TeamProfile` type and `getTeamProfile(abbr, season?)` function.

Also add `getSchools(gender?)` if not already filtering by gender — needed for the
teams browser to only show men's or women's schools based on GenderContext.

## Frontend

### Page 1: `/explore/teams/page.tsx` — Teams Browser

Replaces the "Coming soon" stub.

**Layout:**
```
ALL TEAMS  [Men ● / Women ○]  (global gender switch already in sidebar)

┌────────────┐ ┌────────────┐ ┌────────────┐
│ Fort Hays  │ │ Rogers     │ │ Newman     │
│ State      │ │ State      │ │            │
│ Tigers     │ │ Hillcats   │ │ Jets       │
│            │ │            │ │            │
│ 13W-4L-4D  │ │ 9W-7L-2D  │ │ 4W-9L-4D  │
│ W W W D L  │ │ W L W W D  │ │ L D W L L  │
│            │ │            │ │            │
│ #1 in GAC  │ │ #2 in GAC  │ │ #3 in GAC  │
└────────────┘ └────────────┘ └────────────┘
```

- Responsive grid: 3 cols desktop, 2 cols tablet, 1 col mobile
- Each card: school name, mascot, season record, form strip (last 5), conference rank
- Gender-aware: reads `GenderContext`, shows men's or women's schools accordingly
- Default season: 2024
- Cards are clickable → `/explore/teams/[abbr]`
- Data: use existing `GET /api/conferences/GAC/standings?season=2024&gender=men`
  (already returns everything needed for the cards)

### Page 2: `/explore/teams/[abbr]/page.tsx` — Team Profile

Replaces the "Coming soon" stub.

**Layout:**
```
← Back to Teams

┌──────────────────────────────────────────────────────────┐
│ IDENTITY HEADER                                           │
│ Fort Hays State Tigers  •  GAC Men's Soccer               │
│ #1 in GAC  •  [Season: 2024 ▼]                           │
└──────────────────────────────────────────────────────────┘

[W] [W] [W] [D] [L]   ← FormBadgeStrip (last 5, clickable)

┌────────────┬────────────┬────────────┬────────────┐
│ GOALS/GAME │ SHOT CONV  │ GA/GAME    │ CLEAN SHEET│
│   2.81     │  14.4%     │  1.24      │  7         │
│  +1.41 ▲  │  +3.2% ▲   │  -0.80 ▲  │            │
│ vs conf avg│ vs conf avg│ vs conf avg│            │
└────────────┴────────────┴────────────┴────────────┘

┌──────────────────────────┬─────────────────────────────┐
│ GF vs GA TREND           │ TOP SCORERS                 │
│ (Line chart, per game)   │ Alex Doe       12G 4A       │
│ Teal = GF                │ ████████████░░░░░           │
│ Orange = GA              │ Maria Smith     8G 2A       │
│                          │ █████████░░░░░░░            │
│                          │ ...                         │
└──────────────────────────┴─────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│ RESULTS  (2024 season, all games)                        │
│ Date     │ Opponent       │ H/A │ W/L/D │ Score         │
│ Nov 9    │ Ouachita Bapt  │  A  │  W    │ 4-1           │
│ ...                                                      │
└──────────────────────────────────────────────────────────┘
```

**Component details:**

- **Identity header:** School name + mascot, conference + gender badge (teal/purple),
  conf rank badge, season selector
- **Form strip:** Reuse `FormBadgeStrip` component, each badge links to game detail
- **KPI cards:** Reuse `ContextualMetricCard`, 4 cards:
  - Goals/Game (delta vs conf avg — higher is better)
  - Shot Conversion % (delta vs conf avg)
  - Goals Against/Game (delta vs conf avg — lower is better, so invert delta color)
  - Clean Sheets (raw count, no delta)
- **Trend chart:** Recharts LineChart, one point per game, teal=GF orange=GA,
  x-axis = game number (1, 2, 3...), tooltip shows date + opponent + score
- **Top Scorers:** 5 rows, horizontal progress bar scaled to top scorer,
  player name links to `/explore/players/[abbr]/[encoded_name]`
- **Results table:** All games this season sorted by date desc,
  result badge (W/L/D), score, game_id links to `/dashboard/games/[id]`

### Navigation wiring

1. **Conference Overview** (`/conference/[abbr]/page.tsx`) — school name in standings
   table → `/explore/teams/[abbr]`
2. **Sidebar nav** — "Explore > Teams" link already exists, now points to real page
3. **Team Profile** → player name in top scorers → `/explore/players/[abbr]/[name]`

## Out of Scope

- Multi-season comparison chart (future analytics bead)
- Head-to-head vs specific opponent (future compare bead)
- Team photo/logo (no asset pipeline yet)
- Non-GAC teams (opponents that aren't in our DB)

## Acceptance Criteria

- [ ] `GET /api/teams/FHSU/profile?season=2024` returns valid data
- [ ] `/explore/teams` shows all 7 men's (or women's) schools as cards with records
- [ ] Gender switch updates teams browser to show correct gender
- [ ] `/explore/teams/FHSU` renders with record, KPIs, trend chart, top scorers, results
- [ ] Season selector on team profile updates all sections
- [ ] FormBadgeStrip on team profile links to game detail pages
- [ ] Standings table on conference page links to team profiles
- [ ] Top scorer names link to player profiles
- [ ] API tests pass: `cd apps/api && uv run pytest tests/ -v`
- [ ] No lint errors: `cd apps/web && npm run lint`

## Validation Commands

```bash
curl "http://localhost:8000/api/teams/FHSU/profile?season=2024"
curl "http://localhost:8000/api/teams/HUW/profile?season=2024"
cd apps/api && uv run pytest tests/ -v
cd apps/web && npm run lint
```

## Execution

```bash
cd ~/source/ed-insights-platform
claude --dangerously-skip-permissions "Implement docs/specs/ui-bead11-team-profile.md"
```
