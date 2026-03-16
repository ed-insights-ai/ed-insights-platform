# Bead 5: Gender + Conference Filter — School Selector

## Overview
Wire up the gender toggle to actually filter the school list. Add a conference concept
(GAC only for now) so the selector hierarchy is:

```
Gender (global sidebar) → Conference (default GAC) → School (drill-down)
```

## Files to Modify

### API
- `apps/api/src/routers/schools.py` — add `?gender=` and `?conference=` query params
- `apps/api/src/schemas.py` — add `gender` and `conference` fields to `SchoolResponse`
- `apps/api/src/models.py` — verify `gender` and `conference` fields exist (migration 004 added them)

### Frontend
- `apps/web/src/lib/api.ts` — update `getSchools()` to accept gender + conference params
- `apps/web/src/components/SchoolSeasonSelector.tsx` — connect to GenderContext, add conference display

## Implementation

### 1. API: Update schools router

`GET /api/schools` should accept:
- `?gender=men` or `?gender=women` — filters by `schools.gender` column
- `?conference=GAC` — filters by `schools.conference` column (nullable, use ILIKE or exact match)

```python
@router.get("/schools", response_model=list[SchoolResponse])
async def list_schools(
    gender: str | None = Query(None, description="Filter by gender: 'men' or 'women'"),
    conference: str | None = Query(None, description="Filter by conference abbreviation e.g. 'GAC'"),
    db: AsyncSession = Depends(get_db),
) -> list[School]:
    stmt = select(School).where(School.enabled == True)
    if gender:
        stmt = stmt.where(School.gender == gender)
    if conference:
        stmt = stmt.where(School.conference == conference)
    result = await db.execute(stmt.order_by(School.name))
    return result.scalars().all()
```

Note: `School.enabled` filter ensures disabled schools (like NSU) are excluded.

### 2. API: Update SchoolResponse schema

Add `gender` and `conference` to the Pydantic response schema so the frontend knows what each school is:

```python
class SchoolResponse(BaseModel):
    id: int
    name: str
    abbreviation: str
    conference: str | None
    mascot: str | None
    gender: str | None          # "men" or "women"
    enabled: bool | None = True

    model_config = ConfigDict(from_attributes=True)
```

### 3. Frontend: Update getSchools() in api.ts

```typescript
export interface School {
  id: number;
  name: string;
  abbreviation: string;
  conference: string | null;
  mascot: string | null;
  gender: string | null;     // add this
  enabled: boolean | null;   // add this
}

export async function getSchools(params?: {
  gender?: string;
  conference?: string;
}): Promise<School[]> {
  try {
    const query = new URLSearchParams();
    if (params?.gender) query.set("gender", params.gender);
    if (params?.conference) query.set("conference", params.conference);
    const url = `${API_BASE_URL}/api/schools${query.toString() ? `?${query}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch schools: ${res.status}`);
    return (await res.json()) as School[];
  } catch (error) {
    console.error("Error fetching schools:", error);
    return [];
  }
}
```

### 4. Frontend: Update SchoolSeasonSelector

Read `gender` from `GenderContext`. Re-fetch school list whenever gender changes.
Show a compact "GAC" conference label (static for now — only one conference).

```typescript
"use client";

import { useGender } from "@/context/GenderContext";
import { getSchools } from "@/lib/api";
// ... existing imports

export function SchoolSeasonSelector({ onSelectionChange }) {
  const { gender } = useGender();
  const [schools, setSchools] = useState<School[]>([]);
  // ... existing season/school state

  // Re-fetch schools when gender changes
  useEffect(() => {
    getSchools({ gender, conference: "GAC" }).then(setSchools);
  }, [gender]);

  // Reset selected school when gender changes (avoid stale school from other gender)
  useEffect(() => {
    setSelectedSchool("");
    setSelectedSchoolName("");
  }, [gender]);

  // ... rest of component unchanged
}
```

Key behaviors:
- When gender switches Men's → Women's: school list refreshes, current selection clears
- Default selection on load: first school in the filtered list (or empty — coach picks)
- Conference label: show "GAC" as a static badge next to the selector (no dropdown needed yet)

### 5. Conference label in selector UI

Add a small non-interactive conference badge to the selector:
```
[GAC ▾] [School ▾] [Season ▾]
```
The GAC badge is just a styled `<span>` for now — not a dropdown. When we add more conferences, it becomes a real select.

Style: `inline-flex items-center gap-1 rounded-md bg-surface-muted px-2 py-1.5 text-xs font-semibold text-slate-600`

## Out of Scope
- No multi-conference support yet (GAC only)
- No user preference persistence for default school
- No changes to dashboard data fetching logic — selector still calls `onSelectionChange(abbr, year, name)`

## Validation
```bash
# API
cd apps/api && uv run uvicorn src.main:app --port 8000 --reload &
curl "http://localhost:8000/api/schools?gender=men" | python3 -m json.tool | grep abbreviation
curl "http://localhost:8000/api/schools?gender=women" | python3 -m json.tool | grep abbreviation
# men should return ~13 schools, women ~5

# Frontend
cd apps/web && npm run lint   # no errors
cd apps/web && npm run build  # clean build
```

Manually verify:
- Toggle Men's → school list shows only men's programs
- Toggle Women's → school list switches to women's programs, previous selection clears
- GAC badge visible in selector
- Selecting a school + season still loads War Room data correctly

## Commit
`feat: wire gender filter to school selector — API gender/conference params, selector respects GenderContext`

## When done
```bash
openclaw system event --text "Done: Bead 5 gender filter — school selector respects gender toggle, API filters by gender+conference" --mode now
```
