# Spec: Fix SideArm Player Table Parser (Issue #9 / #11)

## Problem
`_parse_player_table()` in `packages/pipeline/src/sidearm_parser.py` uses hardcoded
positional `row.iloc[N]` to read column values. When a layout has a different column
count (e.g., no MIN column, or column order varies), it crashes:

```
IndexError: single positional indexer is out-of-bounds
  minutes=safe_int(row.iloc[7]),  ← line ~243
```

Affects 14 of 28 GAC programs. Those schools produce 0 parquet output.

## Root Cause
`_parse_player_table()` around line 205–247 uses:
```python
minutes=safe_int(row.iloc[7]),
shots=safe_int(row.iloc[3]),
shots_on_goal=safe_int(row.iloc[4]),
goals=safe_int(row.iloc[5]),
assists=safe_int(row.iloc[6]),
# and also:
pos_raw = str(row.iloc[0]).strip()
player_raw = str(row.iloc[2]).strip()
jersey = safe_int(row.iloc[1])
```

The confirmed player table column layout is:
`['Pos', '#', 'Player', 'SH', 'SOG', 'G', 'A', 'MIN']`

But some schools have layouts where MIN is absent or column order differs.

## Fix

Replace all positional `row.iloc[N]` in `_parse_player_table()` with column-name lookups.

### Helper to add (above `_parse_player_table`):
```python
def _get_col(row: pd.Series, *names: str, default: str = "") -> str:
    """Return first matching column value from row, or default."""
    for name in names:
        if name in row.index:
            return str(row[name])
    return default
```

### Updated `_parse_player_table` body:
Replace the positional lookups with:
```python
pos_raw   = _get_col(row, "Pos", "Position").strip()
player_raw = _get_col(row, "Player", "Name").strip()
jersey_raw = _get_col(row, "#", "No", "Jersey")
shots_raw  = _get_col(row, "SH", "Shots", "S")
sog_raw    = _get_col(row, "SOG", "Shots on Goal")
goals_raw  = _get_col(row, "G", "Goals")
assists_raw = _get_col(row, "A", "Assists")
minutes_raw = _get_col(row, "MIN", "Min", "Minutes", default="0")

jersey  = safe_int(jersey_raw)
minutes = safe_int(minutes_raw)
shots   = safe_int(shots_raw)
sog     = safe_int(sog_raw)
goals   = safe_int(goals_raw)
assists = safe_int(assists_raw)
```

Then use those variables in the `PlayerGameStats(...)` constructor.

## Files to Change
- `packages/pipeline/src/sidearm_parser.py` — only `_parse_player_table()` function

## Do NOT change
- Table classification logic (already works correctly via column signature sets)
- `_parse_scoring_summary`, `_parse_cautions_table`, `_parse_team_stats_table`
- Any other function

## After Fix: Re-scrape Failing Schools

Run from `packages/pipeline`:
```bash
for school in ATU ATUW ECU HSU HSUW NWOSU SAU SAUW SOSU SOSUW SWOSU UAM UAMW; do
    echo "Re-scraping $school..."
    uv run scrape --school $school
done
```

Note: NSU already works (had data). NWOSU (men's) uses `nwosu` abbreviation per config.

## Tests
- `uv run pytest tests/ -v` must pass (no regressions)
- Add a test fixture for the alternate layout (7-column table without MIN if possible,
  or at minimum verify existing tests still pass)
- After re-scrape: `python3 -c "import pandas as pd; df=pd.read_parquet('data/structured/atu/all/games.parquet'); print(len(df), 'ATU games')"` should show > 0

## Acceptance
- All 14 failing schools produce parquet files with > 0 games after re-scrape
- `uv run pytest tests/ -v` passes
- Existing schools (HU, OBU) still parse correctly
- Commit: `fix(pipeline): use column names instead of positional index in player table parser`
- Close GitHub issues #9 and #11
