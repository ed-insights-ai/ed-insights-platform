# Spec: GAC Full Scrape — All 13 Ready Programs

**Feature:** Scrape all 13 enabled GAC soccer programs (2016–2025) and load into Postgres
**ADRs:** ADR-005, ADR-006
**Bead prefix:** eip

---

## Context

`schools.toml` now contains 14 verified GAC programs. 13 are enabled and ready:
- 2 StatCrew (Harding M + W) — statcrew scraper
- 11 SideArm New — sidearm scraper

1 program blocked (NSU men's — SideArm Legacy, scraper not implemented).

This spec scrapes the 13 enabled programs, loads data into Postgres, and runs
a completeness audit.

---

## Implementation Plan

### Task 1 — Run schema migration first

Ensure `005_add_conference_fields.sql` has been applied before loading data.
(Depends on `eip-schema-conference` bead being merged.)

If not yet merged, apply manually:
```bash
docker compose exec db psql -U postgres -d edinsights -f /migrations/005_add_conference_fields.sql
```

### Task 2 — Scrape all 13 enabled programs

Run the existing pipeline scraper for each enabled school in `schools.toml`.
The scraper already handles both `statcrew` and `sidearm` types.

```bash
cd packages/pipeline
uv run python -m pipeline.run --all-enabled 2>&1 | tee /tmp/scrape-gac-full.log
```

If `--all-enabled` flag doesn't exist, run per school:
```bash
for abbr in HU HUW FHSU NU OBU RSU SNU ECU NWOSU OKBU OBUW SNUW SWOSU; do
    uv run python -m pipeline.run --school $abbr
done
```

### Task 3 — Populate `is_conference_game` and `home_conference`

After scrape, update games with known conference info:

```sql
-- Set home_conference for all games from GAC schools
UPDATE games g
SET home_conference = s.conference
FROM schools s
WHERE g.school_id = s.id
  AND g.home_conference IS NULL;
```

For SideArm schools, `is_conference_game` should already be populated by the
scraper if it reads the `is_conference` flag from the schedule page.
If not implemented yet, leave NULL — it's a Phase 1 enhancement, not a blocker.

### Task 4 — Completeness audit

Run a summary query to verify expected game counts:

```sql
SELECT
    s.abbreviation,
    s.gender,
    s.name,
    COUNT(DISTINCT g.game_id)        AS total_games,
    COUNT(DISTINCT g.season_year)    AS seasons,
    MIN(g.season_year)               AS first_season,
    MAX(g.season_year)               AS last_season
FROM schools s
LEFT JOIN games g ON g.school_id = s.id
WHERE s.enabled = true
GROUP BY s.id, s.abbreviation, s.gender, s.name
ORDER BY s.gender, s.abbreviation;
```

Expected rough targets per program (10yr programs):
- ~150–200 games across 10 seasons (15–20 games/season)

Programs with fewer years (affiliates joined 2019):
- FHSU, NU, NSU, RSU: ~7 seasons = ~100–140 games

### Task 5 — Generate parquet export

```bash
uv run python -m pipeline.export --output data/
```

Verify parquet files written:
- `data/games.parquet`
- `data/player_game_stats.parquet`
- `data/team_game_stats.parquet`
- `data/game_events.parquet`

---

## Expected Data Volume (estimates)

| Metric | Estimate |
|---|---|
| Total programs | 13 enabled |
| Avg seasons/program | 8.5 (mix of 10yr and 7yr) |
| Avg games/season | 16 |
| **Total games** | **~1,760** |
| Player stats rows | ~40 per game × 1,760 = ~70,400 |
| Game events rows | ~20 per game × 1,760 = ~35,200 |

## Testing

- No errors in scrape log
- All 13 schools have at least 1 game in DB
- `SELECT COUNT(*) FROM games` > 1,500
- Parquet files present and non-empty

## Acceptance Criteria

- [ ] All 13 enabled programs scraped successfully
- [ ] Games table populated (target: >1,500 rows)
- [ ] `home_conference = 'GAC'` set on all games
- [ ] Parquet files exported and committed (or noted as gitignored per ADR-004)
- [ ] Completeness audit query runs and shows reasonable game counts per school
- [ ] No school has 0 games (scraper failure = blocked bead)

## Validation Commands

```bash
cd ~/source/ed-insights-platform
docker compose up -d
cd packages/pipeline
uv run python -m pipeline.run --all-enabled
# Then audit:
docker compose exec db psql -U postgres -d edinsights -c "
SELECT s.abbreviation, COUNT(g.game_id) as games
FROM schools s LEFT JOIN games g ON g.school_id = s.id
WHERE s.enabled = true
GROUP BY s.abbreviation ORDER BY s.abbreviation;"
```

## Execution

```
Implement docs/specs/eip-gac-full-scrape.md
```
