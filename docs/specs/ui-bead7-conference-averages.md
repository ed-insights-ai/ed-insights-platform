# Bead 7: Conference Average Deltas on War Room KPIs

## Overview
Add a `GET /api/conferences/{abbr}/averages` endpoint that returns per-season conference
averages, then wire those averages into the War Room KPI cards as delta badges.
This delivers DESIGN.md's core thesis: "no number without context."

## Files to Modify
- `apps/api/src/routers/conferences.py` — add new endpoint
- `apps/api/src/schemas.py` — add ConferenceAverages schema
- `apps/web/src/lib/api.ts` — add getConferenceAverages()
- `apps/web/src/app/dashboard/page.tsx` — fetch averages + pass deltas to KPI cards

---

## Part 1: API

### New schema in schemas.py

```python
class ConferenceAverages(BaseModel):
    conference: str
    gender: str
    season: int
    schools_count: int
    avg_goals_per_game: float       # GF / GP averaged across all schools
    avg_shot_conversion: float      # total_goals / total_shots * 100
    avg_clean_sheet_pct: float      # games with 0 GA / total games * 100
    avg_shots_per_game: float
    avg_sog_per_game: float
```

### New endpoint in conferences.py

```
GET /api/conferences/{abbr}/averages?season=2024&gender=men
```

Logic: use the same `games` table + `_ilike_pattern` + `_matches_pattern` helpers already in
conferences.py to compute per-school stats, then average across schools.

```python
@router.get("/{abbr}/averages", response_model=ConferenceAverages)
async def conference_averages(
    abbr: str,
    season: int = Query(...),
    gender: str = Query("men"),
    db: AsyncSession = Depends(get_db),
) -> ConferenceAverages:
    # Get enabled schools
    result = await db.execute(
        select(School).where(
            School.conference == abbr,
            School.gender == gender,
            School.enabled == True,  # noqa: E712
        )
    )
    schools = result.scalars().all()
    if not schools:
        raise HTTPException(status_code=404, detail="No schools found")

    school_stats = []  # list of dicts per school

    for school in schools:
        pattern = _ilike_pattern(school.name)
        games_result = await db.execute(
            select(Game).where(
                Game.school_id == school.id,
                Game.season_year == season,
                Game.home_score.is_not(None),
                Game.away_score.is_not(None),
            )
        )
        games = games_result.scalars().all()
        if not games:
            continue

        gp = total_gf = total_shots = total_sog = clean_sheets = 0
        for g in games:
            is_home = _matches_pattern(g.home_team, pattern)
            own_score = g.home_score if is_home else g.away_score
            opp_score = g.away_score if is_home else g.home_score
            gp += 1
            total_gf += own_score
            if opp_score == 0:
                clean_sheets += 1

        # Get team stats for shots (TGS is fine for shots — we just need own team row)
        # Use school_id + is_home to get own team's TGS rows
        from src.models import TeamGameStats
        tgs_result = await db.execute(
            select(TeamGameStats).join(Game, TeamGameStats.game_id == Game.game_id).where(
                TeamGameStats.school_id == school.id,
                Game.season_year == season,
                TeamGameStats.team.ilike(pattern),
            )
        )
        tgs_rows = tgs_result.scalars().all()
        # Deduplicate by game_id
        seen = set()
        for row in tgs_rows:
            if row.game_id not in seen:
                seen.add(row.game_id)
                total_shots += row.shots or 0
                total_sog += row.shots_on_goal or 0

        school_stats.append({
            "gp": gp,
            "gf": total_gf,
            "shots": total_shots,
            "sog": total_sog,
            "clean_sheets": clean_sheets,
        })

    if not school_stats:
        raise HTTPException(status_code=404, detail="No game data found")

    # Compute averages across schools
    n = len(school_stats)
    avg_gpg = round(sum(s["gf"] / s["gp"] for s in school_stats if s["gp"] > 0) / n, 2)
    avg_conv = round(
        sum(s["gf"] / s["shots"] * 100 for s in school_stats if s["shots"] > 0) / n, 1
    )
    avg_cs_pct = round(
        sum(s["clean_sheets"] / s["gp"] * 100 for s in school_stats if s["gp"] > 0) / n, 1
    )
    avg_spg = round(sum(s["shots"] / s["gp"] for s in school_stats if s["gp"] > 0) / n, 1)
    avg_sog_pg = round(sum(s["sog"] / s["gp"] for s in school_stats if s["gp"] > 0) / n, 1)

    return ConferenceAverages(
        conference=abbr,
        gender=gender,
        season=season,
        schools_count=n,
        avg_goals_per_game=avg_gpg,
        avg_shot_conversion=avg_conv,
        avg_clean_sheet_pct=avg_cs_pct,
        avg_shots_per_game=avg_spg,
        avg_sog_per_game=avg_sog_pg,
    )
```

