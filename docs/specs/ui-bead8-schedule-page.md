# Bead 8: Schedule & Results Page

## Overview
Build the `/dashboard/games` page — full season timeline for the selected school/season.
Data is already available via existing `getGames()` API. Mostly layout work.

## Files to Modify
- `apps/web/src/app/dashboard/games/page.tsx` — full rebuild (currently shows a basic table)

## Reference
- `docs/DESIGN.md` section 4.2 for layout spec
- Existing `apps/web/src/app/dashboard/page.tsx` for school/season selector pattern
- `apps/web/src/components/stats/FormBadgeStrip.tsx` — reuse result badge colors

---

## Implementation

This is a Client Component. Read `gender` from `GenderContext`. Use `SchoolSeasonSelector`
in the same compact header pattern as the War Room page.

### State
```typescript
const [school, setSchool] = useState("")
const [schoolName, setSchoolName] = useState("")
const [season, setSeason] = useState(2025)
const [games, setGames] = useState<GameSummary[]>([])
const [loading, setLoading] = useState(true)
```

### Data fetching
Use `getGames(abbr, season, 100, 0)` — same as dashboard. Sort by date ascending for timeline.

### Layout

```
Header row: "Schedule & Results" title + SchoolSeasonSelector (compact, right-aligned)

Summary strip (bento-card, flex row):
  [W count] [L count] [D count] [Home record] [Away record]

Timeline table (bento-card, full width):
  stat-label: "2024 SEASON"
  
  Each row (one per game):
  [Date] [Result badge] [H/A badge] [Opponent] [Score] [→ detail link]
```

### Summary strip
Compute from games array:
- W / L / D totals
- Home record: `{hw}W-{hl}L-{hd}D` (where school is home_team)
- Away record: `{aw}W-{al}L-{ad}D`

Each stat in a small bento-card sub-block with `stat-label` + `stat-value`.

### Timeline table

Sort games by date ascending. For each game:

**Result badge:** `w-8 h-8 rounded-md font-bold text-xs flex items-center justify-center`
- W: `bg-emerald-500 text-white`
- L: `bg-rose-500 text-white`
- D: `bg-amber-500 text-white`
- No result yet: `bg-slate-100 text-slate-400` showing "–"

**H/A badge:** `text-xs font-semibold px-1.5 py-0.5 rounded`
- Home: `bg-data-primary/10 text-data-primary` showing "H"
- Away: `bg-slate-100 text-slate-500` showing "A"

**Determine home/away:** `game.home_team?.toLowerCase().includes(schoolName.toLowerCase())`

**Opponent:** show `home_team` if school is away, `away_team` if school is home.

**Score:** `{home_score} – {away_score}` in `tabular-nums font-bold`

**Row link:** entire row is clickable → `/dashboard/games/{game.game_id}`
Use `hover:bg-surface-muted cursor-pointer transition-colors`

**Date format:** `new Date(game.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })`

### Filters (below header, above table)
Three small toggle buttons: `All | Home | Away` — filter the displayed rows client-side.
Result filter: `All | W | L | D` — secondary filter.

Style: `inline-flex rounded-lg border overflow-hidden` pill group.
Active: `bg-data-primary text-white`, inactive: `bg-white text-slate-600 hover:bg-surface-muted`

### Empty/Loading states
- Loading: centered spinner
- No school selected: "Select a school above to view their schedule."
- No games: "No games found for this selection."

## Out of Scope
- No conference/non-conference toggle (no `is_conference_game` data for all schools yet)
- No export

## Validation
```bash
cd apps/web && npm run lint && npm run build
```
Manually: select HU + 2024, see 18 games in timeline, W/L/D badges correct, home/away correct.

## Commit
`feat(web): schedule & results page — season timeline with W/L/D badges, home/away filter`

## When done
```bash
openclaw system event --text "Done: Bead 8 schedule page — season timeline live" --mode now
```
