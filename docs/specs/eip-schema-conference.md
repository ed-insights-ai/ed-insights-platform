# Spec: Add Conference/Opponent Schema Fields

**Feature:** Schema migration to support `is_conference_game`, opponent tracking, and `data_status` in school config
**ADRs:** ADR-006, ADR-005
**Bead prefix:** eip

---

## User Story

As a data consumer, I want to know whether each game was a conference game
(counts toward GAC standings) or an out-of-conference game, so I can filter
analytics to GAC-only matchups.

---

## Implementation Plan

### Task 1 — Migration: add `is_conference_game` and conference columns to `games`

File: `packages/pipeline/migrations/005_add_conference_fields.sql`

```sql
BEGIN;

ALTER TABLE games
    ADD COLUMN IF NOT EXISTS is_conference_game BOOLEAN DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS home_conference     VARCHAR(100) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS away_conference     VARCHAR(100) DEFAULT NULL;

COMMENT ON COLUMN games.is_conference_game IS
    'True if game counts toward conference standings. From SideArm is_conference flag.';
COMMENT ON COLUMN games.home_conference IS
    'Conference of the scraping school (always known from schools.conference).';
COMMENT ON COLUMN games.away_conference IS
    'Conference of opponent. NULL = unknown. Filled as opponent registry grows.';

COMMIT;
```

Also add to Alembic: `apps/api/alembic/versions/003_add_conference_fields.py`

### Task 2 — Create `opponents` reference table

```sql
BEGIN;

CREATE TABLE IF NOT EXISTS opponents (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL UNIQUE,
    abbreviation VARCHAR(20),
    conference   VARCHAR(100),
    division     VARCHAR(10),
    verified_at  TIMESTAMP DEFAULT NULL
);

COMMENT ON TABLE opponents IS
    'Reference table of opponent teams. Populated on scrape; conference/division filled over time.';

COMMIT;
```

### Task 3 — Update SQLAlchemy models in `apps/api/alembic/versions/`

Add `is_conference_game`, `home_conference`, `away_conference` to the `Game`
SQLAlchemy model in `apps/api/app/models.py`.

Add `Opponent` model:
```python
class Opponent(Base):
    __tablename__ = "opponents"
    id           = Column(Integer, primary_key=True)
    name         = Column(String(255), nullable=False, unique=True)
    abbreviation = Column(String(20))
    conference   = Column(String(100))
    division     = Column(String(10))
    verified_at  = Column(DateTime)
```

### Task 4 — Update pipeline `Game` dataclass

In `packages/pipeline/src/models.py`, add to `Game`:
```python
is_conference_game: bool | None = None
home_conference:    str | None = None
away_conference:    str | None = None
```

### Task 5 — Update `storage.py` to write new fields

Wherever a `Game` is inserted into Postgres, include the three new columns.
`home_conference` = the scraping school's `conference` from config (always "GAC" for now).
`is_conference_game` = from SideArm schedule data if available; NULL otherwise.
`away_conference` = NULL (future Phase 2).

### Task 6 — Update `schools.toml` schema in `config.py`

`packages/pipeline/src/config.py` — add `data_status: str = "unverified"` and
`notes: str = ""` to the `SchoolConfig` dataclass so the new toml fields don't
cause parse errors.

---

## Testing

- Migration runs cleanly on fresh DB: `docker compose up -d db && alembic upgrade head`
- Existing 30-game OBU dataset still loads: `SELECT count(*) FROM games` returns same count
- New columns exist and are nullable: `\d games` in psql
- `opponents` table exists and is empty (populated on next scrape)

## Acceptance Criteria

- [ ] Migration 005 runs without error
- [ ] `games` table has `is_conference_game`, `home_conference`, `away_conference`
- [ ] `opponents` table created
- [ ] SQLAlchemy models updated and tests pass
- [ ] `data_status` field in SchoolConfig doesn't break existing toml parsing
- [ ] 30/30 existing tests still pass

## Validation Commands

```bash
cd ~/source/ed-insights-platform
docker compose up -d db
cd apps/api && uv run alembic upgrade head
cd ../../packages/pipeline && uv run pytest tests/ -v
```

## Execution

```
Implement docs/specs/eip-schema-conference.md
```
