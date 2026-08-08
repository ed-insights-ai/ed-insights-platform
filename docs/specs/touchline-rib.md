# Spec: Touchline — Keelson Rib for GAC Season Intelligence

**Feature:** A Keelson rib that keeps GAC soccer data fresh on a schedule, renders the
season as live boards and published pages, and answers questions in natural language
**ADRs:** [ADR-008](../decisions/ADR-008-touchline-keelson-rib.md) · corrects an
expectation in [ADR-006](../decisions/ADR-006-opponent-conference-model.md) · depends on
[ADR-007](../decisions/ADR-007-gac-school-membership.md)
**Bead prefix:** tl
**Package:** `@keelson/rib-touchline`
**Repository:** `github.com/ed-insights-ai/keelson-rib-touchline` — **must** be created under
the `ed-insights-ai` organization, not a personal account, like every other repo in this
body of work. Local checkout path is incidental (`~/source/keelson/keelson-rib-touchline`
is fine) as long as `origin` points at the org.

---

## User Story

As someone following a live D2 soccer season, I want the data to refresh itself as
results land, a surface that shows me what moved since I last looked, and the ability
to ask "are we going to make the tournament" and get an answer grounded in numbers I
can trust — without opening a terminal or remembering to run anything.

---

## Problem Statement

Three capabilities are missing, and one of them is structural.

**1. Nothing refreshes on its own.** `uv run scrape` is manual. During a season with
midweek and Saturday fixtures, data goes stale between the times someone remembers.

**2. The data is wrong in five named, reproducible ways.** All verified against the
live `ed_insights` database, not inferred:

| # | Defect | Evidence | Cause |
|---|--------|----------|-------|
| 1 | Conference play unmarked | `is_conference_game` NULL for **2140/2140** rows | Nothing populates it; `conferences.py:55-59` therefore returns an *overall* record labelled "standings" |
| 2 | Five schools' records inverted | NWOSU 0/163 games matched, SWOSU 2/188, FHSU 12/150, OKBU 41/191, RSU 47/132 | `_ilike_pattern` duplicated at `conferences.py:14-21` and `teams.py:14` reduces "Oklahoma Baptist" → `%Oklahoma%`, missing the 104 home games stored as "Okla. Baptist". Failed match ⇒ opponent's score read as theirs |
| 3 | Matches double-counted | **176** duplicate `(date, home, away)` groups | One fixture scraped from both schools; no canonical match key exists |
| 4 | Season labels wrong | FHSU's stored **2020** season holds 24 games dated 2025-09-04 … 2025-12-12 with `/stats/2025/` source URLs | `sidearm_discovery.py:42` fetches `/schedule/{year}` with no assertion; the site serves the current season when that year's page is absent |
| 5 | Red cards invisible outside Harding | All **43** `red_card` rows are HU (41) + HUW (2) | `sidearm_parser.py:339-348` hardcodes `yellow_card` for every caution row at the eleven SideArm programs |

**3. The database has no memory.** `scripts/load_db.py:186-201` DELETEs then re-INSERTs
every child row per `game_id` on each load. Last week's numbers are physically gone, so
week-over-week comparison, "what moved since Saturday", and any check that watches for
data *changing* are impossible against Postgres at any price.

Defect 3 is the reason for the central design decision. Defects 1–5 are the reason
correctness is sequenced before presentation.

---

## Decisions

Adopted as the plan's baseline. Each carries the condition that would reopen it.

### D-01 — Fat ledger

**Decision:** An Observation stores full per-match box lines, not just derived season
state. Estimated ~2 MB per observation, ~55 MB for a season.

**Rationale:** A thin ledger (~200 KB) makes "show me the Sep 6 table" work but leaves
"what did we think that match's shot count was on Sep 6" unanswerable, and limits the
score-mutation check to scores only — silent shot-count corrections would pass. 55 MB
is not a constraint on any machine we care about, and the checks we cannot imagine yet
are the ones we will want in October.

**Revisit if:** observation write time exceeds ~10s, or a collector's read time becomes
visible in board latency.

### D-02 — Correctness before presentation

**Decision:** The integrity board (S2) ships before any designed HTML page (S6).

**Rationale:** An LLM narrator over inverted records is worse than no narrator. The
counter-argument — that a product nobody enjoys opening dies regardless of correctness
— is real, and is why the *boards* land at S3, well before S6. What is deferred is the
broadsheet, not the visual surface.

