# Touchline — Product Brief

> A Keelson rib that gives an amnesiac dataset a memory. Every refresh writes an immutable
> observation; every board and every chat answer is the diff between two of them. By November
> the season is a bound volume instead of a dashboard that forgot.

**Written 7 August 2026. Annotated 8 August 2026.** The designed original is preserved at
[`brief/touchline-brief-2026-08-07.html`](brief/touchline-brief-2026-08-07.html) — open it for
the rendered board mockups and the season-arc chart, which do not survive the trip to markdown.

This markdown version is the one to read for grounding, because it is **corrected**. Several
claims in the original have since been disproven by adversarial audits, and reading a
superseded claim as fact is precisely the failure mode this project keeps making.

| | |
|---|---|
| Plain-language state | [STATUS.md](../STATUS.md) |
| What to work on | [ROADMAP.md](../ROADMAP.md) |
| How it works | [specs/touchline-rib.md](specs/touchline-rib.md) |
| Why, formally | [decisions/ADR-008](decisions/ADR-008-touchline-keelson-rib.md) |

---

## Corrections since publication

Read these before the rest. Each was established by measurement, not argument.

**1. "Re-parsing reproduces … for 2,140/2,140 games" — overstated.** The check's own output is
**2,005 exact, 135 differ** (venue 111, events 26). The 111 are the known `'NaN'` rows.

**2. "The storage layer invents and corrupts nothing" — was false, now fixed (9 Aug).** The
per-season parquets held **22,782** event rows against Postgres's **22,754**: **28 real events
were destroyed**, one of them a goal, because the event-id hash covered seven fields but not
`description`, so two events sharing a clock collapsed into one. The loss happened in
`merge_all_seasons`'s `drop_duplicates(subset=["event_id"])`, not at parse or at load — the
per-season parquets were intact throughout, and `load_db` reads the per-school `all/` merges
rather than them, which is why the database was the corpus that showed the gap. Fixed in PR
#54 and recovered by the re-merge under `tl-o23`/`tl-3zm`: **27 real events restored** (the
28th was inside a phantom game and was deleted with it). All three corpora now agree at
**22,460**.

**3. "493/493 across two unrelated websites" — the independence is overstated.** Twelve of
thirteen data-bearing programmes are SideArm; only HU/HUW are StatCrew. Roughly **454 of 593
pairs are SideArm × SideArm** — same platform, same parser — so a *consistent* parser bug is
invisible to that agreement. The genuinely cross-parser evidence is the **139 pairs involving
HU/HUW**. Real, but narrower than the sentence implied. The re-parse pillar is also
self-referential: it re-parses with the same parser that produced the stored rows.

**4. "The 176 duplicate groups inflate nothing" — right conclusion, wrong number.** 176 is the
gender-blind count. Gender-aware it is **138** today and **98** once the 42 phantom rows are
deleted. The 39 "groups disagreeing on score" that drive the check's ALARM are **all**
legitimate men's-vs-women's fixtures on the same date between the same institutions; gender-aware
the figure is **0**. The check has been reporting corruption that does not exist.

**5. The thin ledger lost.** The brief describes "~200 KB per observation, ~6 MB a season".
[D-01](specs/touchline-rib.md) chose the **fat** ledger — full per-match box lines, ~2 MB per
observation, ~55 MB a season — because a thin one cannot answer "what did we think that shot
count was on Sep 6" and limits the score-mutation check to scores only.

**6. Men's-only lost, and its premise was false.** The brief's fork asks whether to defer
women's. D-04 was overturned: women's is the *larger and cleaner* half (1,238 games to 902,
zero phantom rows to 42). And the claim that "every school carrying the identity defect is a
women's programme" holds only for `_ilike_pattern`, one of five matchers and not the one
`/api/stats/team` uses. Under the full-name ILIKE, two of the three worst-affected programmes
are **men's** — FHSU identifies itself in 12 of 150 games, RSU in 47 of 132.

**7. Red cards converge at 158, not 166.** Of the 166 `penalty-type red` markers in the cache,
**8 sit in the phantom `fhsu/2020` and `obu/2020` directories** that get deleted. 166 = 158
unique + 8 duplicates.

**8. "Eighteen days to v1" no longer holds.** The correctness work expanded substantially once
the *instruments* turned out to need repair before they could grade anything. The sequence in
the brief is still right; the duration is not.

---

## The thesis

You already built the hard part. It just can't remember anything.

`ed-insights-platform` is a working scraper, a 2,098-game Postgres database with 75,982
player-game rows and 22,460 parsed match events, a FastAPI service over it, and a Next.js app
with a genuinely good design system behind it. The plan document even has a Phase 5 — LLM
insights, a text-to-SQL chat panel, match predictions. It sits behind four phases of frontend
work.

