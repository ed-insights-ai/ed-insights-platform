# Spec: SideArm Sports Scraper Adapter

## Feature Description
Add a SideArm Sports scraper adapter to the pipeline so we can ingest game data from OBU (Ouachita Baptist) and other GAC schools that use SideArm. SideArm serves static HTML box scores — no JS rendering needed.

## Problem / Solution
The current pipeline only handles StatCrew HTML (Harding format). SideArm uses a different URL pattern and HTML table structure. We need a new adapter that plugs into the existing pipeline architecture.

## Codebase Analysis Findings

### SideArm Discovery (confirmed working)
- Schedule URL: `https://obutigers.com/sports/mens-soccer/schedule/{year}`
- Boxscore links in schedule page: `href="/sports/mens-soccer/stats/{year}/{opponent}/boxscore/{id}"`
- Pattern: `re.findall(r'/sports/mens-soccer/stats/\d+/[^/]+/boxscore/\d+', html)`
- 2025: 18 games found. 2024: 18 games found.
- Full URL: `https://obutigers.com{path}`

### SideArm Box Score Structure (confirmed via OBU 2025 game #6126)
Table layout (10 tables total):
- Table 0: Team score by period (`Team | 1 | 2 | Total`)
- Table 1: Scoring summary (`Time | Team | Description`)
- Table 2: Cautions and ejections (`Time | Team | Type | Player`)
- Table 3: Team statistics (`Shots | Saves | Corner Kicks | Fouls`)
- Table 4: Home team player stats (`Pos | # | Player | SH | SOG | G | A | MIN`)
- Table 5: Home team goalie stats
- Table 6: Away team player stats
- Table 7: Away team goalie stats
- Tables 8-9: Additional (duplicates/extra)

Player stats format: `DEF 3 3 Lovoy, James 2 1 1 0 90` (pos, jersey, num, name, sh, sog, g, a, min)
Name format: `Last, First` (reversed from StatCrew)

### Existing Pipeline Architecture
- `src/config.py` — `SchoolConfig` with `base_url`, `prefix`, `ordinal` + `build_game_url()`
- `src/discovery.py` — `discover_season_games()` uses sequential probing (StatCrew-specific)
- `src/fetcher.py` — `GameFetcher` with caching (reusable as-is)
- `src/parser.py` — StatCrew-specific HTML parser (898 lines), returns `ParsedGame`
- `src/models.py` — `Game`, `TeamGameStats`, `PlayerGameStats`, `GameEvent`, `ParsedGame`
- `src/storage.py` — saves to parquet (reusable as-is)
- `scripts/scrape.py` — orchestration script

### Key Difference: Discovery
StatCrew: sequential probe `hu-01.htm`, `hu-02.htm`, stop at 404/empty
SideArm: scrape schedule page → extract all boxscore links → fetch each

## Implementation Plan

### Phase 1: SideArm Discovery
**File: `src/sidearm_discovery.py`** (new)
```python
def discover_sidearm_season(year: int, base_url: str) -> list[GameURL]:
    """Fetch schedule page and extract all boxscore URLs."""
    # base_url = "https://obutigers.com/sports/mens-soccer"
    # GET {base_url}/schedule/{year}
    # Extract: re.findall(r'/sports/mens-soccer/stats/\d+/[^/]+/boxscore/\d+', html)
    # Return GameURL(year=year, game_num=i+1, url=f"https://obutigers.com{path}")
```

### Phase 2: SideArm Parser
**File: `src/sidearm_parser.py`** (new)
Parse the 10-table SideArm box score HTML. Returns same `ParsedGame` model.

Key parsing tasks:
1. **Score**: Table 0 — extract home/away team names and final score
2. **Team stats**: Table 3 — shots, saves, corners, fouls (both teams)
3. **Player stats**: Tables 4+6 — Pos, #, Name, SH, SOG, G, A, MIN; starters vs subs
4. **Events**: Table 1 — time, team, description (parse goal scorer + assist from description)
5. **Cautions**: Table 2 — yellow/red cards
6. **Venue/date**: Parse from page `<h1>` or metadata near score table
7. **Name normalization**: SideArm uses "Last, First" → convert to "First Last"