**Revisit if:** the boards at S3 turn out to be unsatisfying enough that motivation
becomes the binding constraint.

### D-03 — Repair the data we have, not just the data we will get

**Revised 2026-08-07.** The original decision was "fix the destructive bugs upstream,
route around the rest," treating the rib's canon as a read-time overlay over corrupt
data. That is not sufficient. The dataset itself must be correct.

**Decision:** Three parallel tracks, all before the rib depends on any of them.

| Track | Scope | Where |
|---|---|---|
| **Prevent** | Season assertion, merge safety, tests | S0, this repo |
| **Repair** | Re-scrape mislabeled seasons, backfill `is_conference_game`, establish a canonical match key and reconcile the 176 duplicate groups | S0.5, this repo |
| **Resolve** | Identity across name variants, at read time, for anything the repair pass cannot collapse | `src/canon.ts` in the rib |

The canon still exists — free-text opponent strings will keep arriving from thirteen
independently-formatted sites, so read-time resolution is permanent infrastructure. But
it is no longer carrying corruption that could have been fixed at the source.

**Rationale:** A read-time overlay means every consumer that is not the rib —
`apps/api`, `apps/web`, any notebook, any future tool — still sees the wrong numbers.
`is_conference_game` NULL for 2140/2140 rows is not a rendering problem; it is a field
nobody populated. FHSU's 2020 season holding 2025 games is not a display bug; it is 24
rows attributed to the wrong year. Those are cheaper to fix once in the data than to
compensate for forever in every reader.

**Still routed around, deliberately:** the red-card `Type` column
(`sidearm_parser.py:339-348`) needs parser work across eleven programs and would require
a full re-scrape to backfill — S9. Replacing `_ilike_pattern` in `apps/api` has its own
blast radius and is separate work.

**Revisit if:** the repair pass reveals that a defect can only be fixed by re-scraping
history we cannot reliably re-fetch, in which case the canon absorbs it and the integrity
board reports it permanently.

### D-04 — Men's soccer only for 2026

**Decision:** One gender. Region keys are `rib:touchline:table` and friends, unqualified.

**Rationale:** A Keelson surface declares *static* region keys, so a board is men's or
women's, never both. The alternatives are a hidden mode toggle — which means the boards
silently mean something different depending on a setting you cannot see — or doubling
every region, which puts fourteen regions on one surface. Deciding out loud costs
nothing and can be undone.

**Note:** this is where the canon would pay off most. The four schools with the worst
identity defects — NWOSU 0/163, SWOSU 2/188, OKBU 41/191 — are all women's programs.

**Revisit if:** the canon work in S1 proves cheap enough that doubling the regions costs
under a day, or after the 2026 season closes.

### D-05 — Ship both the in-process timer and the launchd fallback

**Decision:** `src/wallclock.ts` (a `setInterval` inside the rib) *and* a launchd plist,
from the start.

**Rationale:** They converge on the same code path — both reach `startRun` and both
publish the bound key — so the fallback is nearly free. The timer is what makes matchday
awareness possible: a plist cannot read the fixture calendar and decide it should poll
every thirty minutes tonight. The plist is what survives a sleeping laptop.

**Revisit if:** the timer proves unstable in-process, in which case launchd becomes
primary and matchday polling moves to a fixed window.

### D-06 — Seven programs, conference scope only

**Decision:** Northeastern State appears in the table, reconstructed from the box scores
of the six schools they played, carrying a `via opponents` badge. The table is labelled
conference-only.

**Rationale:** `schools.toml` declares seven men's GAC programs; NSU is `enabled=false`
only because their site is a KnockoutJS SPA with no scraper. Every box score records
both rosters, so their *conference* record is exactly recoverable. Publishing a six-team
table as a conference table is precisely the error we convict the existing product of.
The reconstruction is genuinely lossy for their *overall* record — matches against
non-GAC opponents nobody else played are invisible — which is why the scope is stated
rather than implied.

**Revisit if:** the legacy scraper gets written (S9).

### D-07 — Deterministic delta register in v1; generated prose deferred

**Decision:** The "since you last looked" register is computed from the observation diff
— always true, zero tokens. The narrator ships with the Dispatch at S6, not before.

