# Product Beads Document: GAC Full Conference Data Ingestion

## Goal
Scrape all remaining GAC member schools (men's + women's) to build a complete conference dataset.
Currently have HU M/W + OBU M/W (4 programs). Target: all 16 men's + 12 women's = 28 programs total.
That means adding 24 new programs across both genders.

## Scope
- Add `gender` field to `SchoolConfig` and `schools.toml`
- Research + validate SideArm base URLs for all remaining GAC schools
- Configure and scrape all schools 2016–2025 (or earliest available)
- Note: Men's affiliate members (FHSU, Newman, NSU, Rogers State) joined GAC 2019 — set years accordingly
- Women's GAC = 12 full members only (no affiliates)
- Yellow/red card data only available in SideArm 2020+ layouts — expected, not a bug

## GAC Membership Reference

### Men's Soccer (16 teams)
Full members (12):
- Arkansas Tech (ATU) — Wonder Boys
- Arkansas–Monticello (UAM) — Boll Weevils
- East Central (ECU) — Tigers
- Harding (HU) — Bisons ✅ DONE
- Henderson State (HSU) — Reddies
- Northwestern Oklahoma State (NWOSU) — Rangers
- Oklahoma Baptist (OBU_OK) — Bison (NOTE: abbreviation conflict with OBU/Ouachita — use OKBU)
- Ouachita Baptist (OBU) — Tigers ✅ DONE
- Southeastern Oklahoma State (SOSU) — Savage Storm
- Southern Arkansas (SAU) — Muleriders
- Southern Nazarene (SNU) — Crimson Storm
- Southwestern Oklahoma State (SWOSU) — Bulldogs

Affiliate members — men's only, joined 2019 (years = 2019–2025):
- Fort Hays State (FHSU) — Tigers
- Newman (NU) — Jets
- Northeastern State (NSU) — RiverHawks
- Rogers State (RSU) — Hillcats

### Women's Soccer (12 teams — full members only)
Same 12 full members as men's, no affiliates:
ATU, UAM, ECU, HU ✅, HSU, NWOSU, OKBU, OBU ✅, SOSU, SAU, SNU, SWOSU

## Codebase Context
- `packages/pipeline/config/schools.toml` — school config (add gender field)
- `packages/pipeline/src/config.py` — SchoolConfig dataclass (add gender field)
- `packages/pipeline/src/sidearm_discovery.py` — SideArm URL discovery (working)
- `packages/pipeline/src/sidearm_parser.py` — SideArm HTML parser (working)
- `packages/pipeline/scripts/scrape.py` — CLI: `uv run scrape --school ATU --year 2024`
- `packages/pipeline/data/structured/` — output location (parquet files)
- Run from: `cd packages/pipeline`

## Workflow
- Bead 1 (schema): Add gender field to config — unblocks everything else
- Bead 2 (research): Find + validate all SideArm URLs — must complete before scrape beads
- Beads 3–4 (scrape): Split men's and women's scraping — can run in parallel after bead 2
- Bead 5 (validate): Validate data quality and completeness across all programs

## Dependency Graph
```
eip-gac1 (schema)
    └── eip-gac2 (URL research)
            ├── eip-gac3 (scrape men's)
            └── eip-gac4 (scrape women's)
                    both → eip-gac5 (validate)
```

