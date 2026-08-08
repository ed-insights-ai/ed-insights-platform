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

**2. The data is wrong in seven named, reproducible ways.** All verified against the
live `ed_insights` database and the 1.1 GB of cached source HTML, not inferred. Defects
6 and 7 were found by the ground-truth audit and are the two that most affect a season
product — every other defect leaves the *numbers* intact, while these two mislabel which
team they belong to:

| # | Defect | Evidence | Cause |
|---|--------|----------|-------|
| 1 | Conference play unmarked — though 100% derivable | `is_conference_game` NULL for **2140/2140** rows; `away_conference` likewise NULL 2140/2140. Derives with no ambiguity — no opponent string resolves to two programmes — but only if derived **gender-aware**: measured, a gender-blind derivation produces **103 false positives** | Nothing populates it, and ADR-006's `is_conference` flag does not exist per-game (see ADR-006's superseding note); `conferences.py:67-76` therefore returns an *overall* record labelled "standings", and `insights.py:338` buckets every game as non-conference |
| 2 | School identification fails open, inverting results — in **five** mutually inconsistent ways | Measured against a name-variant ground truth over all 2,140 rows. `_ilike_pattern`: **112 rows wrong, 97 score inversions**; 164 rows blind in both slots (OKBU 150/191, SWOSU 6/188, NWOSU 4/163, SNUW 2/171, OBU 1/173, SNU 1/179). Full-name substring: **651 wrong, 537 inversions** — the school identifies itself in only NWOSU 0/163, SWOSU 2/188, FHSU 12/150, OKBU 41/191, RSU 47/132. `startswith(name[:4])`: **17 wrong, 17 inversions** | Five implementations, no shared helper: (a) `_ilike_pattern`+`_matches_pattern` at `conferences.py:24-39`, applied `:85`, `:108`, `:181`; (b) a byte-identical copy at `teams.py:31-43`, applied `:102`, `:145`, `:183`, `:239`; (c) the full-name ILIKE on `School.name` at `stats.py:44-49` — **this is the one `/api/stats/team` uses**; (d) `startswith(school_name_lower[:4])` at `players.py:145`; (e) `.lower().find(...) >= 0` at `insights.py:59,70,75,80`. All read `own_score = home if is_home else away`, so a match *failure* is indistinguishable from "we are away". `_ilike_pattern` reduces "Oklahoma Baptist" → `%Oklahoma%`, missing the **98** home and 52 away games stored as "Okla. Baptist". Issue #15 covers only (a) and needs widening |
| 3 | No canonical match key | **176** duplicate `(date, home, away)` groups, which decompose exactly (measured 42+40+94=176): **42** involve a phantom 2020 row (defect 4), **40** are cross-*gender* collisions — a men's and a women's fixture on the same date between the same two institutions, i.e. real distinct matches, **39 of the 40 with different scores** — and **94** are genuine cross-school perspectives. Put gender in the key and drop the phantoms and it is **98 groups, every one of size 2, with zero score disagreement** | One fixture scraped from both schools; and `(date, home_team, away_team)` is not a match key because it carries no gender. These duplicates inflate essentially nothing — see D-03 |
| 4 | Phantom seasons — copies, not mislabels | **2 program-seasons, 42 rows** — FHSU's stored 2020 holds 24 rows, OBU's holds 18. All 42 carry `/stats/2025/` source URLs, and all 42 are **exact duplicates of the same school's 2025 rows**: measured 42/42 have a 2025 twin matching on `source_url`, both team names and both scores. The cache is poisoned too — `data/raw_html/fhsu/2020/`'s 24 files are byte-identical by SHA-1 to `fhsu/2025/`, and `obu/2020/`'s 18 differ only in a cache-buster script while linking `/stats/2025/` | `sidearm_discovery.py` fetches `/schedule/{year}` and never observes redirects; FHSU and OBU men's have no `2020` slug (their COVID season is slugged `2020-21`) so the request 302s to the bare `/schedule`, which serves the current season. The correct repair is **DELETE** of rows *and* cache directories, not re-scrape — see S0.5 Task 2 |
| 5 | Red cards invisible outside Harding — **but offline-fixable** | All **43** `red_card` rows are HU (41) + HUW (2). The cached HTML contains **166** `penalty-type red` markers; all 166 are present in the DB, stored as `yellow_card`. Nothing is missing — it is mislabelled | `sidearm_parser.py:339-348` hardcodes `yellow_card` for every caution row at the eleven SideArm programs. The type lives only as a CSS class on an empty `<td>`, which `pandas.read_html` renders as NaN. **This needs no re-scrape** — the class is in the cached bytes, so a regex backfills all 166 |
| 6 | Home/away is fabricated — every game, both parsers | Measured against the venue city in the source: SideArm home/away is correct in only **651 of 1,745 games (37.3%)**, from OKBU 24/150 to SWOSU 88/180. StatCrew stores `home_team='Harding'` in **337/337** HU+HUW games, and of the 239 StatCrew box scores carrying a venue only 92 are at Searcy. Needing no HTML: of 569 two-perspective fixtures, **471** have both rows claiming to be home. Scores are unaffected — they move with the names | `parser.py:859-862` swaps on a comment asserting the opposite of the real convention (StatCrew titles are "Away vs Home"); `sidearm_parser.py:127-134` assigns score-table row 0 to home when row 0 is the AWAY team, and the corrective swap at `:414-443` is gated on an `is_home` hint measured `True` on **1803/1803** pages. **Recoverable offline**: 1,802 of 1,803 SideArm pages carry a `Site:` city in a `<dt>/<dd>` pair |
| 7 | 111 games have no date — and the same 111 have `venue='NaN'` | `date IS NULL` for 111 rows and `venue='NaN'` for 111 rows; verified byte-for-byte the **same** 111 (HU 53, HUW 58). All 111 have a recoverable date in the cached title — 98 as `(Sep. 1, 2016)` and 13 as `(10/2/2018)` | `parser.py:159` accepts only a two-digit `MM/DD/YY` group; the venue fallback at `:188` is keyed on the same pattern so it dies with it; then a mixed-dtype parquet turns the emptiness into `np.nan` and the unguarded `row.get("venue")` at `load_db.py:133` lands the literal string `'NaN'` in a varchar. **Blocks the canonical match key**, which is date-derived |

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
| **Repair** | Fix the date regex and home/away in both parsers, delete the 42 phantom rows, backfill `is_conference_game` gender-aware, establish a gender-bearing canonical match key and reconcile the 98 real duplicate groups | S0.5, this repo |
| **Resolve** | Identity across name variants, at read time, for anything the repair pass cannot collapse | `src/canon.ts` in the rib |

