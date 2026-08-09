# Where we are

*Plain-language status. Updated as things land — last updated 9 August 2026.*

This page is the one to read first if you have been away. For the task list see
[ROADMAP.md](ROADMAP.md); for the pitch — the thesis, the board mockups, the nine open forks
and what we chose not to build — see [docs/BRIEF.md](docs/BRIEF.md); for the design see
[docs/specs/touchline-rib.md](docs/specs/touchline-rib.md).

---

## What we are building

A page you open on a Sunday morning that tells you what happened in GAC soccer this
week — the table, who won, what moved since you last looked — and a chat box where you
can ask questions about it. Updating itself through the season without anyone touching it.

It ships as a **Keelson rib** called Touchline, so it lives in the agent workbench you
already run rather than as a fifth app to keep alive. Both genders, seven programmes each.

Season starts around **27 August 2026**.

## Why we are not building that yet

The database has seven years of soccer in it and **the scores are right**. But most of
what *describes* those scores is wrong:

- ~~**Which team was home** is invented, not observed — right about a third of the time.
  The scraper assumed whichever school's website it read must be the home team.~~
  **Repaired 9 Aug** — derived from the source venue instead. Cross-perspective
  contradictions 523 → **0**, Harding 337/337 → **164/337**, every programme now at a
  plausible 38–48% home share, and 53 genuinely neutral fixtures marked as such.
- ~~**Which team a player played for** is swapped in 723 games; the two rosters wear each
  other's names.~~ **Repaired 8 Aug** — 723 → 0, captions 739 → 0.
