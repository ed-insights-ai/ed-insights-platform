# Bead 6: Conference Overview Page

## Overview
Build the Conference Overview page at `/conference/[abbr]` — a sortable standings data grid
showing all schools in the conference with W/L/D, GF/GA/GD, Points, PPG, and last-5 form badges.

## Critical Data Architecture Lesson (verified by querying production DB)

**DO NOT use `TeamGameStats` for standings computation.**

The `team_game_stats` table has TWO rows per game per school — one row for each team that played.
`tgs.is_home` means "this row is for the home team in the game", NOT "the school was home".
This causes double-counting and wrong record calculations.

**Use the `games` table directly.** Each game row belongs to `school_id` (the school that scraped it).
The school's own team appears in `home_team` or `away_team` via ILIKE matching on school name.

**Verified working query pattern for OBU 2024 (returns 18 GP, 3W 13L 2D ✓):**
```sql
SELECT
  COUNT(*) as gp,
  COUNT(*) FILTER (WHERE 
    (home_team ILIKE '%ouachita%' AND home_score > away_score) OR
    (away_team ILIKE '%ouachita%' AND away_score > home_score)
  ) as wins,
  ...
  SUM(CASE WHEN home_team ILIKE '%ouachita%' THEN home_score ELSE away_score END) as gf,
  SUM(CASE WHEN home_team ILIKE '%ouachita%' THEN away_score ELSE home_score END) as ga
FROM games g
JOIN schools s ON s.id = g.school_id
WHERE s.abbreviation='OBU' AND g.season_year=2024 AND home_score IS NOT NULL
```

**School name → ILIKE pattern mapping** (use `'%' + first_significant_word + '%'`):
- HU → `%Harding%`
- HUW → `%Harding%`
- OBU → `%Ouachita%`
- OBUW → `%Ouachita%`
- FHSU → `%Fort Hays%`
- SNU → `%Southern Nazarene%` (or `%Nazarene%`)
- SNUW → `%Southern Nazarene%`
- SWOSU → `%Southwestern Oklahoma%` (or `%SWOSU%`)
- NU → `%Newman%`
- NSU → `%Northeastern%`
- RSU → `%Rogers%`
- OKBU → `%Oklahoma Baptist%`
- ECU → `%East Central%`
- NWOSU → `%Northwestern Oklahoma%`

**Derive the ILIKE pattern dynamically from `school.name`:**
Take the first word of `school.name` that is >= 4 chars and not a stop word (University, College, State, etc).
This is robust across all schools.

Stop words to skip: `["University", "College", "State", "of", "the", "and", "at"]`

Example: "Fort Hays State" → first qualifying word = "Fort" → `%Fort%`
Example: "Ouachita Baptist" → first qualifying word = "Ouachita" → `%Ouachita%`
Example: "Southern Nazarene" → first qualifying word = "Southern" → `%Southern%`

## Files to Create
- `apps/api/src/routers/conferences.py`
- `apps/web/src/app/conference/[abbr]/page.tsx` (replace stub)

## Files to Modify
- `apps/api/src/main.py` — register conferences router
- `apps/api/src/schemas.py` — add FormResult + ConferenceStanding schemas
- `apps/web/src/lib/api.ts` — add getConferenceStandings()

---

## Part 1: API

### schemas.py — add these two classes

```python
class FormResult(BaseModel):
    result: str    # "W", "L", or "D"
    game_id: int

class ConferenceStanding(BaseModel):
    school_id: int
    school_name: str
    abbreviation: str
    gender: str
    games_played: int
    wins: int
    losses: int
    draws: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    ppg: float
    form: list[FormResult]  # last 5, oldest first
```

### conferences.py — full implementation

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, or_, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import Game, School
from src.schemas import ConferenceStanding, FormResult

router = APIRouter(prefix="/api/conferences")

STOP_WORDS = {"university", "college", "state", "of", "the", "and", "at", "women", "lady"}

def _ilike_pattern(school_name: str) -> str:
    """Derive ILIKE pattern from school name. Takes first significant word >= 4 chars."""
    for word in school_name.split():
        cleaned = word.strip("()").lower()
        if len(cleaned) >= 4 and cleaned not in STOP_WORDS:
            return f"%{word.strip('()')}%"
    # fallback: first word
    return f"%{school_name.split()[0]}%"