The canon still exists — free-text opponent strings will keep arriving from thirteen
independently-formatted sites, so read-time resolution is permanent infrastructure. But
it is no longer carrying corruption that could have been fixed at the source.

**Rationale:** A read-time overlay means every consumer that is not the rib —
`apps/api`, `apps/web`, any notebook, any future tool — still sees the wrong numbers.
`is_conference_game` NULL for 2140/2140 rows is not a rendering problem; it is a field
nobody populated, and one that is 100% derivable from data already on disk. FHSU's and
OBU's stored 2020 seasons are not a display bug either; they are 42 copied rows that
should never have existed. Those are cheaper to fix once in the data than to compensate
for forever in every reader.

**The decisive finding of the ground-truth audit: every defect is repairable offline.**
Re-parsing all 2,140 cached box scores produces zero parse failures and zero missing HTML,
and the evidence needed to fix every defect in the table above is in the 1.1 GB of cached
HTML we already hold. No re-scrape, no network. *That* part stands.

> **Corrected 2026-08-08 by an adversarial audit of the harness itself.** Two sentences
> that used to sit here were overclaims, and both were load-bearing.
>
> - *"reproduces … for 2,140/2,140 games"* — the check's own current output is **2,005
>   exact, 135 differ** (venue 111, events 26). The 111 are the known `'NaN'` rows.
> - *"The storage layer invents and corrupts nothing"* — **false.** The per-season parquets
>   hold **22,782** event rows; Postgres holds **22,754**. **28 real events are destroyed at
>   load**, because `storage.py:15-27` hashes seven fields but not `description`, so two
>   events sharing a clock collapse into one. That is a loader defect, and it is now
>   P0 (`tl-3zm`).
>
> Note also what the re-parse can and cannot prove. It re-parses with the *same*
> `parse_game` / `parse_sidearm_game` that produced the stored rows, so a systematic parser
> misread reproduces exactly and reads as fidelity. And it compares players on
> `(player_name, shots, shots_on_goal, goals, assists)` — **not `team`** — and events on
> `(event_type, clock, player)`. "Zero field diffs" was always compatible with 723
> roster-swapped games and 8,949 events whose team string joins to neither side.
>
> The honest form of the verdict is narrower than *"the numbers are true, the labels are
> wrong."* The labels half is fully supported. The numbers half rests on the **139
> StatCrew × SideArm pairs** — two platforms *and* two parsers — showing zero goal
> disagreements, plus the scoreline-vs-events oracle and the physical-impossibility checks.
> For the other **454 SideArm × SideArm pairs** it rests on agreement between two runs of
> the same code, which is weaker evidence than it reads as. See the *measuring instrument*
> epic for the corrections.