---

## Part 2: Frontend

### api.ts — add type and function

```typescript
export interface ConferenceAverages {
  conference: string;
  gender: string;
  season: number;
  schools_count: number;
  avg_goals_per_game: number;
  avg_shot_conversion: number;
  avg_clean_sheet_pct: number;
  avg_shots_per_game: number;
  avg_sog_per_game: number;
}

export async function getConferenceAverages(
  abbr: string,
  season: number,
  gender: string = "men"
): Promise<ConferenceAverages | null> {
  try {
    const params = new URLSearchParams({ season: String(season), gender });
    const res = await fetch(`${API_BASE_URL}/api/conferences/${abbr}/averages?${params}`);
    if (!res.ok) return null;
    return (await res.json()) as ConferenceAverages;
  } catch {
    return null;
  }
}
```

### dashboard/page.tsx — wire in averages

1. Add state: `const [confAvg, setConfAvg] = useState<ConferenceAverages | null>(null)`

2. In `fetchData`, add a parallel call alongside existing fetches:
```typescript
const [gamesRes, statsRes, playersRes, topPerformersRes, confAvgRes] = await Promise.all([
  getGames(abbr, yr, 100, 0),
  getTeamStats(abbr, yr),
  getPlayerLeaderboard(abbr, yr, "goals", 5, 0),
  getPlayerLeaderboard(abbr, yr, "goals", 5, 0),
  getConferenceAverages("GAC", yr, gender),  // hardcode GAC for now
]);
setConfAvg(confAvgRes);
```

Note: `fetchData` needs access to `gender` from `GenderContext`. Add `const { gender } = useGender()` to the page component and pass `gender` into `fetchData` or capture it via closure.

3. Compute deltas in render (before the JSX return):
```typescript
const goalsPerGameDelta = confAvg
  ? parseFloat((goalsPerGame - confAvg.avg_goals_per_game).toFixed(2))
  : undefined;

const shotConvDelta = confAvg
  ? parseFloat((shotConversion - confAvg.avg_shot_conversion).toFixed(1))
  : undefined;

const cleanSheetPctDelta = confAvg && gamesPlayed > 0
  ? parseFloat(((cleanSheets / gamesPlayed * 100) - confAvg.avg_clean_sheet_pct).toFixed(1))
  : undefined;
```

4. Pass deltas to ContextualMetricCards:
```tsx
<ContextualMetricCard
  label="Goals / Game"
  value={goalsPerGame.toFixed(2)}
  delta={goalsPerGameDelta}
  deltaUnit=""
  baseline="vs Conference Avg"
/>
<ContextualMetricCard
  label="Shot Conversion"
  value={`${shotConversion.toFixed(1)}%`}
  delta={shotConvDelta}
  deltaUnit="%"
  baseline="vs Conference Avg"
/>
<ContextualMetricCard
  label="Clean Sheets"
  value={cleanSheets}
  delta={cleanSheetPctDelta}
  deltaUnit="%"
  baseline="vs Conference Avg"
/>
```

Remove the `// TODO: wire conference avg delta` comments.

---

## Out of Scope
- No caching/materialized views (query is fast enough at current scale)
- Conference is hardcoded to "GAC" on the dashboard for now
- No changes to Conference Overview page

## Validation
```bash
# API
curl -s "http://localhost:8000/api/conferences/GAC/averages?season=2024&gender=men" | python3 -m json.tool
# Expect: avg_goals_per_game ~1.5-2.5, avg_shot_conversion ~10-20%, schools_count=6

# Frontend
cd apps/web && npm run lint && npm run build
```

Manually verify on /dashboard:
- Select HU, season 2024
- Goals/Game card shows delta badge (e.g. "+0.3 ▲ vs Conference Avg")
- Shot Conversion shows delta with % unit
- Clean Sheets shows % delta
- Above-avg = emerald badge, below-avg = rose badge

## Commit
`feat: conference average deltas on War Room KPI cards`

## When done
```bash
openclaw system event --text "Done: Bead 7 conf avg deltas — KPI cards now show +/- vs conference average" --mode now
```
