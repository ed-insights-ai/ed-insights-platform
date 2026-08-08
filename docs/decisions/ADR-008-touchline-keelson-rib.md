# ADR-008: Touchline — a Keelson rib as the season intelligence layer

**Date:** 2026-08-07
**Status:** Proposed

## Context

The 2026 D2 men's and women's soccer seasons start in late August. We want three things
during the season: data that stays fresh without anyone remembering to run a scrape, a
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

1. **`is_conference_game` is NULL for all 2,140 rows — and is 100% derivable.**
   ADR-006 recorded this field as "populated from SideArm's `is_conference` flag.
   Reliable." Both halves are wrong. Nothing populates it — no file under
   `packages/pipeline/src` reads the flag at all — and the flag ADR-006 describes is not
   per-game data. **ADR-006 needs a superseding note.** `away_conference` is likewise NULL
   2,140/2,140. Consequently `/api/conferences/{abbr}/standings` (`conferences.py:67-76`)
   applies no conference filter and returns an *overall* record labelled "standings", and
   `insights.py:338` buckets every game as non-conference.

   The field derives cleanly from `schools.toml` GAC membership with no ambiguity — no
   opponent string resolves to two programmes. It must be derived **gender-aware**:
   measured, a gender-blind derivation produces **103 false positives**, because an
   institution that is a GAC member on one side often fields the other gender outside the
   conference.

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

3. **176 duplicate `(date, home, away)` groups — but only 98 are real duplicates, and
   they inflate almost nothing.** The 176 decompose exactly (measured 42+40+94): **42**
   involve a phantom 2020 row (finding 4), **40** are cross-*gender* collisions — a men's
   and a women's fixture on the same date between the same two institutions, genuinely
   distinct matches, **39 of the 40 with different scores** — and **94** are genuine
   cross-school perspectives. Put gender in the key and drop the phantoms and what remains
   is **98 groups, all of size 2, with zero score disagreement**.

   The claim this ADR originally made — "every aggregate over the base tables is
   inflated" — is **false**. No duplicate group shares both `school_id` and `season_year`
   (measured: 0), and every aggregate in `apps/api` filters or groups by `school_id`, so a
   fixture's second perspective belongs to the other school and never enters the first
   school's totals. The single exception is caused by the phantoms, not by duplication:
   `/api/stats/players` (`stats.py:131-136`) groups by `school_id` *without* `season_year`,
   so with no season filter 574 (player, school) rows carry doubled totals. Deleting the 42
   phantom rows removes it.

   These duplicate rows are also the dataset's only free correctness oracle — 493 fixtures
   scraped from two unrelated sites agree 493/493 on the score and 977/986 on all five team
   metrics. **Do not collapse them before the parsers are fixed.**

4. **Two program-seasons are phantom — 42 rows, all exact copies.** FHSU's stored 2020
   holds 24 rows and OBU's a further 18. `sidearm_discovery.py` fetches `/schedule/{year}`
   and never observes redirects; FHSU and OBU men's have no `2020` slug — their COVID
   season is slugged `2020-21` — so the request 302s to the bare `/schedule`, which serves
   the current season. All 42 rows carry `/stats/2025/` source URLs.

   They are not *mislabelled* — they are **exact duplicates of the same school's 2025
   rows**: measured, 42/42 have a 2025 twin matching on `source_url`, both team names and
   both scores, and the children match too. There is nothing to relabel and nothing to
   recover, so the repair is `DELETE`, not a re-scrape. `data/raw_html/fhsu/2020/` and
   `obu/2020/` are not empty either — 42 files, every one the 2025 season, FHSU's
   byte-identical by SHA-1 — and must be deleted alongside the rows or a cached re-scrape
   recreates them.

   The genuine 2020 seasons were played in **spring 2021** because of COVID; nine other
   programmes hold them correctly. FHSU's and OBU's are missing, not corrupt.

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

**Shape: rib-only.** One Bun/TypeScript package exposing three Keelson surfaces,
twelve tools, six snapshot-bound board producers per gender, and a family of per-subject
HTML canvas keys. The existing FastAPI service and Next.js app keep running and are left
alone; board rows deep-link into them at `localhost:3000`.

**Scope: both genders.** Seven men's and seven women's GAC programmes, on two `season`
surfaces (`season-men`, `season-women`) plus one shared `pressbox`. The spec's D-04
originally deferred women's soccer on the grounds that the identity defect was a
women's-side problem; per finding 2 that was measured against one of five matchers and is
false of the one `/api/stats/team` actually uses, under which the two worst-affected
programmes after the women's are men's (FHSU 12/150, RSU 47/132). The women's side is also
the larger half of the dataset — 1,238 rows against 902 — has zero phantom rows against 42,
one parse-failure blob against 33, and needs no NSU reconstruction. Every snapshot key,
board collector and conference derivation is gender-aware; a gender-blind conference
derivation produces 103 false positives.

A single toggled surface was rejected on a hard constraint, not preference:
`deriveSurfaceSchedules` (`scheduler.ts:63-68`) skips any `workflowArgs`-bearing region, so
a toggled board would never refresh on the server heartbeat.

**Correctness before presentation.** The first board built is the one that names
which numbers are lying and cites the line that broke them. Designed HTML pages
come after scheduled ingest and chat are working.

**Two upstream fixes land in this repository**, because they are destructive rather
than merely wrong (see [touchline-rib.md](../specs/touchline-rib.md) Stage S0), and a
data-repair pass follows them in Stage S0.5 (spec D-03, revised): fix the title date regex
and home/away in both parsers, delete the 42 phantom rows and their cache directories,
backfill `is_conference_game` gender-aware, correct the SideArm roster-label swap and the
red-card type, and add a gender-bearing canonical match key.

The ground-truth audit established the fact that makes this affordable: **every defect is a
parser or loader bug, and every one is fixable from the 1.1 GB of cached HTML already on
disk.** Re-parsing all 2,140 box scores reproduces every stored number exactly, so nothing
requires a re-scrape or a network request. Only the five `apps/api` team-name matchers are
routed around in the rib rather than patched.

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
- Home/away splits on any board for v1. `home_team` is fabricated in all 2,140 rows and is
  correct in only 37% of SideArm games; it is recoverable offline from the source venue, but
  until that repair lands no board presents a home/away breakdown.
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
