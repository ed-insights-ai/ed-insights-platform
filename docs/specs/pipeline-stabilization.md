# Pipeline Stabilization Spec

## Feature Description

Fix the highest-risk bugs in the data pipeline before building anything on top of this data. These are correctness issues — the data we have (2,855 games, 13 programs) has known corruption from unstable game IDs, inverted home/away flags, and brittle table classification.

## Problem Statement

Six issues identified in architecture review, prioritized by data correctness impact:

1. **Game IDs shift when schools.toml is reordered** (HIGH) — ordinal derived from array index
2. **Home/away is inverted on ~50% of games** (HIGH) — parser assumes first team = home, but SideArm lists the host school first regardless
3. **Table classification is case-sensitive** (HIGH) — one column name variant ("Sh" vs "SH") drops the entire table
4. **Stale directories from removed schools** (LOW) — 15 empty dirs under data/structured/ from schools that don't play GAC soccer
5. **README claims `uv run python -m src` works** (LOW) — no `__main__.py` exists
6. **`build_team_abbrev_map` hardcodes "HU": "Harding"** (LOW) — landmine for future StatCrew schools

## Codebase Analysis

### Current File Structure
```
packages/pipeline/
  src/
    config.py        — SchoolConfig + load_schools() (72 lines)
    models.py         — Game, TeamGameStats, PlayerGameStats, GameEvent dataclasses (90 lines)
    parser.py         — StatCrew parser (898 lines)
    sidearm_parser.py — SideArm parser (487 lines)
    discovery.py      — StatCrew URL discovery (62 lines)
    sidearm_discovery.py — SideArm URL discovery (79 lines)
    fetcher.py        — HTTP fetch + disk cache (45 lines)
    storage.py        — Parquet save/merge (132 lines)
  scripts/
    scrape.py         — CLI orchestrator (111 lines)
    load_db.py        — Parquet → PostgreSQL loader (485 lines)
    run.py            — Pipeline runner (156 lines)
    export.py, audit.py
  config/
    schools.toml      — 14 school entries (7 men's, 7 women's)
  tests/
    test_parser.py, test_sidearm_parser.py, test_game_id.py,
    test_discovery.py, test_storage.py
```

### Relevant Files for Each Fix

**Fix 1 — Stable game IDs:**
- `src/config.py` lines 52-53: `ordinal=idx` from `enumerate(data.get("schools", []), start=1)`
- `scripts/scrape.py` line 48: `game_id = school.ordinal * 1_000_000 + year * 100 + gu.game_num`
- `tests/test_game_id.py`: existing tests assert ordinals == range(1, N+1) — these tests must change
- `config/schools.toml`: needs explicit `ordinal` field on every entry

**Fix 2 — Home/away detection:**
- `src/sidearm_parser.py` lines 124-155: `_parse_score_table()` — `idx == 0` assumed home
- `src/sidearm_parser.py` lines 390-430: `parse_sidearm_game()` — builds Game with home/away from score table
- `src/parser.py` lines 490-510: `parse_game()` — uses `team1`/`team2` from goals-by-period table
- `scripts/scrape.py`: the `school` object is available — its `abbreviation` and `name` can be passed to parsers
- `src/models.py`: Game dataclass has `home_team`, `away_team`, `home_score`, `away_score`

**Fix 3 — Case-insensitive table classification:**
- `src/sidearm_parser.py` lines 46-48: `_PLAYER_COLS`, `_GOALIE_COLS`, `_SCORING_COLS` — all mixed-case
- `src/sidearm_parser.py` lines 51-83: `_classify_tables()` — `cols = set(str(c) for c in df.columns)` with exact superset match
- `src/parser.py` lines 64-107: `identify_table_type()` — already lowercases: `cols = {str(c).lower().strip() for c in df.columns}`

**Fix 4 — Stale directories:**
- `data/structured/` contains: atu, atuw, hsu, hsuw, sau, sauw, sosu, sosuw, uam, uamw, nwosuw, okbuw, swosuw — all empty
- Only dirs with actual data: hu, huw, fhsu, nu, obu, rsu, snu, ecu, ecuw, nwosu, okbu, obuw, snuw, swosu + the `all/` merged dir

**Fix 5 — README:**
- `README.md` line 14: `uv run python -m src` — no `src/__main__.py` exists
- Correct invocations: `uv run scrape`, `uv run pipeline-run`, `uv run load-db`