**Rationale:** The delta lines are the part that tells you something you did not already
know. The generated prose largely restates them at greater length. Shipping the
deterministic half first tests whether the narrator is adding anything at all.

**Revisit if:** after a month in season the register reads as a changelog rather than a
briefing — which would be the argument for prose.

### D-08 — No `/touchline` route tree in `apps/web`

**Decision:** Not built. The bridge stays open at zero cost.

**Rationale:** `isAllowedOrigin` (`server-context.ts:13-23`) checks hostname only, never
port, so port 3000 already passes CORS and the WebSocket upgrade gate. Every board is
readable from the Next app over `GET /api/snapshots/:key` whenever we want it. Building
it now means reproducing `BoardView.tsx` (1,308 lines) plus a chart section (337 lines)
plus region chrome — a second chrome for the same payload and no new capability.

**Revisit if:** after a season, the things a board genuinely cannot do — sparklines
inside table rows, a nine-axis radar, a URL per entity you can text someone — turn out
to matter more than they appear to now.

### D-09 — Content-derived `game_id`, deferred to S8

**Decision:** Hash `(ordinal, year, the site-unique numeric id already in every
`/boxscore/13656` URL)` instead of `enumerate()` position. Not in S0, because it
rewrites every existing id and needs a one-time full reload.

**Rationale:** `sidearm_discovery.py:73-75` assigns `game_num` from enumerate position
over schedule-page links, so one late-published box score shifts every subsequent id —
creating fresh rows via `ON CONFLICT` (no conflict fires) and orphaning the old ones.
This will happen at least once this season. The canon means boards never double-count
when it does, and the stability check alarms with the affected program named, so the
rib is safe in the meantime. The alternatives — a sweeper deleting ids absent from the
last two observations, or a soft-delete column — are respectively destructive in a
database we do not own and an alembic ownership problem.

**Revisit if:** orphan accumulation becomes visible to anything reading base tables
outside the canon before S8 arrives.

---

## Architecture

One-way flow. Nothing reads backwards.

```
13 school athletics sites (SideArm SSR · StatCrew static)
      │  uv run scrape --year 2026 --no-cache        [bash node, cd $TOUCHLINE_PROJECT]
      ▼
data/structured/{school}/{year}/*.parquet
      │  merge_all_seasons(FULL_YEAR_LIST, abbrev) per school → merge_all_schools()
      ▼
data/structured/all/  →  uv run load-db
      ▼
┌──────────────────────────────────────────────────────────────┐
│  POSTGRES  ed_insights @ localhost:5432 (lume)                │
│  system of record for DETAIL — read ONCE per refresh          │
└──────────────────────────────────────────────────────────────┘
      │  bin/observe.ts — the only scheduled reader of Postgres
      │  applies canon.json → canonical matches, is_own resolution,
      │  derived table + aggregates, game_id→fingerprint map
      ▼
┌──────────────────────────────────────────────────────────────┐
│  THE OBSERVATION LEDGER   <dataHome>/                         │
│  system of record for TIME — append-only, immutable           │
│    observations/2026-09-13T06-04-11Z.json                     │
│    canon.json · pages/<key>.html · watermark.json             │
└──────────────────────────────────────────────────────────────┘
      │                    │                     │
      │ bin/collect-*.ts   │ in-process          │ touchline_* tools
      │ (bash, files only) │ sm.register()       │ (files; only _query hits PG)
      ▼                    ▼                     ▼
 6 BOUND PRODUCERS    Matchday composer     chat · MCP · prompt nodes
      │                    │
      ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│  KEELSON SNAPSHOT BUS → WebSocket → SPA                       │
│  rib:touchline:{table,race,slate,form,feed,ledger,matchday}   │
│  rib:touchline:match:<canonKey>      ← html, per subject      │
│  rib:touchline:dispatch:<season>-wNN ← html, per matchweek    │
└──────────────────────────────────────────────────────────────┘
```

`apps/api` and `apps/web` keep running untouched. Every board row carries an `href` to
`http://localhost:3000/explore/teams/{abbr}` or `/dashboard/games/{id}`.

---

## Component Inventory

