# Bead 12: Smart Insights Engine

**Date:** 2026-03-16
**Touches:** War Room dashboard (`/dashboard`)
**Reference:** DESIGN.md §4.1 Smart Insights

## Overview

Replace the "Insights coming soon" placeholder on the War Room with real, SQL-generated
narrative insights. These are rule-based template strings — NOT LLM-generated. Each
insight fires when a specific statistical condition is met. The card shows 2-4 insights
at a time, most interesting first.

This makes the platform feel intelligent without any AI cost.

## API Endpoint

### `GET /api/insights`

```
Query params:
  school: str (abbreviation, required)
  season: int (required)

Response:
{
  "insights": [
    {
      "type": "scoring_streak",
      "priority": 1,
      "icon": "🔥",
      "text": "Christian Ramos has scored in 3 consecutive games."
    },
    {
      "type": "conversion_vs_conf",
      "priority": 2,
      "icon": "📉",
      "text": "Shot conversion is 3.2% below conference average over the last 5 games."
    },
    {
      "type": "clean_sheet_home_away",
      "priority": 3,
      "icon": "🏠",
      "text": "Harding has kept 6 clean sheets at home but 0 on the road this season."
    }
  ]
}
```

Returns max 4 insights. Empty array if no conditions fire (don't return
placeholder text — just return nothing, the UI will handle it gracefully).

## Insight Rules (implement all of these)

Each rule queries the DB and fires only if its condition is met.
Priority determines display order (lower = shown first).

### 1. Scoring Streak (`scoring_streak`, priority 1)
**Condition:** A player scored in N≥3 consecutive games (most recent games).
**Template:** `"{player}" has scored in {N} consecutive games.`
**Query:** For each player, look at the last N games ordered by date. Check if
goals > 0 in each. Find the player with the longest current streak ≥ 3.

### 2. Shot Conversion Trend (`conversion_trend`, priority 2)
**Condition:** Team's shot conversion in last 5 games is ≥ 3% different from season avg.
**Template (down):** `Shot conversion has dropped {X}% over the last 5 games ({last5}% vs {season}% season avg).`
**Template (up):** `Shot conversion is up {X}% over the last 5 games ({last5}% vs {season}% season avg).`
**Query:** Compare (goals/shots)*100 for last 5 games vs whole season.

### 3. Unbeaten Run (`unbeaten_run`, priority 1)
**Condition:** Team is unbeaten in last N≥4 games (W or D).
**Template:** `{school} is unbeaten in their last {N} games ({record}).`
**Example:** "Fort Hays State is unbeaten in their last 6 games (4W 2D)."

### 4. Losing Streak (`losing_streak`, priority 1)
**Condition:** Team has lost N≥3 consecutive games.
**Template:** `{school} has lost {N} consecutive games.`

### 5. Clean Sheet Home/Away Split (`clean_sheet_split`, priority 3)
**Condition:** Clean sheets at home ≠ clean sheets away, and at least one is 0
and the other is ≥ 3.
**Template:** `{school} has kept {H} clean sheet(s) at home but {A} on the road.`
**Query:** Count games where team's goals_against = 0, split by home/away.

### 6. Top Scorer Pace (`top_scorer_pace`, priority 2)
**Condition:** Top scorer has goals_per_game ≥ 0.6 (roughly 1 goal every 1.5 games).
**Template:** `{player} is scoring at {X} goals per game — {N} goals in {GP} appearances.`

### 7. Conf vs Non-Conf performance (`conf_split`, priority 3)
**Condition:** Win rate in conference games differs from non-conference by ≥ 25%.
**Template (better conf):** `{school} performs significantly better in conference play ({conf_record} conf vs {nonconf_record} non-conf).`
**Template (better nonconf):** `{school} is struggling in conference play ({conf_record} conf vs {nonconf_record} non-conf).`
**Query:** Split games by `is_conference_game`, compute W/L/D for each.

### 8. Goal Drought (`goal_drought`, priority 1)
**Condition:** Team has failed to score in N≥3 consecutive games.
**Template:** `{school} has failed to score in {N} consecutive games.`

## Priority Logic

- Rules 1 (streaks/runs) take highest priority — most newsworthy
- Only return one "streak" insight (pick the most dramatic)
- Never return both `unbeaten_run` and `losing_streak` for the same team
- Cap at 4 insights total
- If fewer than 2 conditions fire, return what fires (don't pad with filler)

## Implementation

Create `apps/api/src/routers/insights.py`.
Register in `main.py`: `from src.routers import insights`, `app.include_router(insights.router)`.

Each rule is a separate async function returning `Insight | None`.
Run all rules concurrently with `asyncio.gather()`.
Sort by priority, deduplicate streak insights, take top 4.

**Key DB patterns needed:**

For game-by-game order, use:
```sql
SELECT g.game_id, g.date, pgs.goals, pgs.player_name
FROM player_game_stats pgs
JOIN games g ON g.game_id = pgs.game_id
WHERE g.school_id = :school_id AND g.season_year = :season
  AND g.home_score IS NOT NULL
ORDER BY g.date DESC
```

For home/away split, use `games.home_team ILIKE '%{school_name}%'` to determine
if the school was home.

For conference split, use `games.is_conference_game`.

## Frontend

In `apps/web/src/app/dashboard/page.tsx`:

Replace the placeholder Smart Insights card:
```tsx
// BEFORE (placeholder):
<div className="lg:col-span-1 bento-card p-5 bg-teal-50 border-teal-200">
  <p className="stat-label">SMART INSIGHTS</p>
  <p className="text-sm text-teal-700 mt-2">
    Insights powered by real data coming soon...
  </p>
</div>

// AFTER (real):
<SmartInsightsCard schoolId={selectedSchoolId} season={selectedSeason} />
```

Create `apps/web/src/components/stats/SmartInsightsCard.tsx`:
- Fetches `GET /api/insights?school=X&season=Y`
- Shows each insight as a row: `{icon}  {text}`
- Teal card background (`bg-teal-50 border-teal-200`) — already styled
- Loading: skeleton lines
- Empty state: "No notable trends this season." in muted text
- No scroll — max 4 items, each ≤ 1 line of text

Add `getInsights(school, season)` to `apps/web/src/lib/api.ts`.

## Out of Scope

- LLM-generated insights (future)
- Push notifications for insights (future)
- Insights on Team Profile page (future — same engine, different trigger)

## Acceptance Criteria

- [ ] `GET /api/insights?school=HU&season=2024` returns ≥1 real insight
- [ ] `GET /api/insights?school=FHSU&season=2024` returns ≥1 real insight
- [ ] War Room Smart Insights card shows real text, not placeholder
- [ ] Empty state renders gracefully when no insights fire
- [ ] All 8 rules implemented, each tested independently
- [ ] API tests: `cd apps/api && uv run pytest tests/ -v`

## Validation

```bash
curl "http://localhost:8000/api/insights?school=HU&season=2024"
curl "http://localhost:8000/api/insights?school=FHSU&season=2024"
curl "http://localhost:8000/api/insights?school=OBU&season=2019"
cd apps/api && uv run pytest tests/ -v
```

## Execution

```bash
cd ~/source/ed-insights-platform
claude --dangerously-skip-permissions "Implement docs/specs/ui-bead12-smart-insights.md"
```
