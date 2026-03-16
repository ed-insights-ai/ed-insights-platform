# Spec: GAC Data Reset — Correct School List, Clean DB, Full Re-scrape

**Date:** 2026-03-16
**Status:** Ready
**Reference:** ADR-007 (GAC School Membership)

## Problem

The database and pipeline have accumulated errors over multiple sessions:

1. **Wrong abbreviations** — 4 women's schools stored with `W` suffix that
   shouldn't have it: `ECUW`, `NWOSUW`, `OKBUW`, `SWOSUW` (should be `ECU`,
   `NWOSU`, `OKBU`, `SWOSU`)

2. **Wrong gender** — Same 4 schools stored as `gender = 'men'`

3. **Duplicate rows** — Both wrong and correct abbreviations exist for the same
   schools, resulting in 17 rows in `schools` instead of 14

4. **Wrong/missing `conference` values** — Some schools have empty `conference`

5. **Wrong school names** — Some rows have the abbreviation as the name
   (e.g. `name = 'ECUW'` instead of `'East Central'`)

6. **Stale game/player/event data** tied to corrupt school rows

## Goal

A clean database with exactly 14 schools matching ADR-007, all with correct
names, genders, abbreviations, and conference values — and fresh scraped data
loaded for all 13 scrapeable programs.

## Correct School List (from ADR-007)

### Men's (7)
| ordinal | abbr | name | gender | conference | scraper | years |
|---------|------|------|--------|------------|---------|-------|
| 1 | HU | Harding | men | GAC | statcrew | 2016-2025 |
| 2 | FHSU | Fort Hays State | men | GAC | sidearm | 2019-2025 |
| 3 | NU | Newman | men | GAC | sidearm | 2019-2025 |
| 4 | NSU | Northeastern State | men | GAC | sidearm_legacy | 2019-2025 |
| 5 | OBU | Ouachita Baptist | men | GAC | sidearm | 2016-2025 |
| 6 | RSU | Rogers State | men | GAC | sidearm | 2019-2025 |
| 7 | SNU | Southern Nazarene | men | GAC | sidearm | 2016-2025 |

### Women's (7)
| ordinal | abbr | name | gender | conference | scraper | years |
|---------|------|------|--------|------------|---------|-------|
| 8 | HUW | Harding | women | GAC | statcrew | 2016-2025 |
| 9 | ECU | East Central | women | GAC | sidearm | 2016-2025 |
| 10 | NWOSU | Northwestern Oklahoma State | women | GAC | sidearm | 2016-2025 |
| 11 | OKBU | Oklahoma Baptist | women | GAC | sidearm | 2016-2025 |
| 12 | OBUW | Ouachita Baptist | women | GAC | sidearm | 2016-2025 |
| 13 | SNUW | Southern Nazarene | women | GAC | sidearm | 2016-2025 |
| 14 | SWOSU | Southwestern Oklahoma State | women | GAC | sidearm | 2016-2025 |

## Implementation Plan

### Phase 1 — Fix `schools.toml`

Verify `packages/pipeline/config/schools.toml` matches the table above exactly:
- 14 entries, no more
- Correct `abbreviation`, `name`, `gender`, `conference` on every entry
- Women's schools without a men's counterpart use no `W` suffix
- NSU remains `enabled = false` with `scraper = "sidearm_legacy"`

If any entry is wrong, fix it.

### Phase 2 — Alembic Migration: Reset schools table

Create `packages/api/alembic/versions/005_reset_gac_schools.py`:

1. **Delete all child data** (CASCADE or explicit):
   - DELETE FROM `game_events`
   - DELETE FROM `player_game_stats`
   - DELETE FROM `team_game_stats`
   - DELETE FROM `games`
   - DELETE FROM `schools`

2. **Re-seed schools** from the correct 14-entry list (hardcoded in migration):
   - All 14 schools with correct: `abbreviation`, `name`, `gender`, `conference`, `enabled`
   - `ordinal` 1-14 as per the table above
   - NSU: `enabled = false`
   - All others: `enabled = true`

The migration should be idempotent — safe to run on an already-clean DB.

### Phase 3 — Re-scrape all enabled schools

Run the pipeline scraper for all 13 enabled programs:

```bash
cd packages/pipeline
uv run scrape  # scrapes all enabled schools in schools.toml
```

Expected output:
- HU: ~160 games (2016-2025, StatCrew)
- HUW: ~230 games (2016-2025, StatCrew)
- FHSU: ~150 games (2019-2025, SideArm)
- NU: ~105 games (2019-2025, SideArm)
- OBU: ~225 games (2016-2025, SideArm)
- RSU: ~130 games (2019-2025, SideArm)
- SNU: ~175 games (2016-2025, SideArm)
- ECU: ~165 games (2016-2025, SideArm)
- NWOSU: ~160 games (2016-2025, SideArm)
- OKBU: ~190 games (2016-2025, SideArm)
- OBUW: ~230 games (2016-2025, SideArm)
- SNUW: ~170 games (2016-2025, SideArm)
- SWOSU: ~185 games (2016-2025, SideArm)

NSU (men's) skipped — `enabled = false`.

### Phase 4 — Load into DB

```bash
uv run load-db
```

### Phase 5 — Validate

Run the audit script to confirm clean state:

```bash
uv run python -c "
import psycopg2, json
conn = psycopg2.connect('postgresql://lume@localhost/ed_insights')
cur = conn.cursor()
cur.execute('''
    SELECT s.abbreviation, s.name, s.gender, s.conference, s.enabled,
           COUNT(DISTINCT g.game_id) as games
    FROM schools s
    LEFT JOIN games g ON g.school_id = s.id
    GROUP BY s.id
    ORDER BY s.gender, s.abbreviation
''')
rows = cur.fetchall()
print(f'Total schools: {len(rows)}')
for r in rows:
    print(f'  {r[0]:6} | {r[1]:30} | {r[2]:6} | {r[3]:4} | enabled={r[4]} | games={r[5]}')
"
```

**Acceptance criteria:**
- Exactly 14 rows in `schools`
- Zero rows with `gender = 'men'` AND abbreviation ending in `W` (i.e. no ECUW, NWOSUW, etc.)
- All enabled schools have > 0 games
- NSU has 0 games (disabled)
- No school has `conference = ''` or `conference = NULL`
- Total games ≥ 2,500

## Testing

```bash
cd packages/pipeline && uv run pytest tests/ -v
```

All existing tests must pass after the migration and re-scrape.

## Notes

- **Do not** add ATU, HSU, SOSU, SAU, UAM, or any other school not in ADR-007
- **Do not** create SWOSUW, NWOSUW, ECUW, OKBUW abbreviations — these were wrong
- The `W` suffix convention: only when same school has both M and W programs
  (HU/HUW, OBU/OBUW, SNU/SNUW)
- Raw HTML cache will be re-downloaded from network — this is intentional
- NSU (SideArm Legacy) is a separate future spec; leave `enabled = false` for now

## Execution

```bash
cd ~/source/ed-insights-platform
claude --dangerously-skip-permissions "Implement docs/specs/data-reset-gac-correct.md"
```
