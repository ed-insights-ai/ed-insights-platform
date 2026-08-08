# ADR-008: Touchline — a Keelson rib as the season intelligence layer

**Date:** 2026-08-07
**Status:** Proposed

## Context

The 2026 D2 men's soccer season starts in late August. We want three things during
the season: data that stays fresh without anyone remembering to run a scrape, a
visual surface that tracks the conference week to week, and the ability to ask
questions in natural language.

[docs/UI_DESIGN.md](../UI_DESIGN.md) already anticipates all three as **Phase 5 —
AI**: LLM-generated insights, a text-to-SQL chat panel, match outcome predictions.
Phase 5 sits behind four phases of frontend work that will not complete before the
season starts.

[Keelson](https://github.com/danielscholl/keelson) is a local agent harness already
running on this machine. It provides persistent chat, provider routing, a workflow
engine with deterministic control flow, a browser UI with a snapshot bus, an MCP
endpoint, and a typed extension model called ribs. It provides no knowledge of
soccer. A rib is the seam for supplying that.

### What an investigation of the live system found

Before designing anything we read the pipeline, the API, the web app, the Keelson
harness and its four existing ribs, and queried the live `ed_insights` database.
Six findings reorder the priorities:

1. **`is_conference_game` is NULL for all 2,140 rows.** ADR-006 recorded this field
   as "populated from SideArm's `is_conference` flag. Reliable." In practice nothing
   populates it. Consequently `/api/conferences/{abbr}/standings`
   (`conferences.py:55-59`) applies no conference filter and returns an *overall*
   record labelled "standings".

2. **School identification fails open, inverting results.** `conferences.py:69` and
   `teams.py:79` both do `is_home = _matches_pattern(g.home_team, pattern)` and then
   read `own_score = g.home_score if is_home else g.away_score`. A *match failure* is
   therefore silently indistinguishable from "we are the away team," and the
   opponent's score is read as the school's own. `_ilike_pattern`
   (`conferences.py:14-21`, duplicated at `teams.py:14`) takes the first token of
   length ≥ 4 that is not a stop word, so "Oklahoma Baptist" becomes `%Oklahoma%`,
   which matches none of the 104 home games stored as "Okla. Baptist".

   Measured: **164 scored games** in which the pattern matches *neither* team slot,
   so the school cannot identify itself at all — OKBU 150/191, SWOSU 6/188,
   NWOSU 4/163, SNUW 2/171, OBU 1/173, SNU 1/179. The defect is overwhelmingly
   OKBU's; the others are a handful of games each, and FHSU and RSU are unaffected.

3. **176 duplicate `(date, home, away)` groups.** A fixture scraped from both schools
   becomes two rows. Every aggregate over the base tables is inflated.

4. **Two program-seasons are mislabelled — 42 rows.** FHSU's stored 2020 holds 24
   games dated 2025, and OBU's stored 2020 holds a further 18. `sidearm_discovery.py`
   fetches `/schedule/{year}` and never asserts the year segment of the paths that
   come back; when that year's page is absent the site serves the current season.
   All 42 rows carry `/stats/2025/` source URLs.

5. **Red cards are invisible outside Harding.** `sidearm_parser.py:339-348` hardcodes
   `yellow_card` for every caution row at the eleven SideArm programs. All 43
   `red_card` rows in the database are HU (41) and HUW (2).

6. **The database cannot answer a week-over-week question at any price.**
   `scripts/load_db.py:186-201` DELETEs then re-INSERTs every child row per
   `game_id` on each load. Last week's numbers are physically gone.

Finding 6 is structural rather than a bug, and it is the one that shapes the design.
Findings 1–5 mean a prettier dashboard over this data would be a downgrade.

### What Keelson can and cannot do

Verified against the harness source, not documentation:

- **There is no cron.** No `schedule:`, `cron:` or `every:` field in the workflow
  YAML schema; no `keelson schedule` command. Scheduled work is assembled from a
  30-second server heartbeat (which drives bound producers on a `cadenceMs` but
  always fires with empty inputs), a rib-held timer, and an OS-level fallback.
- **A rib can publish arbitrary sandboxed HTML** into a full-width drawer, as
  `keelson-rib-chamber` and `keelson-rib-squad` both do in production.
- **A workflow bash node is a subprocess** and cannot reach the snapshot manager,
  the rib context, or rib module state. In-process work must go through a tool.
- **`ctx.runWorkflow` does not publish to a bound snapshot key** — bindings are
  keyed by definition object identity, and it parses a fresh object. A refresh
  driven through it reaches the database and never reaches the screen.
  `ctx.refreshWorkflow(name)` is the correct seam.

## Decision

Build **Touchline**, a Keelson rib (`@keelson/rib-touchline`), as the season
intelligence layer for GAC soccer. Its structural commitment:

> Every refresh writes an **immutable Observation** — a JSON file holding the
> canonical conference table, per-team aggregates, per-player season lines, a
> `game_id → fingerprint` map, and provenance. Postgres remains the system of
> record for *detail*; the append-only observation ledger becomes the system of
> record for *time*.

Exactly one process reads Postgres on a schedule (`bin/observe.ts`). Every board,
every tool and every published page is a pure function over files on disk.

Three consequences follow from that one decision and are the reason for it:

| Capability | Why it becomes possible |
|---|---|
| "What changed since Sunday?" | A diff between two observation files |
| "Can I trust these numbers?" | Four of nine integrity checks compare two observations |
| "Show me the table as it stood Sep 6" | Read an older file |

**Shape: rib-only.** One Bun/TypeScript package exposing two Keelson surfaces,
twelve tools, six snapshot-bound board producers, and a family of per-subject HTML
canvas keys. The existing FastAPI service and Next.js app keep running and are left
alone; board rows deep-link into them at `localhost:3000`.

**Correctness before presentation.** The first board built is the one that names
which numbers are lying and cites the line that broke them. Designed HTML pages
come after scheduled ingest and chat are working.

**Two upstream fixes land in this repository**, because they are destructive rather
than merely wrong (see [touchline-rib.md](../specs/touchline-rib.md) Stage S0). The
remaining defects are routed around in the rib rather than patched.

## Consequences

**Good:**

- Week-over-week questions, time travel and trust checks become possible at all.
- Board collectors read files, never the database — fast, deterministic, testable,
  offline-capable, and cheap enough to tick on a heartbeat with no token cost.
- The rib is additive. Nothing in `apps/api` or `apps/web` changes; both keep working
  exactly as they do now, and gain a deep-link target rather than a competitor.
- Phase 5 of the UI plan arrives without waiting for Phases 1–4 of the UI plan.
- Chat, scheduled workflows, provider routing, persistence and a browser UI are all
  inherited from the harness rather than built.
- Registering tools once exposes them to Keelson chat, to workflow prompt nodes, and
  over MCP to Claude Code / Copilot / Codex.

**Bad:**

- A second place where conference logic lives. The canonical table computed by the
  rib and the table returned by `/api/conferences/{abbr}/standings` will disagree —
  correctly, but visibly — until the API is fixed or retired.
- A rib is not a sandbox. It runs in-process with the Keelson server and shells out
  to `uv run` in this checkout on a timer. A bug in the refresh workflow is a bug in
  the harness process.
- Rib activation is fail-hard: one out-of-namespace snapshot key or one duplicate
  surface id throws and fails the entire server boot, not just this rib.
- The Keelson board `chart` primitive uses a fixed six-colour series ramp assigned by
  index, so "teal is us" cannot survive into board charts. It survives everywhere
  else, and in the HTML pages where literal hex is available.
- Published HTML pages must be persisted to disk and re-registered at boot; the
  snapshot manager holds everything in memory and has no file IO.

**Out of scope (explicitly):**

- Any change to `apps/web`. The option to render Touchline boards there stays open at
  zero cost — `isAllowedOrigin` (`server-context.ts:13-23`) checks hostname only, so
  port 3000 already passes both CORS and the WebSocket upgrade gate — but it is not
  being built.
- Database views or any DDL against `ed_insights`. The rib stays read-only against a
  schema it does not own.
- Women's soccer for the 2026 season (see D-04 in the spec).
- Rewriting the SideArm legacy scraper for Northeastern State. Their conference record
  is reconstructed from opponents' box scores instead.

## Alternatives considered

**A rib plus a new `/touchline` route tree in `apps/web`.** The closest call. Rejected
on one measurement: reproducing Keelson's board renderer means `BoardView.tsx`
(1,308 lines) plus a hand-rolled chart section (337 lines) plus region chrome — work
that produces a second chrome for the same payload and no new capability. The bridge
costs nothing to defer, so the decision can be revisited once a season of data exists
to justify it.

**A cron entry plus more Next.js pages.** Yields fresher wrong data. It also does not
work as written: `uv run pipeline-run --school HU --year 2026` is a silent no-op at
the database layer, because `scrape.py:103` skips the per-school merge when only one
year is requested and `load_db.py:274-280` then reads the stale `all/` directory
forever.

**Database views as the correctness layer.** A view cannot be named `games` while the
table `games` exists, and `Game.__tablename__ = "games"` — so reading views would
require editing `models.py` and every query body. Creating objects in a database whose
alembic head (`005_reset_gac_schools`) deletes every row from all five data tables is
an ownership hazard a rib should not take.
