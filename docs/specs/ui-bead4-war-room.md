# Bead 4: War Room Dashboard Rebuild

## Overview
Rebuild the main dashboard page (`/dashboard`) to match the War Room design from DESIGN.md section 4.1. Replace the flat stat cards and generic layout with the bento grid, ContextualMetricCard, FormBadgeStrip, and real computed metrics.

## Prerequisites
Beads 1, 2, and 3 must be merged first.

## What Changes

### API — Add Derived Metrics Endpoint
Add `GET /api/stats/derived/team` to `apps/api/src/routers/stats.py`.

Query params: `school` (abbreviation), `season` (year), `conference` (default "GAC").

Response schema (add to `apps/api/src/schemas.py`):
```python
class DerivedTeamStats(BaseModel):
    school_id: int
    school_name: str
    season_year: int
    games_played: int
    record_w: int
    record_l: int
    record_d: int
    goals_for: int
    goals_against: int
    goals_per_game: float          # total_goals / games_played
    goals_against_per_game: float
    shot_conversion_pct: float     # goals / shots * 100 (0 if no shots)
    sog_accuracy_pct: float        # sog / shots * 100 (0 if no shots)
    clean_sheets: int              # games where goals_against = 0
    clean_sheet_pct: float         # clean_sheets / games_played * 100
    total_shots: int
    total_sog: int
    # Conference averages for delta calculation:
    conf_avg_goals_per_game: float
    conf_avg_shot_conversion_pct: float
    conf_avg_sog_accuracy_pct: float
    conf_avg_clean_sheet_pct: float
```

Implementation notes:
- Join games → team_game_stats WHERE is_home matches the school
- For conference averages: aggregate across all schools in the same conference+season. Since the `schools` table may not have a `conference` column yet, use a hardcoded list of school abbreviations for "GAC": `["HU", "FHSU", "NU", "NSU", "OBU", "RSU", "SNU", "HUW", "ECU", "NWOSU", "OKBU", "OBUW", "SNUW", "SWOSU"]`. The conference avg calculation should be the mean across these schools for the given season.
- W/L/D record: join games and compare team_game_stats.goals for is_home vs !is_home rows within same game_id
- If a school has no data for the season, return HTTP 404

Add the route to `apps/api/src/main.py` router registration.

Add `GET /api/stats/form` to return the last N games as a form strip:
Query params: `school` (abbreviation), `season` (year), `limit` (default 5)
Response:
```python
class FormGame(BaseModel):
    game_id: int
    date: str | None
    result: Literal["W", "L", "D"]
    score_for: int
    score_against: int
    opponent: str

class FormResponse(BaseModel):
    items: list[FormGame]
```

### Frontend — `apps/web/src/lib/api.ts`
Add two new fetch functions:
```typescript
getDerivedTeamStats(school: string, season: number): Promise<DerivedTeamStats>
getFormStrip(school: string, season: number, limit?: number): Promise<FormGame[]>
```

Add corresponding TypeScript interfaces for `DerivedTeamStats` and `FormGame`.

### Frontend — `apps/web/src/app/dashboard/page.tsx`
Full rebuild. Replace current implementation with the War Room bento grid.

**Layout (DESIGN.md section 4.1):**

```
Row 1 (2 columns):
  Left (col-span-7): Season Record & Form card
  Right (col-span-5): Smart Insights placeholder card

Row 2 (2 columns):
  Left (col-span-7):
    4 ContextualMetricCards in a 2x2 grid:
      - Goals/Game (delta vs conf avg)
      - Shot Conversion % (delta vs conf avg)
      - Clean Sheet % (delta vs conf avg)
      - SOG Accuracy % (delta vs conf avg)
  Right (col-span-5): Next Match placeholder card (static — "Coming soon")

Row 3 (2 columns):
  Left (col-span-7): Season Trend mini-chart (GF vs GA per game using Recharts LineChart)
  Right (col-span-5): Top Contributors mini-leaderboard
```

All outer cards use `bento-card` class from Bead 1. Gap between cards: `gap-4`.

**Season Record & Form card:**
- Large W-L-D record: `{record.w}W – {record.l}L – {record.d}D` in `stat-value` class
- Sub-label: "SEASON RECORD" in `stat-label`
- School name + season as header
- `FormBadgeStrip` component below — pass last 5 games (from `getFormStrip` response)
- FormBadgeStrip with `gameId` so badges are clickable links

