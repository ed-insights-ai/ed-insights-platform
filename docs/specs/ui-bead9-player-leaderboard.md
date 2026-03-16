# Bead 9: Cross-School Player Leaderboard

## Overview
Build `/explore/players` — a cross-school player leaderboard using the existing
`/api/stats/players` endpoint (no school filter = all schools). Sortable table,
position filter, minimum games threshold.

## Files to Modify
- `apps/web/src/app/explore/players/page.tsx` — full rebuild (currently "Coming soon" stub)

## Reference
- `docs/DESIGN.md` section 4.8 for layout spec
- `apps/web/src/lib/api.ts` — `getPlayerLeaderboard()` already exists, accepts no `school` param

---

## Implementation

Client Component. Read `gender` from `GenderContext`.

### State
```typescript
const [players, setPlayers] = useState<PlayerLeaderboard[]>([])
const [loading, setLoading] = useState(true)
const [season, setSeason] = useState(2025)
const [sortKey, setSortKey] = useState<string>("goals")
const [minGames, setMinGames] = useState(5)
```

### Data fetching
```typescript
// No school param = all schools
getPlayerLeaderboard("", season, sortKey, 100, 0)
```

Note: `getPlayerLeaderboard` in api.ts passes `school` as a query param — passing empty string
should work, but verify. If it causes a 422, update the API call to omit the param entirely
when school is empty (check existing api.ts code).

Re-fetch when `season`, `sortKey`, or `gender` changes. Gender filtering happens server-side
via school's gender — the existing endpoint returns players from all schools regardless of gender.
For now, filter client-side: after fetching, filter `players` where `player.school_name` matches
schools of the correct gender. This is a TODO — ideal solution is adding `?gender=` param to
the players API endpoint, but skip that for this bead.

### Layout

```
Header: "Players" h2 + gender badge (teal "Men's" / purple "Women's")
Subhead: "GAC Conference · {season} Season"

Controls row (flex, space between):
  Left: Season selector <select> 2016–2025
  Right: Min games slider or select: "Min GP: [5▾]" (options: 1, 3, 5, 8, 10)

bento-card with overflow-x-auto:
  stat-label: "PLAYER LEADERBOARD"
  Sortable table
```

### Table columns

| Column | Key | Notes |
|--------|-----|-------|
| Rank | 1-based | `text-slate-400 text-xs` |
| Player | player_name | plain text for now (no profile route) |
| School | school_name | `text-slate-500 text-sm` |
| GP | games_played | |
| G | total_goals | sortable, bold when sortKey=goals |
| A | total_assists | sortable |
| Pts | total_goals + total_assists | computed client-side |
| Shots | total_shots | |
| Conv% | total_goals/total_shots*100 | `tabular-nums`, format "14.2%" |
| G/90 | total_goals/total_minutes*90 | `tabular-nums`, format "0.34", show "–" if minutes=0 |

All numeric columns use `tabular-nums`. Headers are `table-header` class (uppercase tracked).

**Active sort column:** bold header + sort indicator ▲/▼
**Default sort:** goals DESC

### Sorting
Client-side sort on the fetched array. Click header toggles direction.
Sortable columns: G, A, Pts, Shots, Conv%, G/90, GP.

### Min games filter
Filter client-side: `players.filter(p => p.games_played >= minGames)`

### Loading / empty states
- Loading: centered spinner
- Empty: "No player data for this selection."

## Out of Scope
- No player profile links (no route yet)
- No cross-school gender filtering via API (client-side only for now)
- No position filter (no position data in current schema)

## Validation
```bash
cd apps/web && npm run lint && npm run build
```
Manually: navigate to /explore/players, see cross-school leaderboard, sort by goals, change min games.

## Commit
`feat(web): cross-school player leaderboard — sortable table with per-90 metrics`

## When done
```bash
openclaw system event --text "Done: Bead 9 player leaderboard — cross-school sortable table live" --mode now
```