**What is *not* wrong — corrected:** the 176 duplicate groups inflate nothing. **No**
duplicate group shares both `school_id` and `season_year` (measured: 0), and every
aggregate in `apps/api` filters or groups by `school_id`, so a fixture's second
perspective belongs to the *other* school and never enters the first school's totals.
The one real inflation is caused by the phantoms, not by duplication: `/api/stats/players`
(`stats.py:131-136`) groups by `school_id` without `season_year` and only joins `Game`
when a `season` filter is supplied, so with no filter **574 (player, school) rows carry
doubled totals**. Deleting the 42 phantom rows removes that entirely. Any claim that
"every aggregate over the base tables is inflated" should be struck wherever it appears.

Those duplicate rows are also the dataset's only free correctness oracle: 493 fixtures
scraped from two unrelated sites agree 493/493 on the score and 977/986 on all five team
metrics. **Do not collapse them before the parsers are fixed** — they are the regression
test for the home/away and red-card repairs.

**Still routed around, deliberately:** replacing the team-name matchers in `apps/api` has
its own blast radius and is separate work — and there are **five** of them, not one, so it
is five call-site replacements plus the deletion of four duplicate implementations.

**No longer routed around:** the red-card `Type` column (`sidearm_parser.py:339-348`) was
deferred to S9 on the belief that it needed a full re-scrape. It does not. The card type is
a CSS class on an empty `<td>` and it is present in every cached page — grepping
`penalty-type red` returns **166** against 43 stored, all 166 already in the database
wearing the wrong label. It is a regex change plus a re-parse, so it moves into the repair
pass. The same unparsed SideArm play-by-play carries all 166 with correct types as an
independent second route.

**Revisit if:** the repair pass reveals that a defect can only be fixed by re-scraping
history we cannot reliably re-fetch, in which case the canon absorbs it and the integrity
board reports it permanently.

### D-04 — Both genders in scope

***Overturned 2026-08-07. Was: "Men's soccer only for 2026."***

**Decision:** Seven men's and seven women's GAC programmes, across **two `season`
surfaces** — `season-men` and `season-women` — with region keys carrying a `:m:`/`:w:`
segment (`rib:touchline:m:table`, `rib:touchline:w:table`). The `pressbox` surface stays
single and gender-spanning; Feed Health is about the pipeline, not the sport, so its
per-programme grid simply gains a gender column. Nav stays at three tabs. `src/keys.ts`
is the single place that knows the qualifier.

**Rationale:** the original decision rested on a claim that is false. It read: "every
school carrying the identity defect is a women's programme … the men's side is clean."
That is true only of `_ilike_pattern`, which is one of five matchers and is *not* the one
`/api/stats/team` uses. Under the full-name ILIKE at `stats.py:44-49`, the two
worst-affected programmes after the women's are **men's**: FHSU identifies itself in 12 of
150 games, RSU in 47 of 132.

The data is also majority women's — **1,238 of 2,140 rows** against 902 — and the women's
side is in better shape on every measured axis: 7 fully-scraped programmes against 6 plus a
reconstructed NSU, **0** phantom rows against 42, **1** parse-failure blob against 33, a
complete 7-team conference round robin every season 2016-2025 where the men's conference
had only 3 programmes in 2016-2018, and zero games missing scores, team stats or player
stats. It is the *cheaper* of the two tables to build correctly.