| Component | Role | Copy from |
|---|---|---|
| `src/index.ts` | The Rib literal — id, mutable `RIB_VIEWS`, 2 surfaces, `contributeWorkflows`, `registerTools`, `onAction`, commands, agents, `authStatus`, `dispose` | `keelson-rib-chamber/src/index.ts`; package skeleton verbatim from `keelson-rib-workiq` |
| `src/ledger.ts` + `bin/observe.ts` | **The spine.** Only scheduled reader of Postgres. Writes one immutable observation via temp-write + rename | `chamber/src/room-store.ts:70-169` (atomic write, tolerant parse) |
| `src/canon.ts` + `canon.json` | **Correctness floor.** Identity keyed on *abbreviation*, never name — the live `schools` table has two rows named "Harding" (HU id=3, HUW id=10). Collapses the 176 duplicate groups; derives `is_conference_game`; resolves 9,781 player-name strings across `Last, First` and `First Last` forms; allocates identity hues | Replaces `_ilike_pattern` (`conferences.py:14-21`, `teams.py:14`) and the `.find()` at `insights.py:63` |
| `src/integrity.ts` | Nine named checks, each returning verdict + evidence + causing `file:line` + remedy | — |
| `src/wallclock.ts` | Rib-held scheduler. `setInterval(60_000).unref()`, slot table against local time, `last-fired.json`, matchday awareness, hard in-flight guard | Calls `ctx.refreshWorkflow` (`shared/src/rib.ts:324`) |
| `bin/collect-*.ts` (×6) | Deterministic board collectors. Read observation files, print one board JSON. No LLM, no DB, no network | `chamber/bin/collect-roster.ts`; binding shape from `rib-osdu/src/index.ts:437-452` |
| `src/pages.ts` + `src/tools/emit.ts` | In-process publish seam. Writes HTML to disk **before** registering the key; re-registers at boot | `chamber/src/tools/lens-emit.ts:280-295`, `lens-html.ts:123-175` (`reregister`) |
| `src/broadsheet.ts` / `src/matchpage.ts` | Deterministic HTML builders — pure functions from observation rows to a styled page. Every colour through a CSS custom property | `squad/src/report.ts` |
| `src/gates.ts` | Watermark gate (has anything landed since you last looked) + fingerprint gate (did the table actually move) | `chamber/src/workflows.ts:193-233` |
| `src/sim.ts` | Season Monte Carlo — 50k remainders, empirical-Bayes-shrunk Poisson rates, swing ranking | New |
| `src/keys.ts` | Single source of truth for every snapshot key. Activation is fail-hard: one out-of-namespace key throws and fails server boot | — |

---

## Tool Inventory

Ten of twelve are `state_changing: false` and therefore reach MCP by default.

| Tool | Answers |
|---|---|
| `touchline_diff` | **Signature tool.** What changed between two observations. Zero-argument default = the two newest |
| `touchline_table` | The canonical conference table, with `asOf` for any past observation |
| `touchline_match` | One canonical match with every source perspective + per-metric disagreement report |
| `touchline_team` | A program's season: record, five team metrics with conference percentiles, form, home/away split, minutes load |
| `touchline_player` | One player across seasons, fuzzy-resolved through the canon |
| `touchline_head_to_head` | Full record between two programs, 2016–2026 — impossible today (the `opponents` table has 0 rows) |
| `touchline_clock` | Goal/card/sub distribution over the match clock. **22,754 of 22,754 clocks parse**; conference goals bucket 1019/993/991/1262/1223/1261 with 115 past the 90th. No endpoint has ever aggregated `game_events` |
| `touchline_race` | Monte Carlo odds, modal seed, magic/tragic numbers, swing ranking. Accepts `assume: ["HU>SNU"]` |
| `touchline_integrity` | The nine checks with evidence and causing `file:line` |
| `touchline_query` | Guarded read-only SQL with the canon injected as a CTE prelude. One SELECT, implicit LIMIT 500, 10s timeout |
| `touchline_refresh` | Kick ingest now. Durable op via `ctx.registerOp`; dry-run plan without `confirm` |
| `touchline_emit_page` | **The in-process write seam.** Runs the forbidden-metric gate and the palette validator, writes to disk, registers the key, declares the view |

---

## Workflow Inventory

