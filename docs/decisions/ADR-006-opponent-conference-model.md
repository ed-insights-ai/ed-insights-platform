# ADR-006: Opponent and Conference Data Model

**Date:** 2026-03-16
**Status:** Accepted — **partially superseded 2026-08-07 by
[ADR-008](ADR-008-touchline-keelson-rib.md)** on the provenance of `is_conference_game`.

> **Superseding note (2026-08-07).** Two statements below about SideArm's `is_conference`
> flag are false, and neither was ever implemented.
>
> - *"Each game has an `is_conference` boolean flag"* (Context) — the box score carries no
>   such per-game flag. The `is_conference` values present in cached SideArm pages belong to
>   a scoreboard sidebar widget, not to the game being parsed, and they are scrape-time
>   content: a page fetched for the 2016 season carries the same fixtures dated late 2025
>   that the 2025 file does.
> - *"`is_conference_game`: populated from SideArm's `is_conference` flag. Reliable."*
>   (Decision) — no file under `packages/pipeline/src` reads the flag. The column is NULL
>   for **2,140 of 2,140** rows and always has been.
>
> The field is instead **derived** from `schools.toml` GAC membership, gender-aware and
> season-aware, per [touchline-rib.md](../specs/touchline-rib.md) Stage S0.5 Task 1. A
> gender-blind derivation produces 103 false positives and must not be used.
>
> The rest of this ADR stands: `home_conference` is populated 2,140/2,140, `away_conference`
> is NULL 2,140/2,140 as designed, and the `opponents` table holds 0 rows as designed.

## Context

Every game has two teams. Our scrapers are school-centric — we scrape
Ouachita Baptist's schedule and capture 18 games. Each of those 18 games
includes an opponent (Centenary, Northeastern State, Dallas Christian, etc.)
who belongs to a conference we know nothing about from the boxscore alone.

Investigation of SideArm boxscores revealed:
- The home school's conference appears in analytics metadata (`"Conference": "Great American Conference"`)
- Each game has an `is_conference` boolean flag (whether it counts in GAC standings)
- The **opponent's conference is not present** in the boxscore HTML
- Opponents span many conferences: MIAA, SCAC, OAC, Frontier, independents, etc.

The temptation here is to chase every opponent conference and build a full
NCAA school registry. **We are not doing that now.**

## Decision

### Phase 1 (now): Capture what we have, mark what we don't know

**Schema additions to `games` table:**

```sql
ALTER TABLE games ADD COLUMN is_conference_game BOOLEAN DEFAULT NULL;
ALTER TABLE games ADD COLUMN home_conference     VARCHAR(100) DEFAULT NULL;
ALTER TABLE games ADD COLUMN away_conference     VARCHAR(100) DEFAULT NULL;
```

- `is_conference_game`: populated from SideArm's `is_conference` flag. Reliable.
- `home_conference`: populated from the scraping school's known conference (GAC). Always known.
- `away_conference`: NULL for all opponents until Phase 2. Explicitly unknown, not wrong.

**Add `opponents` reference table** (empty to start, filled over time):

```sql
CREATE TABLE IF NOT EXISTS opponents (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL UNIQUE,
    abbreviation VARCHAR(20),
    conference   VARCHAR(100),  -- NULL = unknown
    division     VARCHAR(10),   -- 'DI', 'DII', 'DIII', 'NAIA', NULL
    verified_at  TIMESTAMP      -- NULL = auto-populated, not manually verified
);
```

When scraping a game, look up the opponent name in this table. If missing,
insert with `conference = NULL`. This way `away_conference` in `games` can
be joined from `opponents` as data accumulates.

**Focus: GAC programs only.** For Phase 1, the only `away_conference`
values we care to populate are GAC teams playing each other. Those are
already known (all GAC members are in our `schools.toml`).

### Phase 2 (future, when expanding beyond GAC): NCAA school registry

When we add more conferences, introduce a proper school registry sourced
from the NCAA member directory. At that point:
- `opponents` table gets populated from the registry
- `away_conference` becomes reliable across the board
- A separate `conferences` table (id, name, abbreviation, division) normalizes the strings

Phase 2 is not scoped, not scheduled, and not a blocker for anything today.

## Consequences

**Good:**
- `is_conference_game` is immediately useful for filtering GAC-only analytics
- `opponents` table grows naturally as we scrape — no upfront work
- `away_conference = NULL` is honest; it won't pollute analytics with wrong data
- Clean upgrade path to Phase 2 — no breaking schema changes needed

**Bad:**
- OOC opponent conference is unknown for all non-GAC opponents (intentional, not a bug)
- Dashboard queries that want "conference breakdown of schedule" will show GAC + "Unknown"
  until Phase 2

**Out of scope (explicitly):**
- Tracking opponents outside GAC games
- NCAA school registry integration
- Conference membership history (teams that switched conferences)
- Non-DII programs (NAIA, DIII) — opponents may be these, we just mark them unknown