A Keelson rib isn't a detour from that plan. **It is Phase 5 arriving first, through a door
that is already built** — because Keelson already has the chat, the scheduler, the provider
routing, the persistence and the browser UI. What it doesn't have is anything that knows about
soccer.

## The data is lying, in named and reproducible ways

Every one confirmed against `ed_insights` on localhost, not inferred. A prettier dashboard over
this is a downgrade.

| Defect | Scale | Cause |
|---|---|---|
| Home/away is fabricated | correct in ~651 of 1,745 SideArm games | both parsers force the scraping school into the home slot |
| Rosters wear each other's names | 723 games | `parse_sidearm_game` swaps teams and scores but never reorders the player tables |
| Red cards stored as yellow | 158 markers vs 43 stored | the type lives only as a CSS class the parser never reads |
| Dates and venues missing | 111 games | one over-strict title regex |
| ~~Events destroyed at merge~~ **fixed 9 Aug** | was 28, incl. one goal; now 0 | the event-id hash omitted `description` |
| ~~Phantom duplicate rows~~ **purged 9 Aug** | was 42; now 0 | a season URL 302s to whatever season is current |
| `is_conference_game` never populated | 2,098 of 2,098 NULL | the field was never derived; ADR-006 claimed a source that does not exist |

**And the structural one, which is why this brief exists:** `scripts/load_db.py:186-201` DELETEs
then re-INSERTs every child row per `game_id` on each load. Last week's numbers are physically
gone. The database can only ever tell you what is true *right now*.

## Give the data a time axis, and everything falls out of it

Touchline writes one immutable Observation per refresh — the canonical table, per-team
aggregates, per-player season lines, **full per-match box lines**, a `game_id → fingerprint`
map, and provenance.

That single decision makes four things true that are impossible today:

- **"What moved since Saturday" is a diff between two files, not a query.** Always true, because
  nothing overwrote it.
- **Four of the nine integrity checks compare two observations** — did a `game_id` change
  identity, did a final score mutate, did a programme lose matches, is the feed stale.
- **"Show me the table as it stood on September 6th"** is just reading an older file, form
  strips and all.
- **A watermark gate reads the diff before spending a turn.** A quiet Tuesday costs zero tokens
  and the boards still render.

Every board becomes a pure function of files on disk — fast, deterministic, testable, offline,
recomposable. No board ever touches Postgres. Exactly one thing does, once per refresh:
`bin/observe.ts`.

## What it looks like

Rendered in Keelson's own board vocabulary. No React, no second app.

Teal is us and only us; orange is the opponent; green / amber / rose are win / draw / loss.
That contract comes straight from [`UI_DESIGN.md`](UI_DESIGN.md) and survives the port intact —
with one adjustment. Keelson's `validateCategoricalPalette` passes dark `[#0D9488, #F97316]` on
all four checks (lightness band, chroma floor, colourblind separation ΔE 59.4 protan, surface
contrast); light mode warns on `#F97316` at 2.80:1 on white, so light swaps to brand-accent
`#EA580C`.

- **The Table** — seven programmes per gender, not six. `schools.toml` declares seven GAC
  members; NSU is `enabled=false` only because their site is a KnockoutJS SPA with no scraper.
  But every box score records both rosters, so their *conference* record is recoverable from the
  six schools they played, and the row says so rather than omitting a real member. Their overall
  record is not recoverable, and the board must not pretend otherwise.
- **The Slate** — fixtures that flip to results within ~30 minutes of a final whistle, with
  nobody clicking anything.
- **Matchday** — fold the panel and the record still reads 4-1-2 in the header strip. The header
  carries the story even collapsed.
- **The Race** — the biggest game left on the schedule isn't *on* the schedule. That is the
  reason to open the tab on a Sunday morning, and nothing in the existing stack can compute it.
- **Feed Health** — the first board shipped, before anything pretty. On a dataset with this many
  named defects, the panel that says which numbers are lying — and cites the line that broke
  them — is the highest value-per-hour work available.

And once a week, a **broadsheet**: a dated, versioned HTML page in Keelson's full-width drawer,
the thing you would actually send someone. The layout is a deterministic function of the ledger;
only the prose is generated, slotted into a fixed scaffold so the archive stays a series instead
of being silently redesigned every week.

## Keelson has no cron

There is no `schedule:`, `cron:` or `every:` field anywhere in the workflow schema, and no
`keelson schedule` command. Scheduled freshness is assembled from three real clocks — and one
obvious-looking seam is a trap.