| Workflow | Trigger | Notes |
|---|---|---|
| `touchline-refresh` | Wall clock (Sun/Wed 06:00, Sat 22:00, Fri 16:00 check-only, matchday 20:00–23:59 every 30m); the `touchline_refresh` tool; the Feed Health `[Pull now]` action; launchd | 7 nodes: preflight → scrape → merge → load → observe → verify (`always_run`) → publish (`trigger_rule: all_done`). Bound to `rib:touchline:feed`. **No** `cadenceMs` on its region, so the 30s heartbeat never schedules a 3-minute scrape. No approval node and no `memory:` block — both would break headless runs |
| `touchline-{table,race,slate,form,feed,ledger}` | Server heartbeat via region `cadenceMs` | One contribution binding **one** key with its **own** name. `deriveSurfaceSchedules` refuses to schedule a region whose workflow publishes to a different key — the failure mode is a panel that looks fine and goes permanently stale |
| `touchline-dispatch` | Chained after a successful Sunday refresh; `/dispatch`; a board action | gate (bash, free) → author (prompt, `when: dirty == 'true'`, tool whitelist) → publish (`all_done`). Deliberately **not** on a cadence — the author node buys a turn |
| `touchline-scout` | `/scout <abbr>`; the Slate card action; Thursday 17:00 | Four parallel prompt nodes → compose → emit HTML brief |
| `touchline-retry-errors` | Feed Health `[Retry]`; monthly | The 34 orphaned blobs in `data/errors/` are invisible to every consumer today; this turns them into a work list |

---

## Surface Inventory

Two Keelson surfaces (top-level nav tabs).

**`season`**

| Region | Key | Cadence | Shows |
|---|---|---|---|
| Matchday (header) | `matchday` | in-process | Record pulse, five tiles, "since you last looked" delta register, last results, next three, actions |
| The Table | `table` | 15m | Conference table, seven programs, form strips, Δ vs a named prior observation, honest caption |
| Race | `race` | 60m | Odds bars, three delta tiles, "the four results that matter most" |
| The Slate | `slate` | 15m | Results matrix (doubles as a scrape-gap detector), this weekend's cards |
| Form & The Clock | `form` | 15m | Hot/cold, goal-timing segments, boot race, minutes-load fatigue table |

**`pressbox`**

| Region | Key | Cadence | Shows |
|---|---|---|---|
| Feed Health (header) | `feed` | none (bound to refresh) | Four tiles, the nine checks with evidence, per-program grid, actions |
| Observation Ledger | `ledger` | 60m | Last twenty observations, cumulative-matches staircase (a flat step = a failed refresh), diff-two-observations |
| Archive | — | — | Every published page as a card; matchweek strip showing gaps |

**HTML canvas keys** (full-width sandboxed drawer): `match:<canonKey>`,
`dispatch:<season>-wNN`, `scout:<abbr>-<date>`.

### Visual contract

Carried from [UI_DESIGN.md](../UI_DESIGN.md) unchanged. Keelson's own
`validateCategoricalPalette` was run against these values:

| Token | Value | Result |
|---|---|---|
| `--us` | `#0D9488` | Passes in both modes |
| `--them` (dark) | `#F97316` | All four checks pass (CVD ΔE 59.4 protan) |
| `--them` (light) | `#EA580C` | `#F97316` warns at 2.80:1 on white; `brand-accent` passes |
| win / draw / loss | `#10B981` / `#F59E0B` / `#F43F5E` | Board tones `ok` / `warn` / `error` |

Teal = us, orange = opponent, everywhere a tone is accepted. Keelson's `id-teal` is
`#0e9d8f` dark / `#11b3a5` light — within a hair of `data-primary`.

**The one honest break:** board `chart` series use a fixed six-colour ramp assigned by
array index, never cycled, capped at 6 series. Pinning the tracked team to slot 1 paints
it violet on the one board with a chart. Mitigation: slot 1 + direct endpoint label, the
seventh program folded into the caption, slots frozen in `season-slots.json` at season
start, and the real teal season-arc chart lives in the Dispatch HTML where literal hex
is available.

---

## Scheduling

Keelson has **no cron**. No `schedule:`, `cron:` or `every:` field in the workflow YAML
schema; no `keelson schedule` command. Three real clocks, and one trap.