- **Red cards from eleven of the thirteen programmes are filed as yellow** — **158** of them
  in the cached pages, measured across 2,098 pages read now that the phantom copies are
  gone. *(This read 166 before 9 Aug; 8 of those were duplicate transcriptions living in the
  purged cache folders, exactly as `tl-65z.6` predicted, so the check's convergence target is
  now a satisfiable 158 = 158.)* Harding's own 43 are stored correctly, because Harding's two
  programmes are the only ones on a different platform. So the repair takes the database from
  43 red cards to **201**, not to 158.
  **Half-repaired 9 Aug** — the parser now reads the card type from the `penalty-type` CSS
  class instead of hardcoding yellow
  ([#64](https://github.com/ed-insights-ai/ed-insights-platform/pull/64)), so cards scraped
  from here on are right. **The database is untouched at 43** and the backfill is still
  outstanding, because the guarded regeneration turned up a change nobody had approved — a
  player-name whitespace difference on 6 non-card events — and refused to write rather than
  load a diff it could not fully account for (`tl-5m9`). That refusal is the guard working.
- ~~**28 events** are destroyed on every database load, one of them a goal.~~ **Recovered
  9 Aug** — the re-merge that the phantom purge required also re-ran the fixed event-id
  hash, and 27 real events came back (1 goal, 6 substitutions, 20 yellow cards). The 28th
  lived inside a phantom game and was deleted with it. Per-season parquets, merged export
  and Postgres now agree exactly at 22,460.

The un-struck figures are **pre-repair baselines, frozen as scraped** — they describe the
defect, not the current database. The live state of every one of these metrics, with a
computed verdict, is the **`data-vitals` lens** on the Chamber surface, measured against
Postgres every half hour. When this file and that lens disagree, the lens is right and
this file has a bug worth fixing.

None of it is lost. It is all in the 1.1 GB of web pages already saved on disk — it just
got labelled wrong on the way in. **No re-scraping is needed.**

The home record is no longer fiction. The card record still is — but the parser that made it
fiction is fixed, so it is now a backfill waiting on one unexplained diff, not an open wound.

## Is this cleaning the data, or the process that broke it?

Both, and mostly they are the same action. The database is *derived* — the real record is
those saved pages. So for nearly every defect, "fix the data" means "fix the parser, then
re-read the pages." Patching rows alone would be worse than useless: the next scrape would
recreate the mess.

Exactly one item was pure cleanup — deleting 42 duplicate rows and the poisoned cache
folders that produced them. **That one landed 9 Aug.** Everything else is a code fix.

**The root cause, named:** the pipeline was built *school-centric* — point it at Harding's
site, read Harding's schedule. That is a fine way to scrape and a poor way to model a
*match*, because a match has two sides and the scraper only ever had one in hand. It filled
in the other side by assumption, and every one of those assumptions became a defect.

## The bit that took the longest, and why

To fix the data you need a way to check whether you fixed it. We had two automated
inspectors — 21 tests over the database and the cached pages. Every target in the repair
plan is written as a number from those tests.

**An adversarial audit found 19 of the 21 would report "all clear" when they could not run
at all.** Like a smoke detector whose green light stays on after the battery dies: it is not
telling you there is no fire, it is telling you nothing, in a way that looks like good news.
Proven by pointing a test at a database that does not exist — it printed a clean pass.

Fixing that took three passes, each catching a class the previous one structurally could not:

1. **Assert the answer is not empty** — catches a dead database.
2. **Guard the source, not the value** — catches a missing or unreadable folder. A file
   count emits `0`, never empty, and `0` is also the healthy answer.
3. **Check the command's exit status, and give every count a denominator** — catches a
   search that ran but could not read.

That third one produced the most durable idea here: **a bare count is an assertion with its
evidence stripped off.** "0 red cards" is unreadable. "0 red cards across 2,140 pages read"
and "0 red cards across 3 pages read" are obviously different claims.

### The mistake that keeps recurring

Nine times now, in different disguises: **a rule that looks obviously right, where nobody
asked what legitimate data it excludes** — or an acceptance number stated without the
condition that makes it true.

- A phantom-row detector written as `date year != season year` would have deleted **79 real
  games** — nine programmes played their COVID season in spring, correctly filed under the
  previous year.
- A match key on `(date, two schools)` without **gender** would have collapsed **40 real
  fixtures** — a men's and a women's match, same day, same two schools, 39 of them with
  different scores.
- A test reporting `0` when it could not look, in the same words it uses for a genuine zero.
- A duplicate-group target of "98" that is only reachable *after* the phantom rows are
  deleted. **This very bullet then went stale, which is the subtlest version yet:** it said
  "138 is correct today", and today it is **641** — because the home/away repair made the two
  perspectives of a fixture *agree*, so they now collapse into the same ordered group instead
  of landing in two different ones. The number moved because the repair worked. Anyone
  reading 138 flatly would report a catastrophic regression.
- An acceptance criterion carrying "471 → 0 across 569 two-perspective fixtures" when the
  measured figures were **523 → 0 across 641** — the criterion was written against 2,029
  dated games, before the 111 restorations. Caught in a pre-dispatch audit; had it run, a
  correct repair would have read as a 52-fixture overshoot.
- A red-card target of "158" that silently omits the **43 already-correct** cards, so the
  true post-repair total is **201** and a correct result would read as a 43-row overcount.
- A verification query that grouped by `home_team` and then asked whether `home_team` varied
  — self-contradictory, so it returned a confident **0** where the real figure is **471**
  — itself measured across 2,029 dated games, and **523** now that all 2,140 are dated.
- The project's own headline figure, 651 of 1,745, which turned out to depend on two
  unstated conventions: venue-less pages counted as away rather than held out, and a name
  match that silently dropped 41 games spelled differently.
- **The ninth, and the most instructive, because the corrected answer was already written
  down.** PR #64's description recited "166 markers = 166 db rows" three times, having pulled
  the acceptance criteria from `tl-9ap`'s **description** while the bead's own **notes**,
  directly below, corrected it to 158 / 201. The same PR said "the existing 158 SideArm rows"
  in an adjacent paragraph — it contradicted itself on the same page and read as authoritative
  in both places. Caught and rewritten before merge. A correction is only as good as the
  chance that whoever reads the record scrolls far enough to find it.

The tell is always the same: the number looks clean, and nobody asks what it had to exclude
to look that way.

It is now written into [CLAUDE.md](CLAUDE.md) as a standing check: *ask of every rule, what
valid row does this throw away?*

## Done so far

- **Migration 005 defused** ([#32](https://github.com/ed-insights-ai/ed-insights-platform/pull/32)) — it deleted every row in both directions and ran on
  every container start. Nothing was broken yet; it was waiting to be.
- **The scraper catches the lie at source** — a URL for a season that does not exist quietly
  redirects to whatever season is current, which is how 42 games dated 2025 got filed under
  2020. It now checks.
- **The inspectors fail closed** — all 21 checks, verified against a failed producer, with
  real-data numbers unchanged.
- **Work is tracked in [beads](https://github.com/gastownhall/beads)** — a dependency-aware tracker, so `bd ready` only ever shows
  work whose prerequisites are actually done. That matters here because the repair has a
  strict order and doing it out of order produces plausible-looking wrong answers.
- **The first data repair landed (8 Aug)** — the 111 games with no date and a literal
  `'NaN'` venue, restored from the cached pages
  ([#42](https://github.com/ed-insights-ai/ed-insights-platform/pull/42)). It went through
  the full factory loop: adversarial audit (which corrected the bead's own mechanism note),
  a Keelson `bead-work` run with a human approval gate, a three-lens review, and a
  review-bot pass — and the run itself found a constraint nobody had written down
  (Postgres rejects the raw `Sep. 1, 2016` form, so dates must be normalised before load).
  The `data-vitals` lens shows the first repair metric at target.
- **The identity canon landed (8 Aug)** — one authoritative answer to "which programme is
  this row about?", committed as `canon.json`
  ([#46](https://github.com/ed-insights-ai/ed-insights-platform/pull/46)): all 221 distinct
  opponent strings across five columns resolve to a gender-free institution slug, an explicit
  non-member mark, or an evidence-backed artifact note, with 26 hand-adjudicated near-misses.
  The pre-dispatch audit mattered again: the bead as filed would have covered only the 193
  strings in `games` and keyed on gendered abbreviations — passing its own acceptance criteria
  while silently failing player-team attribution, its primary consumer. This unlocks the
  widest gate in the tracker: the canonical match key, roster attribution, matcher
  unification, and the conference backfill lane all sit directly behind it.
- **The roster swap is repaired (8 Aug)** — the largest single defect in the database:
  in 723 games the two rosters wore each other's names, because the parser corrected the
  home/away labels but never reordered the player tables beneath them
  ([#48](https://github.com/ed-insights-ai/ed-insights-platform/pull/48)). The fix reorders
  the rosters with the same swap decision, and the PR also had to *build its own proof*:
  the acceptance criterion cited an HTML-caption check that did not exist yet, so the run
  committed it — every SideArm page's two goalie captions compared against the stored
  labels, with a denominator on every bucket. Measured after merge and reload: arithmetic
  gate swapped **723 → 0** and captions **739 → 0**, aligned 1,803 of 1,803 pages, across
  exactly 2,140 games. The 21 games whose player sums genuinely reconcile with neither
  team are triaged separately. The already-correct StatCrew games stayed correct: 0
  swapped of exactly 337.
- **The defining defect is fixed (9 Aug)** — home/away is now derived from the **source
  venue city** compared against each school's own home city, rather than from row order or
  from whichever school's site was being read
  ([#52](https://github.com/ed-insights-ai/ed-insights-platform/pull/52)). Measured against
  Postgres after merge: cross-perspective contradictions **523 → 0**, the logical
  impossibility of both rows claiming home **505 → 0**, and `home_team='Harding'` for HU+HUW
  **337/337 → 164/337**. An audit past those gates — because all three could pass while every
  *non*-Harding school was uniformly forced to away — confirms every programme now sits at a
  plausible **38–48%** home share, with 53 genuinely neutral fixtures carrying an explicit
  `neutral_site` flag instead of being forced to a side. Scores were untouched and no row was
  lost. Two further repairs landed the same night: the preseason redirect blind spot
  ([#53](https://github.com/ed-insights-ai/ed-insights-platform/pull/53)) — whose two deleted
  season slugs proved safe because FHSU's 24 and OBU's 18 `season_year=2020` rows are
  *exactly* the 42 known phantoms — and the event-id collision that destroys 28 events
  ([#54](https://github.com/ed-insights-ai/ed-insights-platform/pull/54)), whose parser half
  merged while its regeneration half was deliberately deferred rather than run against a base
  that predated #52 and would have silently restored all 523 contradictions.

- **The phantom rows are gone, and the lost events came back (9 Aug)** — the only pure-cleanup
  item in the plan. 42 duplicate games (FHSU 2020's 24 and OBU 2020's 18, all scraped from
  `/stats/2025/` pages a preseason redirect misfiled) deleted along with the two poisoned
  cache folders that produced them, and their 1,604 player / 84 team / 321 event children.
  The delete set was **pinned, not detected**: derived twice independently — Postgres
  twin-verification against the real 2025 rows, and the `game_id` column of the deleted
  parquets — which named identically the same 42, and executed behind three transactional
  guards that abort rather than delete if the count is not 42, if any row lacks a verified
  twin, or if any of the 79 legitimate spring-2021 COVID games appears. Measured after
  reload: phantoms **42 → 0**, same-school duplicate groups **40 → 0**, duplicate groups
  **641 → 621** (every one now a genuine two-school pair), doubled player aggregates
  **574 → 0**, 0 orphaned children, and the 79 COVID games untouched. Because purging the
  phantoms required re-merging the parquets, the same pass ran the fixed event-id hash from
  PR #54 and recovered **27 real events** — events dropped at merge **28 → 0**, and the
  three corpora now agree exactly at 2,098 / 75,982 / 22,460 / 4,196 with `game_id` sets
  identical in both directions. Both protected invariants held at 0 throughout: cross-perspective
  home contradictions and gender-aware score disagreements.

- **Three ran in parallel and all three landed (9 Aug)** — the first time work was fanned out
  rather than queued, in three isolated worktrees off one commit, each with its own approval
  gate.
  - **A grader for the conference backfill** ([#62](https://github.com/ed-insights-ai/ed-insights-platform/pull/62)) —
    `data-integrity` counted NULLs in `is_conference_game` and nothing else, so a *wrong*
    backfill would have read green. The new check re-derives the flag independently,
    gender- and season-aware, and alarms on disagreement. It verdicts **warn** while the
    column is still all-NULL rather than `ok`, which is the difference between "correct" and
    "could not look". Acceptance is proven by pytest over synthetic flipped rows, since there
    is nothing live to flip yet. It also re-measured its own bead's stale figures — 1,430 /
    1,533 / 103 became **1,387 / 1,467 / 80** on the post-purge corpus — and hardcodes none
    of them. Checks: 10 → **11**.
  - **Parquets are build output** ([#63](https://github.com/ed-insights-ai/ed-insights-platform/pull/63)) —
    528 derived parquet files untracked and gitignored, superseding ADR-004 with ADR-009.
    They were burying the ~15 reviewable files in every repair PR under 378 binary ones, and
    the review bot had been silently refusing to review since PR #52. A fresh clone now
    bootstraps with `uv run reparse`, which walks the committed HTML cache **offline** and
    rebuilds all four corpora exactly (2,098 / 75,982 / 22,460 / 4,196, verified from a
    zero-parquet checkout). `data/source_urls.csv` preserves all 2,098 source URLs, which the
    cache does not carry and the API serves.
  - **The red-card parser** ([#64](https://github.com/ed-insights-ai/ed-insights-platform/pull/64))
    — described above; parser fixed, backfill outstanding.

  What the fan-out bought that a queue would not have: #63's investigation discovered that
  `uv run scrape` is **not** offline — discovery hits the network before `use_cache` is ever
  consulted — while #64 was actively planning a backfill that assumed it was. Neither run
  could see the other. Caught at the approval gate, and now written into
  [CLAUDE.md](CLAUDE.md).

## What is next

1. ~~Four measurement bugs in the inspectors~~ — **fixed 8 August**: the archive check,
   the gender-aware duplication key, honest cross-source independence, and a new
   `site-city-oracle` that finally measures the defining home/away defect. The
   conference-backfill detector **landed 9 Aug** (#62). One check remains: card fidelity
   (`tl-65z.6`), whose 166 target still double-counts the 8 phantom markers.
2. **The data repair itself** — parser and loader fixes, then re-read the cached pages.
   The two immediate blockers are both new and both small: `tl-5m9`, the unexplained
   whitespace diff on 6 events that is holding up the red-card backfill, and `tl-2tc`, the
   membership-windows table the conference backfill needs now that its grader exists.
3. **The rib** — the ledger, the boards, the chat.

## The free regression test the repair creates

**621 fixtures were scraped twice**, once from each school's site — two independent
transcriptions of the same match. Once the labels are fixed those pairs must agree forever.
If a future scrape breaks the roster logic again, the two perspectives stop matching and it
shows up immediately. That is not a one-time cleanup; it is a regression test the season
generates by itself.

*(This read **586** until 9 Aug — measured before the 111 date restorations, since an
undated row cannot be paired with anything. It then read 641 groups, of which 601 were
genuine two-school pairs and 40 held two rows from the same school, all 40 the work of the
42 phantom rows. **The purge landed the same day and the prediction held exactly**: measured
after it, **621 groups, every one a genuine two-school pair, 0 same-school duplicates**.
That is the figure to hold the season to.)*

## Getting back up to speed

```bash
bd ready --exclude-type=epic   # what can be started right now
bd show <id>                   # mechanism, evidence, acceptance criteria
bd memories                    # what we have learned the hard way
python3 scripts/roadmap.py     # regenerate ROADMAP.md
```

There are two live boards in Keelson — open `http://127.0.0.1:7878`, the **Chamber**
surface: the **`touchline-queue`** lens (the work queue, read directly from beads) and the
**`data-vitals`** lens (every repair metric measured against Postgres, with a computed
verdict per row — the *live* values; this file keeps only the frozen pre-repair
baselines). Both refresh every 30 minutes while pinned.

Keelson also carries the project's standing constitution in its **project notebook**,
injected into every agent turn it runs, and a **governed memory**: `bead-work` runs leave
a pending work-log trail and recall only human-confirmed lessons, so an unattended run can
never teach the next one something nobody vetted. Review pending memories on the Memory
surface.

## One caveat on trust

The verdict *"the numbers are true, the labels are wrong"* is directionally right but was
an overclaim as originally stated, and the spec now says so. The labels half is fully
supported. The numbers half rests mainly on **139 fixtures** where two different platforms
*and* two different parsers agree — real evidence, but narrower than "two unrelated
websites" implied, since 454 of the pairs are the same parser reading two copies of the
same platform.