**Why two surfaces rather than the alternatives — mechanically, not aesthetically.** A
persisted mode toggle routes through `workflowArgs` on `surfaceRegionSchema`, and
`deriveSurfaceSchedules` (`scheduler.ts:63-68`) explicitly *skips* any `workflowArgs`-bearing
region, warning that it refreshes client-side only. A toggled board would refresh only while
a tab is open — the exact opposite of a season tracker. Gender-suffixed regions on a single
surface save nothing, because a region's workflow must bind its own key, so ten regions still
need ten workflows; and they invite a combined chart, where `chartSectionSchema` is `.max(6)`
and fourteen series is a **hard schema rejection** with fail-hard rib activation. Two surfaces
cost one extra nav tab and keep every per-board constraint — 6-series cap, 5 identity hues —
exactly as it is today.

**Cost, priced in.** Scrape and load do not change at all: `schools.toml` already enables 13
programmes and `data/raw_html` already holds all 2,140 pages, so D-04 never saved a second of
collection — it only hid rows already on disk. A both-gender in-season observation is 2.85 MB
(men 1.35, women 1.49) and the full-history read takes 202 ms against live Postgres. S3 grows
(2 collectors → 4, 2 surfaces, 2 Matchday composers, 2 slot files) — bigger, not harder,
roughly +1 day. Every snapshot key, collector, canon lookup and conference derivation becomes
gender-aware. That last one is not optional: a gender-blind conference derivation produces
**103 false positives** (measured), because "Northeastern St." in a women's fixture and
"Northeastern St." in a men's fixture are different institutions' programmes.

**Revisit if:** two surfaces proves unreadable, in which case the answer is a different
navigation, not the deferral of one gender.

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

**Note (added with the D-04 reversal):** the women's table has no equivalent gap. All
seven women's GAC programmes in `schools.toml` are `enabled=true` and carry data, so no
`via opponents` reconstruction is needed and no honesty badge is required — that is the
women's table's one structural advantage over the men's, and the caption should say so.
NSU is a men's-only GAC member; women's fixtures against "Northeastern St." are
non-conference.

But the women's roster in `schools.toml` may be incomplete: women's GAC programmes played
"Northeastern St."/"Northeastern State" **32 times across 2016-2025 and all seven
programmes**, plus Rogers State 18x and Newman 17x, none of which resolve to a women's GAC
member. That is conference-schedule frequency, not out-of-conference frequency. See the
open question on ADR-007 in S0.5 Task 1 — it is a fact about the GAC, not about the
database, and cannot be settled from the data alone.

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
│  rib:touchline:{m,w}:{table,race,slate,form,feed,ledger,      │
│                       matchday}   (two surfaces: season-men,  │
│                       season-women; pressbox shared)          │
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
| `src/canon.ts` + `canon.json` | **Correctness floor.** Identity keyed on *abbreviation*, never name — the live `schools` table has **three** names carried by two rows each: "Harding" (HU id=3 / HUW id=10), "Ouachita Baptist" (OBU id=7 / OBUW id=14), "Southern Nazarene" (SNU id=9 / SNUW id=15). Maps to **gender-free institution slugs**, with gender as a separate axis, because opponent strings carry no gender. Collapses the 98 real duplicate groups; derives `is_conference_game` **gender-aware**; resolves 193 team strings and 9,781 player-name strings across `Last, First` and `First Last` forms (canonicalising collapses them to 7,683); allocates identity hues | Replaces all five matchers: `_ilike_pattern` (`conferences.py:24-31`, `teams.py:31-38`), the full-name ILIKE at `stats.py:44-49`, `startswith(name[:4])` at `players.py:145`, and the `.find()` at `insights.py:59,70,75,80` |
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

Three Keelson surfaces (top-level nav tabs). Per the D-04 reversal the `season` surface
exists **twice** — `season-men` ("Men's") and `season-women` ("Women's") — with identical
region structure. Every key in the Key column below is shorthand for `rib:touchline:m:<key>`
on the men's surface and `rib:touchline:w:<key>` on the women's. Fourteen board regions in
total, seven per surface, so every per-board constraint (6-series chart cap, 5 identity hues)
is unchanged from the single-gender design.

`pressbox` stays **single and gender-spanning**: Feed Health and the Ledger describe the
pipeline, not the sport, so their per-programme grids gain a gender column rather than being
duplicated. Keys there stay unqualified.

**`season-men` / `season-women`**

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
| ~~`data/raw_html` is 1.1 GB tracked in git~~ — **resolved, #18** | The blanket `!packages/pipeline/data/` negation swept the HTML cache into git. `.gitignore` now excludes `raw_html/`, stopping the growth with no history rewrite: already-committed pages stay tracked as an offline re-parse archive, new ones are ignored. Parquets stay tracked per ADR-004 |