| | Mechanism | Used for |
|---|---|---|
| **A** | Server heartbeat — 30s tick, `apps/server/src/scheduler.ts`, 6× slower with no tab subscribed | The six board collectors. They need neither inputs nor a cwd |
| **B** | `ctx.refreshWorkflow(name)` driven by `src/wallclock.ts` | Everything scheduled. Writes a run row, fires `onRunEvent`, dedupes, **and publishes to the bound key** |
| **C** | `keelson workflow run touchline-refresh --no-watch --json --base-url http://127.0.0.1:7878` from launchd | Fallback for a sleeping laptop. `--base-url` routes through the server, so it publishes exactly like B |
| **✕** | `ctx.runWorkflow(definition, …)` | **Do not use.** It is the only seam accepting a `cwd`, which is why it is tempting. It writes no run row, fires no run event, and does **not** publish to a bound snapshot key — `ribWorkflowBindings` is keyed by definition *object identity* and `runDefinition` parses a fresh object. A refresh through it reaches the database and never reaches the screen. `cwd` was never load-bearing: every bash node already `cd`s into the checkout |

---

## Verified Constraints & Landmines

Each of these was confirmed in source. Each has a plausible-looking wrong version.

| Constraint | Consequence of getting it wrong |
|---|---|
| The merge node must pass the **full historical year list**, never `[2026]` | `merge_all_seasons` *overwrites* `all/*.parquet` with only the years given, `merge_all_schools()` inherits the truncation, and the ten-season archive (ADR-004) is destroyed on the first Saturday night |
| The scrape node needs explicit `timeout: 900000` | Subprocess default is 5 minutes; 13 schools × ~20 matches × 0.5s politeness lands past it. Every matchday window silently half-completes |
| `--no-cache` on every matchday run | `fetcher.py:35-42` keys the cache on `(school, year, game_num)` only and returns the file verbatim. A box score fetched at 21:40 mid-match freezes permanently |
| `--year 2026` is mandatory, not optional | No `schools.toml` entry lists 2026 — every `years` array ends at 2025 — and `scrape.py:91` is `years = [args.year] if args.year else school.years` |
| A bash/script node is a **subprocess** | It cannot reach `sm.register`, `RIB_VIEWS`, or `invalidateManifest`. Page publishing must be an in-process tool named in the prompt node's `allowed_tools` |
| The snapshot manager has **zero file IO** | Published pages must be written to `<dataHome>/pages/` and re-registered at boot, or the archive evaporates on the first restart |
| One workflow binds one key, with its own name | Two regions naming one workflow means one silently never refreshes — a boot warning nobody reads and a panel that looks fine forever |
| Region wiring is boot-frozen | `cadenceMs` and `serverRefresh` are read once when surfaces are walked. Per-team panels must go through `ctx.registerRegion`, never array mutation |
| Never `await` an agent turn inside `onAction` | The harness awaits the handler synchronously and the socket caps at 60s idle. Fire and return; results arrive as snapshot frames |
| Rib activation is **fail-hard** | One out-of-namespace key or duplicate surface id throws and fails the entire server boot, not just this rib |
| `data/raw_html` is 1.1 GB tracked in git | A twice-weekly in-season job adds ~260 files per run. Untrack before S4 turns the scheduler on, or the repo roughly doubles by November. Keep the parquets (12 MB) per ADR-004 |

---

## Implementation Plan

Dependency-ordered. No dates — each stage lands when the one before it works.

### S0 — Upstream pipeline fixes *(this repo)*

The two defects that are destructive rather than merely wrong. Small, and they fix
`apps/web` for free.

**Task 1 — Season assertion.** `packages/pipeline/src/sidearm_discovery.py:42`. Before
accepting any discovered boxscore path, assert it contains `/stats/{year}/`. Fail the
discovery rather than ingesting the wrong season. ~3 lines. This is the fix that would
have prevented FHSU's 2020 season holding 24 games dated 2025.

**Task 2 — Merge safety.** `packages/pipeline/src/storage.py` and
`scripts/scrape.py:103,108`. Two problems: `merge_all_seasons(years, abbrev)` overwrites
`all/*.parquet` with only the years passed, and `scrape.py` skips the per-school merge
entirely when `len(years) == 1` — which is why a single-year in-season scrape never
reaches the database (`load_db.py:274-280` then reads the stale `all/` directory
forever). Make the merge additive with respect to years already on disk, and let a
single-year scrape merge.

**Task 3 — Tests.** Extend `packages/pipeline/tests/` to pin both behaviours: a
discovered path for the wrong season is rejected; a single-year merge preserves prior
seasons.

