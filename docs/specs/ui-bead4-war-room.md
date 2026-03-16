# Bead 4: War Room Dashboard Rebuild

## Overview
Rebuild `apps/web/src/app/dashboard/page.tsx` into the DESIGN.md "War Room" layout. Replace the current generic dashboard with a bento grid showing real computed metrics, form badges, season trend chart, and top contributors. Use the Bead 2 component library throughout.

## Prerequisites
Beads 1, 2, 3 must be merged (they are — check git log).

## Reference
- `docs/DESIGN.md` section 4.1 for the full War Room layout
- `apps/web/src/components/stats/` for ContextualMetricCard, FormBadgeStrip, DeltaBadge, InlineSparkline
- `apps/web/src/lib/api.ts` for existing API calls (getGames, getTeamStats, getPlayerLeaderboard)
- Mockup: `~/.openclaw/workspace/mockups/dashboard.html` (reference only, don't copy verbatim)

## Files to Modify
- `apps/web/src/app/dashboard/page.tsx` — full rebuild (main deliverable)
- `apps/web/src/components/DashboardTopbar.tsx` — move school+season selector here (compact)
- `apps/web/src/components/SchoolSeasonSelector.tsx` — may need a compact variant prop

## Files to DELETE
- `apps/web/src/components/DashboardStats.tsx` — replaced by the new layout
- `apps/web/src/components/ValueCard.tsx` — replaced by ContextualMetricCard

## Layout Target (matches DESIGN.md section 4.1)

```
┌──────────────────────────────────┬────────────────────────────────┐
│ SEASON RECORD & FORM             │ SMART INSIGHTS                 │
│ 12-4-2  [W][W][L][D][W]          │ (placeholder teal card)        │
│ Season 2024                      │                                │
├────────────┬───────────┬─────────┤                                │
│ GOALS/GAME │ SHOT CONV │CLEAN SHT│                                │
│    1.85    │   18.4%   │   4     │                                │
│  (no delta)│(no delta) │(no delta│                                │
├────────────┴───────────┴─────────┼────────────────────────────────┤
│ SEASON TREND: GF vs GA           │ TOP CONTRIBUTORS               │
│ [Line chart — teal vs orange]    │ 1. Player — 4G 2A  ████░░      │
│                                  │ 2. Player — 3G 1A  ███░░░      │
│                                  │ 3. Player — 2G 2A  ██░░░░      │
└──────────────────────────────────┴────────────────────────────────┘
```

**Grid**: `grid-cols-1 lg:grid-cols-3 gap-4` — most cards span 2 cols on left, 1 col on right.

## Implementation Details

### 1. School/Season Selector (DashboardTopbar)

Move the `SchoolSeasonSelector` out of the page and into `DashboardTopbar`. The topbar should accept optional `onSchoolSeasonChange` callback and render a compact inline selector. This keeps the page clean.

Update `DashboardTopbar.tsx`:
- Add props: `onSchoolSeasonChange?: (abbr: string, year: number, name: string) => void`
- Render `<SchoolSeasonSelector>` in the topbar right side, compact style
- Remove `pageTitle` prop (or keep it, up to you)

Update `DashboardLayout` (`dashboard/layout.tsx`): Since DashboardTopbar is a Server Component but SchoolSeasonSelector is client-side, extract the selector logic. The simplest approach: make DashboardTopbar a client component that manages its own school/season state and passes data up via a context or callback. 

**Simpler alternative** (preferred for now): Keep the selector in the page itself but render it at the top in a compact horizontal strip, not a prominent block. Move it to a `<div className="flex items-center justify-between mb-6">` header row with a compact right-aligned selector.

### 2. Page State & Data Fetching

Keep the existing `fetchData` pattern. Add these computed values:

```typescript
// Computed from teamStats + allGames:
const gamesPlayed = teamStats?.games_played ?? 0;
const totalGoals = teamStats?.total_goals ?? 0;
const totalShots = teamStats?.total_shots ?? 0;
const totalSOG = teamStats?.total_shots_on_goal ?? 0;

const goalsPerGame = gamesPlayed > 0 ? (totalGoals / gamesPlayed) : 0;
const shotConversion = totalShots > 0 ? (totalGoals / totalShots * 100) : 0;
const sogAccuracy = totalShots > 0 ? (totalSOG / totalShots * 100) : 0;

// Clean sheets: count games where this school's goals_against = 0
// We can compute from allGames: count games where opponent scored 0
// Use getResult logic — if W with opponent score 0, or D with 0-0
// Simpler: count games where (isHome && away_score===0) || (!isHome && home_score===0)
const cleanSheets = allGames.filter(game => {
  if (game.home_score == null || game.away_score == null) return false;
  const isHome = game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
  const opponentScore = isHome ? game.away_score : game.home_score;
  return opponentScore === 0;
}).length;
```

**Note on deltas**: We don't have conference average API yet. Set `delta={undefined}` on all ContextualMetricCards for now — the component handles missing delta gracefully (no badge shown). Add a `// TODO: wire conference avg delta when /api/conferences/{abbr}/standings lands` comment.

### 3. Form Badge Strip

Compute from `allGames`, sorted by date ascending, last 5:

```typescript
const formResults = [...allGames]
  .filter(g => g.date != null && g.home_score != null && g.away_score != null)
  .sort((a, b) => (a.date ?? '').localeCompare(b.date ?? ''))
  .slice(-5)
  .map(game => {
    const isHome = game.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
    const schoolScore = isHome ? game.home_score! : game.away_score!;
    const opponentScore = isHome ? game.away_score! : game.home_score!;
    const result: 'W' | 'L' | 'D' = schoolScore > opponentScore ? 'W' : schoolScore < opponentScore ? 'L' : 'D';
    return { result, gameId: game.game_id };
  });
```

### 4. Row 1 — Season Record & Smart Insights (2-col grid)

**Left card** (`bento-card p-5`, `lg:col-span-2`):
```
SEASON RECORD
12 – 4 – 2
[W][W][L][D][W]   ← FormBadgeStrip
{season} Season
```

Layout:
- `stat-label` for "SEASON RECORD"  
- Record as large text: `<span className="text-3xl font-extrabold tabular-nums text-slate-900">{record.w} – {record.l} – {record.d}</span>`
- Color W/L/D counts using `text-data-positive`, `text-data-negative`, `text-data-neutral`
- `<FormBadgeStrip results={formResults} />` below
- Small `text-xs text-slate-400` showing `{season} Season`

**Right card** (`bento-card p-5 bg-teal-50 border-teal-200`, `lg:col-span-1`):
Smart Insights placeholder:
```
SMART INSIGHTS
⚡ Insights powered by real data coming soon.
Track scoring streaks, conversion trends, and conference benchmarks.
```
Use `stat-label` for "SMART INSIGHTS", body in `text-sm text-teal-700`.

### 5. Row 2 — KPI Cards (3 cards in a row, or nested grid)

Three `ContextualMetricCard` components side by side:

```typescript
<ContextualMetricCard
  label="Goals / Game"
  value={goalsPerGame.toFixed(2)}
  // delta={undefined} — no conf avg yet
  baseline="vs Conference Avg"
/>
<ContextualMetricCard
  label="Shot Conversion"
  value={`${shotConversion.toFixed(1)}%`}
/>
<ContextualMetricCard
  label="Clean Sheets"
  value={cleanSheets}
/>
```

Use a nested `grid grid-cols-3 gap-4` inside the main layout OR span `lg:col-span-2` with an internal 3-col grid.

### 6. Row 3 — Season Trend Chart + Top Contributors

**Left: Season Trend** (`bento-card p-5`, `lg:col-span-2`):

Use Recharts `LineChart`. Data = `allGames` sorted by date, one entry per game:
```typescript
const trendData = [...allGames]
  .filter(g => g.date != null && g.home_score != null && g.away_score != null)
  .sort((a, b) => (a.date ?? '').localeCompare(b.date ?? ''))
  .map((g, i) => {
    const isHome = g.home_team?.toLowerCase().includes(schoolName.toLowerCase()) ?? false;
    return {
      label: g.date ? new Date(g.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : `G${i+1}`,
      gf: isHome ? (g.home_score ?? 0) : (g.away_score ?? 0),
      ga: isHome ? (g.away_score ?? 0) : (g.home_score ?? 0),
    };
  });
```

Chart:
- `<ResponsiveContainer width="100%" height={200}>`
- Two `<Line>` elements: `gf` in `#0D9488` (teal/data-primary), `ga` in `#F97316` (orange/data-opponent)
- `<XAxis dataKey="label" tick={{ fontSize: 10 }} />`, `<YAxis width={24} tick={{ fontSize: 10 }} />`
- `<Tooltip />`, `<Legend />` with custom labels ("Goals For", "Goals Against")
- `stat-label` header: "SEASON TREND"

**Right: Top Contributors** (`bento-card p-5`, `lg:col-span-1`):

Show top 5 players by goals. For each:
```
[rank] [name]          [G]G [A]A
       [progress bar]
```

Progress bar: `<div className="h-1.5 rounded-full bg-data-primary" style={{ width: `${(player.total_goals / maxGoals) * 100}%` }} />`
Background: `bg-slate-100 rounded-full h-1.5` wrapper.

Each player name is a plain text for now (no player profile route yet). Show `player.player_name`, `{player.total_goals}G`, `{player.total_assists}A`.

Use `topPerformers` (already fetched, top 5 — update the fetch limit to 5).

### 7. Loading & Empty States

Keep the existing spinner for loading. For empty state (no data selected), show a centered message: "Select a school and season above to load the War Room."

### 8. Remove DashboardStats

Delete `apps/web/src/components/DashboardStats.tsx` and `apps/web/src/components/ValueCard.tsx`. Remove all imports of these in dashboard/page.tsx.

## Out of Scope
- No new API endpoints
- No conference average deltas (placeholder only)
- No Smart Insights logic (placeholder card only)
- No Next Match scouting card (placeholder or omit)
- No player profile links (no route yet)
- No dark mode handling beyond what Tailwind handles automatically

## Validation
```bash
cd apps/web && npm run lint   # no errors
cd apps/web && npm run build  # clean build
```

Manually verify (start `npm run dev`, navigate to /dashboard):
- Select HU + 2024 → sees record, form badges, 3 KPI cards, trend chart, top 5 contributors
- Form badges show correct W/L/D colors
- Trend chart shows two colored lines
- No console errors

## Commit
`feat(web): rebuild War Room dashboard — bento grid, KPI cards, form badges, trend chart, top contributors`

## When done
```bash
openclaw system event --text "Done: Bead 4 War Room — bento dashboard live with real data, form badges, trend chart" --mode now
```