| | What it is | What it drives |
|---|---|---|
| **A** | 30s heartbeat in `apps/server/src/scheduler.ts` re-runs any bound producer with a `cadenceMs`. Always fires with empty inputs and `KEELSON_HOME` as cwd | the cheap board collectors, which need neither |
| **B** | `setInterval(60_000).unref()` in the rib, evaluating a slot table against local time, persisting `last-fired.json` | the only in-process way to get time-of-day |
| **C** | launchd calling `keelson workflow run touchline-refresh --no-watch --json --base-url http://127.0.0.1:7878` | belt and braces, because a laptop sleeps |
| **TRAP** | `ctx.runWorkflow` | **writes no run row, fires no run event, and does not publish to a bound snapshot key** — bindings are keyed by definition object identity and `runDefinition` parses a fresh object. A refresh through it reaches the database and never reaches the screen |

`cwd` was never load-bearing anyway: every bash node already `cd`s into the checkout.

## Nine real forks

The ones where either side is arguable. Three have since been settled by measurement — marked.

1. **Fat ledger or thin?** — ***settled: fat.*** A thin ledger makes the Sep 6 table work but
   leaves shot-count history unanswerable.
2. **Is the Dispatch really last?** The phasing puts correctness, boards, scheduling and chat
   ahead of any designed page, on the theory that an LLM narrator over inverted records is worse
   than no narrator. The counter-case: the broadsheet is what decides whether this feels like a
   product or a dashboard, and a product nobody enjoys opening dies regardless of correctness.
3. **Patch the pipeline, or route around it?** — ***settled: patch.*** Routing around keeps the
   rib self-contained, but four of these are one-line fixes upstream and fixing them repairs the
   Next.js app for free.
4. **Men's only, a toggle, or double every region?** — ***settled: both genders, two surfaces.***
5. **Is the in-process wall clock worth its risk?** It runs inside the Keelson server and shells
   out to `uv run` on a timer. Nothing forbids it and both chamber and squad hold timers — but
   nothing tests that path either, and a bug there is a bug in the harness.
6. **Seven programmes or six?** Reconstructing NSU is genuinely lossy. A conference-only table
   with NSU is honest; an overall table with NSU is not.
7. **Should the narrator exist at all in v1?** The "since you last looked" register is
   deterministic, always true, zero tokens. There is a real case for shipping only that all
   season — the delta lines are the part that tells you something you did not know, and the prose
   mostly restates them at greater length.
8. **Do we ever build a `/touchline` tree in the Next.js app?** The bridge is already free. What
   a board genuinely cannot do is real — sparklines inside table rows, a 9-axis radar, a URL per
   entity you can text someone — but the port is ~1,600 lines to render the same payload in a
   second chrome.
9. **What happens to orphaned `game_id`s?** A sweeper is destructive in someone else's database;
   a soft-delete column is an alembic ownership problem. Deferred to a content-derived id.

## What we decided not to build

- **The hybrid — rib plus a `/touchline` route tree.** The closest call. Rejected on one number:
  `BoardView.tsx` is 1,308 lines plus a 337-line hand-rolled chart section plus ~200 lines of
  region chrome, against a proposal that budgeted "roughly 400 lines" for it. And deferring costs
  nothing, because the bridge is already open.
- **A cron entry and more Next.js pages.** Gets you fresher wrong data. Worse, the naive version
  does not even work: a single-year scrape was a silent no-op at the database layer.
- **Database views as the correctness layer.** You cannot create a view named `games` while the
  table `games` exists, and creating objects in a database whose alembic head DELETEs every row
  is an ownership hazard a rib should not take.
- **Workflow nodes that publish snapshots.** A bash node is a subprocess — no snapshot manager,
  no rib context, no module state. The write path is an in-process tool named in the prompt
  node's whitelist, which is how chamber does it.
- **An LLM-authored HTML page.** A 262 KB page cannot round-trip through a tool result, and
  re-authoring one per tick would silently redesign it every week.
- **A starting-XI section with eleven seats.** The failure mode is backwards: 3,556 team-games
  flag exactly 11 starters, **674 flag more** (up to 22), only 45 flag fewer. A section designed
  for eleven would render eighteen. Cap at 11 by minutes and surface the overflow as a warning.

## The risk with no mitigation

**Nobody opens it.**

Every other risk in this brief has a mitigation with a line number attached. This one does not.
The whole design points at it: the "since you last looked" register exists precisely so that
opening the tab on a Sunday morning immediately says something you did not already know.

So here is the falsifiable failure condition, offered up front rather than discovered in
December:

> **If that register is ever empty on a Monday in October, the system failed at its actual job.**

That is measurable. Judge it by that, not by whether the charts are pretty.