**Done when:** `uv run scrape --year 2026 --no-cache` for one school, followed by
`uv run load-db`, produces new rows in Postgres without truncating `all/`.

### S0.5 — Repair the existing data *(this repo)*

*Depends on: S0 (do not repair into a pipeline that will re-corrupt).*
Per the revised D-03. Scoped by an audit that establishes, for each defect, what is
recoverable from data on disk versus what requires re-fetching.

**Task 1 — Backfill `is_conference_game`.** GAC membership is authoritative in
`schools.toml` per ADR-007. A game is a conference game when both programs are GAC
members in that season. This is a derivation over data we already have, not a re-scrape.
Ships as a migration plus a loader change so it stays populated.

**Task 2 — Re-scrape mislabeled seasons.** FHSU's stored 2020 is the confirmed instance
(24 games dated 2025 with `/stats/2025/` source URLs). Audit every program-season for the
same signature — a season whose games' dates or source URLs disagree with its label —
before deciding scope. With S0 Task 1 in place, the re-scrape cannot repeat the error.

**Task 3 — Canonical match key.** `sha1(date | sorted normalized team pair)` as a column
on `games`, populated by the loader. Collapses the 176 duplicate groups into one match
with N source perspectives — which is strictly better than picking a winner, because two
schools' box scores for the same fixture sometimes disagree on shots, and showing both is
more honest than showing either.

**Task 4 — Verification.** Re-run the audit and record before/after counts for every
defect in the spec's Problem Statement table. Those numbers become the S2 integrity
board's first baseline.

**Done when:** `is_conference_game` is non-NULL for every game between two GAC programs;
no program-season contains games dated outside it; and the duplicate-group count is
reconciled and explained.

### S1 — The canon and the first Observation

*Depends on: nothing (can run parallel to S0).*
New repo. Package skeleton copied verbatim from `keelson-rib-workiq`. `src/index.ts`
default-exports a Rib with one tool (`touchline_query`). Then the real work:
`src/canon.ts` building the identity map from `SELECT DISTINCT` over
`team`/`home_team`/`away_team`, keyed on abbreviation, with the NSU reconstruction path;
and `bin/observe.ts` writing the first immutable observation.