---

## The verification harness

`.keelson/workflows/data-integrity.yml` — a Keelson workflow in this repo, runnable now:

```
keelson workflow run data-integrity          # or workflow_run over MCP, project-scoped
```

Nine deterministic read-only checks (`freshness`, `conference-flag`, `duplication`,
`season-label`, `identity`, `discipline`, `orphans`, `parse-failures`, `archive`) run in
parallel against the live Postgres and the parquet archive, then one report node prints a
per-check verdict with the causing `file:line`. No model turns, so it costs nothing to run
and is safe to run often. `mutates_checkout: false` — it never writes.

It exists for three reasons: it is the before/after evidence for every repair in S0 and
S0.5; it is the working prototype of the rib's `src/integrity.ts` (Stage S2), so that
stage is mostly a port; and it is the thing that catches a regression when the scheduled
refresh starts running unattended.

It has already earned its keep — it found that **OBU 2020 is phantom too**, not just
FHSU, and it forced a correction to the identity numbers this spec originally carried.

It is not yet sufficient, and its limitation is structural: it checks whether the data is
*self-consistent*, never whether it is *true*. `team_game_stats` scores 4,280/4,280 against
`games` on every internal-coherence measure — which is exactly what hides the home/away
defect, because the table is consistently wrong. This workflow would pass today's data.

The companion `ground-truth.yml` closes that gap with twelve read-only, offline checks that
re-derive from the 2,140 cached box scores and from the second transcription that exists
wherever two schools scraped one fixture.

> **The instrument is not yet fit to grade the repair.** An adversarial audit on 2026-08-08
> found faults serious enough to need their own epic. The headline one is systemic:
> **19 of the 21 checks fail OPEN.** Every `Q()` sends psql stderr to `/dev/null` and most
> verdicts are unguarded `[ "$X" -gt 0 ]`, which on an empty string is a shell *test error*
> — so `V` keeps its initial value of `ok`. Demonstrated: a check body run against a
> nonexistent database emits valid JSON with `"verdict":"ok"` and exit 0, and the report
> renders `[ OK ]` with blank numbers.
>
> Also: `archive`'s verdict is `[ "${PQ:-0}" -lt 0 ]` — a row count is never negative, so
> that check can never detect the mismatch it exists for; and `duplication`'s ALARM is
> driven by 39 "score disagreements" which are **all** legitimate men's-vs-women's fixture
> pairs, so it reports corruption that does not exist.
>
> The `duplication` check that needs gender in its key is in **`data-integrity.yml:49-51`**,
> not in `ground-truth.yml` — an earlier draft of this paragraph named the wrong file. Its
> `identity` check reproduces only `_ilike_pattern`, one of five matchers, and the `Site:`
> city oracle that produced the headline 651/1,745 home/away figure is **in neither
> workflow**, so that number is not currently reproducible by the instrument that is
> supposed to grade its repair.

The numbers in the Problem Statement above are the targets for both — once the checks that
measure them are trustworthy.