## Parallel Lanes
- Lane A: eip-gac3 (men's scrape) — after eip-gac2
- Lane B: eip-gac4 (women's scrape) — after eip-gac2
- eip-gac5 waits for both lanes

---

## Beads

### eip-gac1 · Schema: Add gender field to SchoolConfig

**Type:** chore  
**Priority:** 1 (blocks everything)  
**Effort:** S (< 30 min)

**Description:**
Add a `gender` field (`"men"` | `"women"`) to `SchoolConfig` in `packages/pipeline/src/config.py`
and update `packages/pipeline/config/schools.toml` to set `gender` on all existing entries.
Default should be `"men"` if field is absent (backwards compat). Also add `abbreviation` uniqueness
note — OBU is already used for Ouachita Baptist. Oklahoma Baptist should use `OKBU`.

**Inputs:**
- `packages/pipeline/src/config.py` — SchoolConfig dataclass
- `packages/pipeline/config/schools.toml` — current 4 entries

**Outputs:**
- `SchoolConfig.gender: str = "men"` field added with default
- All 4 existing schools in toml have `gender` set explicitly
- `load_schools()` passes through gender field correctly

**Acceptance Criteria:**
- `SchoolConfig` has `gender` field, defaults to `"men"`
- `uv run python -c "from src.config import load_schools; [print(s.abbreviation, s.gender) for s in load_schools()]"` prints gender for all 4 schools
- Existing scrape still works: `uv run scrape --school HU --year 2024` completes without error
- No existing tests broken: `uv run pytest tests/ -v` passes

---

### eip-gac2 · Research: Find and validate all GAC SideArm URLs

**Type:** chore  
**Priority:** 1 (blocks scrape beads)  
**Effort:** M (1–2 hrs)

**Description:**
Find and HTTP-validate the SideArm base URL for every remaining GAC school (22 programs:
14 men's + 10 women's — HU and OBU already done for both genders).

For each school, the SideArm schedule URL pattern is:
`https://[domain]/sports/[sport-slug]/schedule/[year]`

where sport-slug is typically `mens-soccer` or `womens-soccer`.

Known working examples:
- OBU men: `https://obutigers.com/sports/mens-soccer`
- Newman men: `https://newmanjets.com/sports/mens-soccer` (confirmed 200)
- FHSU men: `https://fhsuathletics.com/sports/mens-soccer` (confirmed 200)
- NSU men: `https://nsuathletics.com/sports/mens-soccer` OR `https://nsuriverhawks.com/sports/mens-soccer` (confirmed 200)
- Rogers State men: `https://rsuhillcats.com/sports/mens-soccer` (confirmed 200)

Schools needing URL discovery (try `/schedule/2024` to confirm):
- Arkansas Tech (ATU): try `atuwonderboys.com` or `atuathletics.com`
- Arkansas–Monticello (UAM): try `uambolls.com` or `uamathletics.com`
- East Central (ECU): try `ectigers.com` or `ecuathletics.com`
- Henderson State (HSU): try `hsuathletics.com` or `hsureddies.com`
- Northwestern Oklahoma State (NWOSU): try `nwoarengers.com`
- Oklahoma Baptist (OKBU): try `okbuathletics.com` or `okbusports.com`
- Southeastern Oklahoma State (SOSU): try `gosoutheastern.com` or `sosusavage.com`
- Southern Arkansas (SAU): try `saumuleriders.com` or `gomuleriders.com`
- Southern Nazarene (SNU): try `snustorm.com` or `snu.edu`
- Southwestern Oklahoma State (SWOSU): try `swosuathletics.com` or `goswosu.com`

For each school that resolves: test both men's and women's sport slugs.
Some schools may use `men%27s-soccer` or `soccer-m` — try variants if main slug 404s.

**Output:** Update `packages/pipeline/config/schools.toml` with ALL validated entries:
- All 14 remaining men's programs (12 full + 4 affiliates with years=2019–2025)
- All 10 remaining women's programs
- Set `enabled = true` only if URL validated 200
- Set `enabled = false` with `notes = "URL not found: [tried URLs]"` if can't resolve
- Set `gender` field on every entry
- Set `scraper = "sidearm"` on all new entries

**Acceptance Criteria:**
- `schools.toml` has entries for all 24 new programs
- All `enabled = true` schools have a URL that returns 200 for `/schedule/2024`
- `uv run python -c "from src.config import load_schools; e=[s for s in load_schools() if s.enabled]; print(f'{len(e)} enabled schools')"` prints ≥ 20
- Any school that couldn't be resolved has `enabled = false` with notes explaining what was tried

---

### eip-gac3 · Scrape: All men's programs (2016–2025)

**Type:** feature  
**Priority:** 2  
**Effort:** L (2–4 hrs, mostly runtime)

**Description:**
Run the scraper for all enabled men's GAC schools not yet scraped. This is mostly runtime —
the scraper infrastructure is already built and working.

Schools to scrape (all men's `enabled = true` from schools.toml after eip-gac2, excluding HU/OBU):
- 12 full members: ATU, UAM, ECU, HSU, NWOSU, OKBU, SOSU, SAU, SNU, SWOSU (women's affiliates excluded)
- 4 affiliate members: FHSU, NU, NSU, RSU (years 2019–2025 only)

Run command for each school:
```bash
cd packages/pipeline
uv run scrape --school [ABBR]
```

This scrapes all configured years for that school. Uses cache, so safe to re-run.

If a school fails or produces zero games for a year, log it and continue — don't block.
Partial data is better than no data.

After all schools scraped, run the merge:
```bash
uv run python -c "from src.storage import merge_all_schools, merge_all_seasons; merge_all_schools('men')"
```
(Note: if merge_all_schools doesn't support gender filter yet, just run the standard merge)

**Inputs:**
- Validated `schools.toml` from eip-gac2
- Working scraper infrastructure

**Outputs:**
- `packages/pipeline/data/structured/[abbr]/[year]/` parquet files for all men's schools
- `packages/pipeline/data/structured/all/` merged parquet files updated

**Acceptance Criteria:**
- Each enabled men's school has at least `data/structured/[abbr]/2024/games.parquet` present
- `uv run python -c "import pandas as pd; df=pd.read_parquet('data/structured/all/games.parquet'); print(df['home_team'].nunique() + df['away_team'].nunique(), 'unique teams')"` shows significantly more teams than current
- No unhandled exceptions — errors logged to `data/errors/` and scraper continues
- Commit: `data: scrape GAC men's programs 2016-2025`

---

### eip-gac4 · Scrape: All women's programs (2016–2025)

**Type:** feature  
**Priority:** 2  
**Effort:** L (2–4 hrs, mostly runtime)

**Description:**
Same as eip-gac3 but for women's programs. Run scraper for all enabled women's GAC schools
not yet scraped (i.e., everything except HUW and OBUW).

Women's full members to scrape (10 schools, excluding HUW/OBUW already done):
ATUW, UAMW, ECUW, HSUW, NWOSUW, OKBUW, SOSUW, SAUW, SNUW, SWOSUW

Run command for each school:
```bash
cd packages/pipeline
uv run scrape --school [ABBR]
```

**Inputs / Outputs / Acceptance Criteria:** Same pattern as eip-gac3 but for women's programs.
Women's teams should have data from 2016–2025.

Acceptance:
- Each enabled women's school has `data/structured/[abbr]/2024/games.parquet`
- Commit: `data: scrape GAC women's programs 2016-2025`

---

### eip-gac5 · Validate: Conference data completeness audit

**Type:** chore  
**Priority:** 3  
**Effort:** S (< 1 hr)

**Description:**
Run a completeness audit across all scraped data. Produce a summary report that answers:
1. Which schools scraped successfully vs failed?
2. How many games per school per year? (flag any school/year with < 8 games as suspicious)
3. Are yellow/red card events present? (expected only for 2020+ SideArm)
4. Any duplicate game_ids?
5. Total rows: games, player_stats, team_stats, events across all/games.parquet

Write the report to `docs/data-audit-[date].md`.

```python
# Key checks to run
import pandas as pd, glob

games = pd.read_parquet('data/structured/all/games.parquet')
player = pd.read_parquet('data/structured/all/player_stats.parquet')
events = pd.read_parquet('data/structured/all/events.parquet')

# Games per team per year
print(games.groupby(['season_year']).size())

# Duplicate game_ids
dupes = games[games.duplicated('game_id')]
print(f"Duplicate game_ids: {len(dupes)}")

# Event type distribution
print(events['event_type'].value_counts())

# Unique teams
all_teams = pd.concat([games['home_team'], games['away_team']]).unique()
print(f"Unique teams: {len(all_teams)}")
```

**Inputs:** All parquet files from eip-gac3 and eip-gac4

**Outputs:**
- `docs/data-audit-[date].md` with completeness report
- Any critical issues (duplicates, 0-game schools) fixed or noted

**Acceptance Criteria:**
- Audit report exists at `docs/data-audit-YYYY-MM-DD.md`
- ≥ 20 unique teams in `all/games.parquet`
- Zero duplicate game_ids
- Men's: at least 12 schools with 2024 data
- Women's: at least 10 schools with 2024 data
- Report committed: `docs: data completeness audit post-GAC scrape`