**Fix 6 — Hardcoded abbrev map:**
- `src/parser.py` line 203: `abbrev_map: dict[str, str] = {"HU": "Harding"}`

## Implementation Plan

### Task 1: Stable game IDs via explicit ordinal in schools.toml

**What:** Add `ordinal = N` to every `[[schools]]` entry in `schools.toml`. Change `load_schools()` to read it from TOML instead of deriving from enumerate index.

**Details:**
- In `config/schools.toml`, add `ordinal = N` to each entry. Assign values that match current enumerate order so existing data doesn't break:
  - HU=1, FHSU=2, NU=3, NSU=4, OBU=5, RSU=6, SNU=7, HUW=8, ECU=9, NWOSU=10, OKBU=11, OBUW=12, SNUW=13, SWOSU=14
- In `src/config.py`, change `ordinal=idx` to `ordinal=entry.get("ordinal", idx)` — reads from TOML, falls back to index for backwards compat
- Add a validation in `load_schools()`: after loading all schools, check for duplicate ordinals and raise `ValueError` if found
- Update `tests/test_game_id.py`:
  - Remove `test_ordinals_are_stable_and_positive` (no longer range-based)
  - Add `test_ordinals_are_explicit_and_unique` — verify every school has an ordinal, all unique
  - Add `test_ordinals_survive_reorder` — shuffle schools.toml entries, verify ordinals unchanged

### Task 2: Fix home/away detection in both parsers

**What:** Pass the scraping school's abbreviation and name into the parsers. Use it to determine which team is "us" (the school being scraped). The school's website always lists games from their perspective — cross-reference to correctly assign home/away.

**Details:**

For `sidearm_parser.py`:
- Change `parse_sidearm_game()` signature: add `school_abbrev: str = ""` and `school_name: str = ""` parameters
- After `_parse_score_table()` returns `home_team`/`away_team`, check: if the SideArm page title contains "vs" → the school is home (they host); if it contains "at" → the school is away
- Look for "vs" or "at" in the HTML `<title>` tag (already parsed in `_parse_header_metadata`). Pattern: "Men's Soccer vs Opponent" = home, "Men's Soccer at Opponent" = away
- If detected as away, swap home_team ↔ away_team, home_score ↔ away_score in the Game object
- Update `_parse_header_metadata()` to also return `is_home: bool | None` based on title "vs"/"at" detection

For `parser.py` (StatCrew):
- Change `parse_game()` signature: add `school_name: str = ""` parameter  
- After determining team names from the title regex `(.+?) vs (.+?)`, check: in StatCrew format, the title is "Home vs Away (date at venue)". Verify: if `school_name` matches team1, that's correct (home). If it matches team2, swap.
- This is less critical since StatCrew is only Harding and the format seems consistent, but adding the guard is cheap.

For `scripts/scrape.py`:
- Update `_scrape_season()` to pass `school.abbreviation` and `school.name` to both parsers
- Line 48: `result = parse_sidearm_game(html, game_id, gu.url, year, school_abbrev=school.abbreviation, school_name=school.name)`
- Line 50: `result = parse_game(html, game_id, gu.url, year, school_name=school.name)`

### Task 3: Case-insensitive table classification in sidearm_parser.py

**What:** Lowercase all column names before matching in `_classify_tables()`. Update signature constants to lowercase.

**Details:**
- Change `_PLAYER_COLS` to `{"pos", "#", "player", "sh", "sog", "g", "a", "min"}`
- Change `_GOALIE_COLS` to `{"position", "#", "goalie", "minutes", "ga", "saves"}`
- Change `_SCORING_COLS` to `{"time", "team", "description"}`
- In `_classify_tables()`, change: `cols = set(str(c).lower() for c in df.columns)`
- Update `"Statistic"` check to `"statistic"` and `"Team"` check to `"team"` and `"Type"` check to `"type"`
- In `_parse_player_table()`, column lookups via `_get_col()` already work by exact name — update the `_get_col` calls to use lowercase names: `_get_col(row, "pos", "position")`, `_get_col(row, "player", "name")`, etc.
- Actually: `_get_col` searches `row.index` which has the original (mixed-case) column names from the DataFrame. After lowercasing in `_classify_tables`, the DataFrames passed to `_parse_player_table` still have original columns. **Solution:** lowercase the DataFrame columns before appending to the classified result. Add `df.columns = [str(c).lower() for c in df.columns]` at the top of the loop in `_classify_tables`.
- Add test: `test_classify_tables_case_insensitive` — create a DataFrame with "SH", "Sh", "sh" variants, verify all classify as player stats