> **Authoring note, learned the hard way.** Do not name a shell variable `GROUPS` in a
> bash node. It is a readonly bash builtin array holding the caller's group ids;
> assignment is silently ignored and `$GROUPS` expands to a gid — `20` on macOS — which
> reads as a perfectly plausible count. And keep heredocs out of YAML block scalars: an
> embedded script at column 1 terminates the scalar and silently unregisters the whole
> workflow. Validate with a real YAML parse before trusting that a workflow exists.

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
`schools.toml` per ADR-007. A game is a conference game when both programs are GAC members
**of the same gender** in that season. This is a derivation over data we already have, not a
re-scrape; ADR-006's claim that the field comes from SideArm's `is_conference` flag is false
(see ADR-006's superseding note). Ships as a migration plus a loader change so it stays
populated.

**Three constraints, each of which changes the answer:**

- It must be **gender-aware**. Measured: gender-aware **1,430** conference rows against
  gender-blind **1,533** — **103 false positives**, every one a real fixture where an
  institution fields the other gender outside the GAC (28 men's vs Okla. Baptist, 24 women's
  vs Northeastern St., 16 women's vs Newman, 11 women's vs Rogers State).
- It must be **season-aware**. Men's GAC is HU/OBU/SNU for 2016-2018 and gains
  FHSU/NU/NSU/RSU from 2019; women's is a stable seven throughout. Add a
  `(gender, institution_slug, since_year)` membership table and a `gac_since` field to
  `schools.toml` so this derives from config rather than a hardcoded table in the loader.
- It must run over a **corrected own-team identification**. None of the five `apps/api`
  matchers is good enough; the canon is a prerequisite, not a consumer.

**Resolved: `schools.toml` is a membership record, not a scrape-coverage list.** This was an
open question — it moves 100–120 rows — and it is settled by two measurements plus a
documented date, not by judgement.

*Meeting frequency separates a member from a neighbour by an order of magnitude.* A conference
member is met by every programme every year; a convenient nearby opponent is met by about half
the programmes, some years:

| Women's opponent | Meetings/season | Per programme per season |
|---|---|---|
| OBUW, SNUW — known GAC | 23.3–29.7 | **3.33–4.24** |
| Northeastern State | 3.6 | **0.51** |
| Newman | 2.1 | **0.30** |
| Rogers State | 2.0 | **0.29** |

*Season timing corroborates it.* 100% of the women's Northeastern State fixtures fall in
August–September, against 40% for known GAC opponents — conference play runs into October and
November, non-conference is front-loaded. These are out-of-conference friendlies against nearby
institutions, so **the women's roster in `schools.toml` is complete**; NSU, RSU and NU field
men's GAC teams and non-GAC women's teams, which is exactly why the derivation must be
gender-aware.

*The men's affiliate boundary shows the same signature inverted.* Meetings per season, before
and after 2019:

| Men's opponent | 2016–18 | 2019–25 |
|---|---|---|
| FHSU | 1.0 | **32.0** |
| NU | 0.7 | **21.3** |
| RSU | 1.0 | **20.1** |
| OBU — member throughout | 16.7 | 13.4 *(flat)* |

A 32× step at exactly 2019 against a flat line for a continuous member. This corroborates
[UI_DESIGN.md](../UI_DESIGN.md) line 18 — *"4 affiliates: FHSU, Newman, NSU, Rogers State —
men's only, joined GAC 2019"*. Pre-2019 men's fixtures against them are **non-conference**.

Reproduce either table with `keelson workflow run data-integrity` plus the queries in this
section's git history.

**Resolution is unambiguous but not automatic.** No opponent string resolves to two
programmes, so there are no ties to break. But **13 distinct opponent strings are near-misses
requiring hand adjudication** before the migration is written: "Northwestern OSU" (3 rows) and
"Southwestern OSU" (2) are real GAC programmes under alternate spellings and MUST resolve,
while "Southwest Baptist" (24), "Dallas Baptist", "Williams Baptist", "Southwestern Christi.",
"Southwestern (KS)" and "Central Baptist" are NOT members and must not. Getting these wrong is
silent. Bake the adjudicated list into `canon.json`, not into the migration.

**Open question — `schools.toml` as a membership record.** Treating each programme's `years`
array as its GAC membership span is a *scrape-coverage* fact being read as a membership fact,
and it swings the result by roughly 100-120 rows. This is the same question as the incomplete
women's roster noted in D-06. **Settle it before the migration is written.**

**Task 2 — Delete the 42 phantom rows.** *Revised: this task previously read "re-scrape
mislabeled seasons", which is not achievable and would not be the right repair anyway.*

Two instances totalling 42 rows: FHSU 2020 (24) and OBU 2020 (18), all carrying
`/stats/2025/` source URLs. They are not mislabelled — they are **exact duplicates of the
same school's 2025 rows**. Measured: 42/42 have a 2025 twin matching on `source_url`, both
team names and both scores; children match too (1,604 player lines, 84 team lines, 321
events). There is nothing to relabel and nothing to recover, so the repair is `DELETE` on the
42 `games` rows and their children.

`data/raw_html/fhsu/2020/` and `obu/2020/` are **not** empty and must be deleted with the
rows, or a scrape without `--no-cache` re-ingests them: 42 files, every one the 2025 season.
FHSU's 24 are byte-identical by SHA-1 to `2025/`; OBU's 18 differ only in a cache-buster
`<script>` and reference `/stats/2025/` throughout. A scan of every cached `*/2020` directory
flags exactly these two and no others.

Deleting them also removes the only real aggregate inflation in the database:
`/api/stats/players` groups by `school_id` without `season_year`, so with no season filter
**574 (player, school) rows currently carry doubled totals**.

**Root cause, and a residual gap in the PR #14 fix.** FHSU and OBU men's soccer have no
season slug `2020` — their COVID season was played in spring 2021 and is slugged `2020-21` —
so `/schedule/2020` 302s to the bare `/schedule`, which serves whatever season is current.
PR #14's year-segment assertion *would* have prevented these 42, but it is blind during
preseason: when the fallback page has no box scores yet, the code takes the `if not matches`
branch and logs the same message for "season not started" and "you were served a different
season". Add a redirect assertion (`resp.history` / `resp.url`) alongside it — that is correct
in both windows. Also remove the unreachable `2020` entries from FHSU's and OBU's `years`, or
widen the slug type: `discover_sidearm_season(year: int, ...)` cannot express `2020-21`.

The genuine 2020 seasons are **missing, not corrupt**, and are out of scope here.

**Task 3 — Canonical match key.** `sha1(gender | date | sorted normalized institution pair)`
as a column on `games`, populated by the loader.

**Gender is not optional in the key.** Without it, 40 pairs of genuinely distinct fixtures
collide — a men's and a women's match on the same date between the same two institutions —
and **39 of those 40 pairs carry different scores**, so collapsing them would silently destroy
a real result. Gender comes from `schools.gender` of the row's `school_id`, which is reliable:
all 2,140 rows agree with the mens-soccer/womens-soccer segment of their own `source_url`.
Opponent strings carry no gender, so `canon()` must map to a **gender-free institution slug**
with gender as a separate axis.

**The pair must be sorted, never `(home, away)`** — home/away is fabricated (defect 6), so an
order-dependent key would fail to match the two perspectives of the same fixture.

**Depends on the date fix (defect 7).** 111 rows have no date and cannot receive a key until
the title regex at `parser.py:159` accepts the other two forms. Sequence that into S0.

Measured over the 1,987 keyable rows, with the 42 phantoms already gone via Task 2:

| Metric | Value |
|---|---|
| distinct canonical matches | **1,401** |
| two-perspective fixtures | **586** (men 204, women 382) |
| max group size | **2** |
| groups where `count(*) != count(DISTINCT school_id)` | **0** |
| groups mixing genders | **0** |
| groups disagreeing on oriented score | **0** |

Each group collapses into one match with two source perspectives — strictly better than
picking a winner, because two schools' box scores for the same fixture sometimes disagree on
*shots* even when they agree on the score, and showing both is more honest than showing
either. **Do not de-duplicate these rows before the parsers are fixed** — they are the only
free correctness oracle in the dataset and are the regression test for defects 5 and 6.

**Residual risk to state:** a same-gender doubleheader between the same two institutions on
one date would collide. Zero such cases exist 2016-2025. Mitigation if one ever appears:
append the site-unique numeric boxscore id from the URL.

**Task 4 — Verification.** Re-run `keelson workflow run data-integrity` and record
before/after counts for every defect in the Problem Statement table. Those numbers become
the S2 integrity board's first baseline.

**Done when:**

- `is_conference_game` is non-NULL for all 2,140 rows, derived gender-aware and season-aware,
  with the 13 near-miss opponent strings adjudicated in `canon.json` and zero rows resolving
  to two programmes. *(State the expected conference/non-conference split only after the
  membership-span question in Task 1 is settled — it moves the answer by ~100 rows, so it is
  a judgement, not an acceptance threshold.)*
- The 42 phantom rows, their child rows and the `data/raw_html/{fhsu,obu}/2020/` directories
  are gone; no program-season contains games dated outside it; the doubled-aggregate count
  goes 574 -> 0.
- `date IS NULL` goes **111 -> 0** and `venue='NaN'` goes **111 -> 0**.
- Cross-perspective home/away contradictions go **471 -> 0** across the 569 two-perspective
  fixtures, and `home_team='Harding'` for HU+HUW falls from 337/337 to roughly half.
- The SideArm roster swap goes **723 -> 0** on the arithmetic gate and **739 -> 0** against the
  HTML captions; StatCrew stays at 0/337.
- Red cards converge: `penalty-type red` markers in cached HTML = **158** and SideArm
  `red_card` rows = **158**. *(Corrected 2026-08-08 from 166 = 166, which is unsatisfiable:
  of the 166 markers in the cache, **8** sit in the phantom `fhsu/2020` and `obu/2020`
  directories that Task 2 deletes — 7 and 1 respectively, byte-identical to their 2025
  twins. 166 = 158 unique + 8 duplicates. Same trap as the re-parse count two bullets down,
  caught there and missed here.)*
- Every `(gender, date, sorted institution pair)` group has `count(*) = count(DISTINCT
  school_id)`, max size 2, zero gender mixing, zero oriented-score disagreement — currently
  40 violations, all phantom, so 0 after Task 2.
- The full re-parse harness reports **2,098/2,098** games re-parsed with 0 errors and 0 field
  diffs, and `ground-truth.yml` reports no alarms it did not report before the repair.
  *(2,098, not 2,140 — Task 2 deletes 42 phantom games and their cached HTML, so the
  post-repair corpus is smaller than the pre-repair one. An earlier draft of this line said
  2,140, which is unsatisfiable after Task 2 and quietly pressures keeping the phantoms.)*
- `ground-truth.yml` itself has been corrected first, per the note in *The verification
  harness*: its duplication check must gain gender in the key (it reports 176 where the true
  figure is 98) and its identity check must cover all five matchers rather than
  `_ilike_pattern` alone. A baseline measured with an uncorrected instrument is not a
  baseline.

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
page reproduces the FHSU/OBU corruption on day one; S0 Task 1 (merged as #14) is the
assertion that catches it, and it now distinguishes "no schedule published yet" (INFO,
benign) from "the site served a different season" (ERROR, naming the year served).
Repo growth was handled separately in #18.

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
so NSU stops being reconstructed (D-06).

*Corrected 2026-08-08.* This stage previously also listed the caution `Type` column at
`sidearm_parser.py:339-348`. That contradicted D-03, which had already moved it into the
S0.5 repair pass, and D-03 wins: it is a regex change plus a re-parse, not a re-scrape.
Leaving it here would have stored every red card of the 2026 season as yellow until
November, and would have made S0.5's own "0 field diffs" gate unsatisfiable — a re-parse
with the hardcoded parser either reverts the 166-row backfill or reports 166 diffs.

---

## Definition of Done — v1 *(end of S5)*

- [ ] The canonical table is correct for all seven men's GAC programs including reconstructed
      NSU, and for all seven women's GAC programs (which need no reconstruction)
- [ ] `is_conference_game` is non-NULL and gender-aware for all 1,401 canonical matches
- [ ] Home/away is derived from the source venue, not from row order or the scraping school
- [ ] Feed Health reports nine checks with evidence and causing `file:line`
- [ ] Six live boards: Matchday, The Table and The Slate, per gender, across the
      `season-men` and `season-women` surfaces
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
| ~~Women's soccer~~ | **No longer deferred** — D-04 overturned 2026-08-07; both genders are in scope. Women's is the larger (1,238 of 2,140 rows) and cleaner half |
| Home/away splits on any board | Defect 6 — `home_team` is fabricated in all 2,140 rows. Recoverable offline from the source venue, but until that lands `touchline_team` ships without a home/away split |
| `/touchline` in `apps/web` | D-08 — the bridge is free and stays open |
| Fixing the five team-name matchers in `apps/api` | `conferences.py`, `teams.py`, `stats.py`, `players.py`, `insights.py` — five implementations, no shared helper. The rib's canon supersedes all five; fixing the API is separate work with its own blast radius. **Issue #15 is scoped to `_ilike_pattern` only and needs widening to all five** — the worst offender is the full-name ILIKE at `stats.py:44-49`, which `/api/stats/team` uses |
| ~~Red-card `Type` column~~ | **Moved into the S0.5 repair pass** — the deferral assumed a re-scrape was needed. It is not: the `penalty-type red` CSS class is in every cached page (166 markers against 43 stored reds), so a regex plus a re-parse backfills all 166 offline |
| `sidearm_legacy` scraper (NSU) | S9 — a KnockoutJS SPA needs a headless browser |
| Database views or any DDL on `ed_insights` | ADR-008 — the rib stays read-only against a schema it does not own |
| Orphaned `game_id` sweeper | D-09 — fix the cause upstream instead of cleaning up after it |