**Smart Insights placeholder:**
- Show a `bg-teal-50 border border-teal-200 rounded-xl p-5` card
- Header: "SMART INSIGHTS" in `stat-label`  
- Body: 3 static example insight rows (italic, text-slate-600):
  - "📈 Scoring trend data loading..."
  - "🎯 Shot conversion analysis coming soon"
  - "🛡️ Defensive stats loading..."
- Add a small note: `text-xs text-slate-400 mt-3` — "Rule-based insights powered by SQL — coming in Phase 2"

**4 ContextualMetricCards:**
Use `ContextualMetricCard` from Bead 2. Pass:
- Goals/Game: `value={derivedStats.goals_per_game.toFixed(2)}`, `delta={derivedStats.goals_per_game - derivedStats.conf_avg_goals_per_game}`, `baseline="vs Conference Avg"`
- Shot Conv%: `value={derivedStats.shot_conversion_pct.toFixed(1) + "%"}`, `delta={derivedStats.shot_conversion_pct - derivedStats.conf_avg_shot_conversion_pct}`, `deltaUnit="%"`
- Clean Sheet%: `value={derivedStats.clean_sheet_pct.toFixed(1) + "%"}`, `delta={derivedStats.clean_sheet_pct - derivedStats.conf_avg_clean_sheet_pct}`, `deltaUnit="%"`
- SOG Accuracy: `value={derivedStats.sog_accuracy_pct.toFixed(1) + "%"}`, `delta={derivedStats.sog_accuracy_pct - derivedStats.conf_avg_sog_accuracy_pct}`, `deltaUnit="%"`

**Season Trend chart:**
Use Recharts `<LineChart>` with 2 lines:
- Goals For: stroke `#0D9488` (data-primary teal), name "Goals For"
- Goals Against: stroke `#F97316` (data-opponent orange), name "Goals Against"
- X axis: game date or "G1, G2..." labels
- Y axis: integer 0-N
- Legend: show it
- No CartesianGrid needed (cleaner look for a small card)
- Responsive container, height 180px

Data: sorted games from existing `allGames` state, compute per-game GF/GA using `is_home` from game data.

**Top Contributors:**
Keep similar to current implementation but use `bento-card` styling and add:
- Progress bar behind each player row: use a `div` with `bg-data-primary/20` background and `bg-data-primary` fill, width = `(player.total_goals / maxGoals * 100)%`
- Show: rank number, player name, G + A counts
- Player name is a link to `/explore/players/{player.player_name}` (slug it: lowercase, replace spaces with hyphens) — stub route OK

**Loading state:**
When loading, show skeleton cards (use `animate-pulse bg-slate-100 rounded-xl h-32` divs) in the same grid positions — not a centered spinner.

**School selector:**
Keep `SchoolSeasonSelector` at the top of the page. Position it in the top-right of the page header row.

## Out of Scope
- No auth changes
- No real Smart Insights SQL engine (static placeholder only)  
- No Next Match Scouting card real data (placeholder card only)
- Don't touch other dashboard pages (games, players, analytics, etc.)

## Validation

### API tests
```bash
cd apps/api && uv run pytest -v
# All existing tests pass
# curl http://localhost:8000/api/stats/derived/team?school=HU&season=2024
# Should return JSON with goals_per_game, conf_avg_goals_per_game, etc.
# curl http://localhost:8000/api/stats/form?school=HU&season=2024&limit=5
# Should return last 5 games with W/L/D results
```

### Frontend
```bash
cd apps/web && npm run lint   # no errors
cd apps/web && npm run build  # clean build
```

### Visual
- Dashboard loads with bento grid layout
- 4 ContextualMetricCards show values + delta badges (green/red arrows)
- FormBadgeStrip shows last 5 W/L/D results as colored squares
- Season trend shows two-line chart (teal + orange)
- Top contributors show progress bars

## Commits
`feat(api): add derived team stats + form strip endpoints`
`feat(web): rebuild War Room dashboard with bento grid, metric cards, form strip`

## When done
```bash
openclaw system event --text "Done: Bead 4 War Room — bento grid, ContextualMetricCards with deltas, FormBadgeStrip, season trend chart live" --mode now
```