### Task 4: Clean up stale directories

**What:** Remove the 15 empty school directories from `data/structured/` that correspond to schools removed from `schools.toml`.

**Details:**
- Delete these empty dirs: `atu`, `atuw`, `hsu`, `hsuw`, `sau`, `sauw`, `sosu`, `sosuw`, `uam`, `uamw`, `nwosuw`, `okbuw`, `swosuw`
- Verify each is truly empty (no parquet files) before deleting
- The `all/` subdirs inside them are also empty

### Task 5: Fix README

**What:** Replace the broken `uv run python -m src` instruction with working commands.

**Details:**
Replace the Usage section with:
```markdown
## Usage

```bash
# Scrape all enabled schools
uv run scrape --all

# Scrape a single school
uv run scrape --school HU

# Full pipeline (scrape → load → export → audit)
uv run pipeline-run --all-enabled

# Load parquets into PostgreSQL (requires Docker)
uv run load-db

# Run tests
uv run pytest
```

### Task 6: Remove hardcoded abbrev map

**What:** Remove `"HU": "Harding"` default from `build_team_abbrev_map()`.

**Details:**
- `src/parser.py` line 203: change `abbrev_map: dict[str, str] = {"HU": "Harding"}` to `abbrev_map: dict[str, str] = {}`
- The function already builds abbreviations from team_names — the hardcoded entry is redundant when team_names includes "Harding"
- Verify by running existing StatCrew parser tests — Harding abbreviation should still resolve via the generation logic

## Testing Strategy

### Existing Tests (must all still pass)
- `tests/test_parser.py` — StatCrew parser
- `tests/test_sidearm_parser.py` — SideArm parser  
- `tests/test_game_id.py` — game ID collision (will be updated)
- `tests/test_discovery.py` — URL discovery
- `tests/test_storage.py` — parquet save/merge

### New Tests Required
1. **test_ordinals_explicit_and_unique** — all schools have ordinal, no duplicates
2. **test_ordinals_survive_reorder** — shuffling schools.toml entries doesn't change ordinals (mock test)
3. **test_classify_tables_case_insensitive** — column name variants all classify correctly
4. **test_home_away_sidearm_vs_keyword** — "vs" in title → home, "at" in title → away
5. **test_home_away_sidearm_swap** — when school is away, home/away fields are swapped correctly
6. **test_abbrev_map_no_hardcoded_harding** — verify Harding resolves without the hardcoded default

### Validation Commands
```bash
cd packages/pipeline
uv run pytest -v
# Expected: all existing + 6 new tests pass

# Verify no stale dirs remain
ls data/structured/ | sort
# Expected: all, ecu, ecuw, fhsu, hu, huw, nsu, nu, nwosu, obu, obuw, okbu, rsu, snu, snuw, swosu

# Verify ordinals are explicit
grep 'ordinal' config/schools.toml | wc -l
# Expected: 14
```

## Re-scrape Note

After fixes 1-3 are applied, **the existing parquet data should be re-scraped** to get correct game IDs and home/away assignments. However, since we have the HTML cache in `data/raw_html/`, re-scraping only re-parses cached HTML — no network calls needed. Run:
```bash
uv run scrape --all --use-cache
```

Then re-merge:
```bash
uv run pipeline-run --all-enabled --skip-load
```

## Acceptance Criteria

- [ ] Every school in schools.toml has an explicit `ordinal` field
- [ ] `load_schools()` reads ordinal from TOML, validates uniqueness
- [ ] Reordering schools.toml entries does not change any game_id
- [ ] SideArm parser correctly identifies home/away using "vs"/"at" in page title
- [ ] StatCrew parser cross-references school_name for home/away assignment
- [ ] `_classify_tables()` lowercases all column names before matching
- [ ] No stale empty directories under data/structured/
- [ ] README documents correct CLI commands
- [ ] `build_team_abbrev_map` has no hardcoded entries
- [ ] All existing tests pass
- [ ] 6+ new tests pass

## Execution

```bash
cd ~/source/ed-insights-platform && claude --dangerously-skip-permissions "Implement docs/specs/pipeline-stabilization.md"
```