Parser must return the same `ParsedGame` dataclass as the StatCrew parser.

### Phase 3: SchoolConfig adapter field
**File: `src/config.py`** — add `scraper: str = "statcrew"` field to `SchoolConfig`
Values: `"statcrew"` | `"sidearm"`

### Phase 4: schools.toml — enable OBU
```toml
[[schools]]
name          = "Ouachita Baptist"
abbreviation  = "OBU"
conference    = "GAC"
mascot        = "Tigers"
prefix        = "obu"
base_url      = "https://obutigers.com/sports/mens-soccer"
years         = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
enabled       = true
scraper       = "sidearm"
```

### Phase 5: Update scrape.py orchestration
**File: `scripts/scrape.py`** — route to correct discovery + parser based on `school.scraper`:
```python
if school.scraper == "sidearm":
    urls = discover_sidearm_season(year, base_url=school.base_url)
    result = parse_sidearm_game(html, game_id, url, year)
else:  # statcrew (default)
    urls = discover_season_games(year, ...)
    result = parse_game(html, game_id, url, year)
```

### Phase 6: DB seed — add OBU school
**File: `packages/pipeline/migrations/004_add_obu_school.sql`** (new)
```sql
INSERT INTO schools (name, abbreviation, conference, mascot)
VALUES ('Ouachita Baptist', 'OBU', 'GAC', 'Tigers')
ON CONFLICT (abbreviation) DO NOTHING;
```

### Phase 7: Tests
**File: `packages/pipeline/tests/test_sidearm_parser.py`** (new)
- Fixture: save `/tmp/obu_boxscore.html` as `tests/fixtures/sidearm_boxscore_6126.html`
- Test: parse fixture → verify score 2-1, OBU wins, goal scorers, player stats
- Test: name normalization "Last, First" → "First Last"
- Test: cautions parsed correctly

## Step-by-Step Tasks
1. Create `tests/fixtures/sidearm_boxscore_6126.html` (copy from /tmp/obu_boxscore.html)
2. Create `src/sidearm_discovery.py` with `discover_sidearm_season()`
3. Create `src/sidearm_parser.py` with `parse_sidearm_game()` returning `ParsedGame`
4. Add `scraper: str = "statcrew"` field to `SchoolConfig` in `src/config.py`
5. Update `schools.toml` — enable OBU with `scraper = "sidearm"`, add OBUW entry (disabled, needs research)
6. Update `scripts/scrape.py` to route by `school.scraper`
7. Create `migrations/004_add_obu_school.sql`
8. Write tests in `test_sidearm_parser.py`

## Testing Strategy
- Offline: fixture HTML file for parser tests (no network)
- Online integration: `uv run scrape --school OBU --year 2025` should find 18 games
- Validation: run `uv run pytest tests/` — all existing tests must still pass

## Acceptance Criteria
1. `uv run scrape --school OBU --year 2025` completes, produces parquet with 18 games
2. `uv run load-db --school OBU` loads OBU data into DB without errors
3. OBU appears in the dashboard school selector alongside HU/HUW
4. `uv run pytest tests/` passes (including new sidearm tests)
5. Existing HU/HUW scraping unaffected

## Validation Commands
```bash
cd packages/pipeline
uv run pytest tests/ -v
uv run scrape --school OBU --year 2025 --verbose
uv run load-db --school OBU --dry-run
```

## Notes
- OBU women's (`OBUW`) uses `https://obutigers.com/sports/womens-soccer` — same SideArm format. Add as disabled entry, enable after men's confirmed working.
- Years 2016-2019 need verification — older SideArm pages may differ. Start with 2024-2025.
- The game_id for OBU will be `3 * 1_000_000 + year * 100 + game_num` (ordinal=3)

## Execution Command
```
Implement docs/specs/sidearm-scraper-adapter.md
```