**Proves:** discovery finds the rib, activation does not throw, `keelson rib list` shows
it, and an observation lands on disk with a table correct for all seven programs — with
the real messiness absorbed ("Okla. Baptist" / "Oklahoma Baptist" / "Okla. Baptist
OKLA."; "#16 Northeastern State" with its ranked-team prefix).

Nothing renders. The ledger *is* the product; everything downstream is a projection.

### S2 — Feed Health

*Depends on: S1 (needs two observations for four of the checks).*
`src/integrity.ts` with all nine checks, `bin/collect-feed.ts`, the `pressbox` surface,
the `touchline-refresh` contribution in observe-only form (no scrape yet), and a **boot
self-check** asserting every cadence-bearing region has a matching bound producer whose
key equals the region key.

**Proves:** we know exactly which numbers are lying and why, with the causing `file:line`
attached. If the project stopped here it would still have delivered the most important
thing.

### S3 — The Table and The Slate

*Depends on: S2 (boot self-check, surface pattern).*
`bin/collect-table.ts`, `bin/collect-slate.ts`, their bound contributions with distinct
workflow names and `expectView` validators, the `season` surface, and the in-process
Matchday composer.

**Proves:** the heartbeat re-runs bound producers with zero scheduling code; boards
render from disk in milliseconds; the Δ column produces a real number against a real
prior observation. Also the point at which to confirm the board-chart colour break and
decide whether the season-arc chart stays on a board or moves entirely to HTML.

### S4 — The refresh DAG and the wall clock

*Depends on: S0 (merge safety), S2 (the board it publishes to).*
The complete 7-node `touchline-refresh` including the scrape node. `src/wallclock.ts`
with `last-fired.json` and `.unref()`. The launchd plist. `touchline_refresh` as a
durable op.

**Gate before this stage turns on:** validate `--year 2026` against a live schedule page
for all thirteen enabled programs. A SideArm site serving 2025 instead of an empty 2026
page reproduces the FHSU corruption on day one, and S0 Task 1 is the assertion that
catches it. Also untrack `data/raw_html` first.

**Proves:** scheduled freshness end to end, unattended, against the project checkout —
the requirement the harness heartbeat structurally cannot meet.

### S5 — Tools and chat ◆ **v1**

*Depends on: S1 (the ledger everything reads).*
All twelve tools with `state_changing: false` on the ten read-only ones.
`contributeDocs` so `keelson_docs` makes the rib self-describing. `/table`, `/scout
<abbr>` with roster completion, `/dispatch`. Two named agents, with `buildSeedFor`
shared between the board's Ask action and `resolveAgent` so the two entry points cannot
drift.

**Proves:** chat in the Keelson composer, in workflow prompt nodes, and over MCP to
Claude Code / Copilot / Codex — from one registration. Cheapest stage, highest
usefulness-to-code ratio.

### S6 — The Match Page and the Dispatch

*Depends on: S5 (the tools the author node calls); benefits from a month of S4 data.*
`src/pages.ts` + `src/tools/emit.ts` (the in-process publish seam), `src/matchpage.ts`,
`src/broadsheet.ts`, boot reconciliation from `<dataHome>/pages/`, the forbidden-metric
render gate, the frame-action allowlist, and the `touchline-dispatch` gate/author/publish
DAG.

**Render gate:** refuse to publish prose containing `xG`, `possession`, `pass` or `foul`
tokens — `team_game_stats` has exactly ten columns and none of them are those. The
author node's `allowed_tools` grants only Touchline tools, which at the SDK level also
strips Read/Glob/Grep so the turn cannot wander.

**Proves:** the visual ceiling — that a rib with zero React can produce a page worth
sending to someone. And that the cost gates work: a week where nothing moved spends
nothing.

### S7 — The Race

*Depends on: enough conference matches for shrunk rates to mean something.*
`src/sim.ts`, `bin/collect-race.ts`, the Race region, `race-history.jsonl` appended once
per **observation** (not per collector tick, or the week-over-week arrows lie).

**Proves:** the fun. Odds that move every Saturday, and a swing table that turns other
people's games into your games.

### S8 — Form, the clock, per-team panels, `game_id` fix

*Depends on: S3.*
`bin/collect-form.ts` with goal-timing segments over the 22,754 event rows no endpoint
has ever aggregated. `ctx.registerRegion` follow/unfollow with identity-hue allocation
and release. Then D-09: content-derived `game_id` upstream in this repo, plus the
one-time full reload it requires.

### S9 — Post-season

Bracket mode for the Race region, the Dispatch splitting into preview/review pairs, a
season-in-review page. Then the deferred correctness work: the `sidearm_legacy` scraper,
so NSU stops being reconstructed (D-06), and the caution `Type` column at
`sidearm_parser.py:339-348`, so red cards become visible outside Harding.

---

## Definition of Done — v1 *(end of S5)*

- [ ] The canonical table is correct for all seven men's GAC programs, including NSU
- [ ] Feed Health reports nine checks with evidence and causing `file:line`
- [ ] Three live boards: Matchday, The Table, The Slate
- [ ] `touchline-refresh` runs unattended on a wall clock and publishes Feed Health on
      every run, including failed ones
- [ ] Twelve tools reachable from Keelson chat and over MCP
- [ ] "What changed since last Sunday?" answers with no arguments
- [ ] A refresh that half-fails leaves the panel reading *stale*, never yesterday's
      numbers presented as current

**The falsifiable failure condition.** If the "since you last looked" register is ever
empty on a Monday in October, the system failed at its actual job. Judge it by that, not
by whether the charts are pretty.

---

## Deferred / Out of Scope

| Item | Why |
|---|---|
| Women's soccer | D-04 — one gender per surface; revisit after 2026 |
| `/touchline` in `apps/web` | D-08 — the bridge is free and stays open |
| Fixing `_ilike_pattern` in `apps/api` | The rib's canon supersedes it; fixing the API is separate work with its own blast radius |
| Red-card `Type` column | S9 — needs parser work across eleven programs |
| `sidearm_legacy` scraper (NSU) | S9 — a KnockoutJS SPA needs a headless browser |
| Database views or any DDL on `ed_insights` | ADR-008 — the rib stays read-only against a schema it does not own |
| Orphaned `game_id` sweeper | D-09 — fix the cause upstream instead of cleaning up after it |