@router.get("/{abbr}/standings", response_model=list[ConferenceStanding])
async def conference_standings(
    abbr: str,
    season: int = Query(..., description="Season year e.g. 2024"),
    gender: str = Query("men", description="'men' or 'women'"),
    db: AsyncSession = Depends(get_db),
) -> list[ConferenceStanding]:
    # 1. Get schools in this conference
    result = await db.execute(
        select(School).where(
            School.conference == abbr,
            School.gender == gender,
            School.enabled == True,
        ).order_by(School.name)
    )
    schools = result.scalars().all()

    standings: list[ConferenceStanding] = []

    for school in schools:
        pattern = _ilike_pattern(school.name)

        # 2. Get all scored games for this school this season
        games_stmt = select(Game).where(
            Game.school_id == school.id,
            Game.season_year == season,
            Game.home_score.is_not(None),
            Game.away_score.is_not(None),
        ).order_by(Game.date.desc())

        games_result = await db.execute(games_stmt)
        games = games_result.scalars().all()

        # 3. Compute standings from games table
        gp = wins = losses = draws = gf = ga = 0

        for g in games:
            is_home = (g.home_team or "").upper().replace(" ", "") in (school.name.upper().replace(" ", ""), school.abbreviation.upper()) or \
                      _matches_pattern(g.home_team, pattern)
            
            own_score = g.home_score if is_home else g.away_score
            opp_score = g.away_score if is_home else g.home_score

            gp += 1
            gf += own_score
            ga += opp_score

            if own_score > opp_score:
                wins += 1
            elif own_score < opp_score:
                losses += 1
            else:
                draws += 1

        points = wins * 3 + draws
        ppg = round(points / gp, 2) if gp > 0 else 0.0
        goal_diff = gf - ga

        # 4. Form: last 5 games (games already sorted desc, take first 5, then reverse)
        form: list[FormResult] = []
        for g in games[:5]:
            is_home = _matches_pattern(g.home_team, pattern)
            own_score = g.home_score if is_home else g.away_score
            opp_score = g.away_score if is_home else g.home_score
            if own_score > opp_score:
                res = "W"
            elif own_score < opp_score:
                res = "L"
            else:
                res = "D"
            form.append(FormResult(result=res, game_id=g.game_id))
        form.reverse()  # oldest first

        standings.append(ConferenceStanding(
            school_id=school.id,
            school_name=school.name,
            abbreviation=school.abbreviation,
            gender=school.gender or gender,
            games_played=gp,
            wins=wins,
            losses=losses,
            draws=draws,
            goals_for=gf,
            goals_against=ga,
            goal_diff=goal_diff,
            points=points,
            ppg=ppg,
            form=form,
        ))

    # Sort: points DESC, goal_diff DESC, goals_for DESC
    standings.sort(key=lambda s: (s.points, s.goal_diff, s.goals_for), reverse=True)
    return standings


def _matches_pattern(team_name: str | None, pattern: str) -> bool:
    """Check if team_name matches the ILIKE pattern (case-insensitive substring)."""
    if not team_name:
        return False
    # pattern is like '%Fort%' — extract the keyword
    keyword = pattern.strip("%").lower()
    return keyword in team_name.lower()
```

### main.py — add router registration
```python
from src.routers import conferences
app.include_router(conferences.router)
```

---

## Part 2: Frontend

### api.ts — add types and function

```typescript
export interface FormResult {
  result: "W" | "L" | "D";
  game_id: number;
}

export interface ConferenceStanding {
  school_id: number;
  school_name: string;
  abbreviation: string;
  gender: string;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  ppg: number;
  form: FormResult[];
}

export async function getConferenceStandings(
  abbr: string,
  season: number,
  gender: string = "men"
): Promise<ConferenceStanding[]> {
  try {
    const params = new URLSearchParams({ season: String(season), gender });
    const res = await fetch(`${API_BASE_URL}/api/conferences/${abbr}/standings?${params}`);
    if (!res.ok) throw new Error(`Failed to fetch standings: ${res.status}`);
    return (await res.json()) as ConferenceStanding[];
  } catch (error) {
    console.error("Error fetching conference standings:", error);
    return [];
  }
}
```

### apps/web/src/app/conference/[abbr]/page.tsx — full rebuild

Client component. State: `standings`, `loading`, `season` (default 2025, then try 2024 if empty), `sortKey`, `sortDir`. Read `gender` from `GenderContext`.

**Layout:**
```
Header row: "GAC Conference" title + gender badge (teal pill "Men's" or purple "Women's")
Subhead: "Great American Conference · {season} Season"
Season selector: <select> 2016–2025, default 2025

bento-card with overflow-x-auto:
  stat-label: "STANDINGS"
  Sortable table (see columns below)

Loading: centered spinner
Empty: "No standings data for {season}."
```

**Table columns** (all numeric cols use `tabular-nums`):

| Column | Key | Notes |
|--------|-----|-------|
| # | rank (1-based) | not sortable, `text-slate-400 text-xs` |
| School | school_name | link to `/explore/teams/{abbreviation}` |
| GP | games_played | |
| W | wins | `text-data-positive font-semibold` |
| L | losses | `text-data-negative font-semibold` |
| D | draws | `text-data-neutral font-semibold` |
| GF | goals_for | |
| GA | goals_against | |
| GD | goal_diff | badge: positive=`text-data-positive`, negative=`text-data-negative`, zero=`text-slate-400` |
| Pts | points | `font-extrabold text-slate-900` |
| PPG | ppg | |
| Form | form | `<FormBadgeStrip results={row.form} size="sm" />` |

**Sorting:** click header → sort client-side. Show ▲/▼ on active sort column. Default sort: points DESC.

**Rank 1 row:** `border-l-2 border-data-primary`

**Row styles:** `even:bg-surface-muted hover:bg-slate-50 cursor-pointer`

**Season selector:** `<select>` years 2016–2025 (descending), default 2025. On change → re-fetch.

## Out of Scope
- No playoff zone markers
- No discipline table
- No inline sparklines in table cells
- No team profile pages (links go to stub)

## Validation
```bash
# API test (postgres + api must be running)
brew services start postgresql@15
cd apps/api && uv run uvicorn src.main:app --port 8000 --reload &
sleep 2
curl -s "http://localhost:8000/api/conferences/GAC/standings?season=2024&gender=men" | \
  python3 -c "import json,sys; data=json.load(sys.stdin); [print(f\"{d['school_name']:<25} GP={d['games_played']} W={d['wins']} L={d['losses']} D={d['draws']} GD={d['goal_diff']:+d} Pts={d['points']}\") for d in data]"

# Expected: ~6 men's schools, sensible records (GP 15-25, W+L+D=GP)

# Frontend
cd apps/web && npm run lint
cd apps/web && npm run build
```

## Commit
`feat: conference overview page — standings API + sortable data grid with form badges`

## When done
```bash
openclaw system event --text "Done: Bead 6 Conference Overview — standings table live with form badges, GD coloring, sortable" --mode now
```
