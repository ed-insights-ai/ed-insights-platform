# Touchline — Roadmap

*Generated from beads on 2026-08-08 by `scripts/roadmap.py`. Do not edit — edit the issues with `bd` and regenerate.*

The goal: turn an amnesiac dataset into a season you can ask questions about. See [`docs/specs/touchline-rib.md`](docs/specs/touchline-rib.md) for the build plan and [`ADR-008`](docs/decisions/ADR-008-touchline-keelson-rib.md) for why.

**0/64 tasks complete** across 13 epics · **13 ready to start** · 51 waiting on a blocker

## Start here

Work with no unmet blockers, highest priority first:

| | Issue | Task | Epic |
|---|---|---|---|
| P0 | `tl-37d` | Fix SideArm rosters labelled with each other's team in 723 games (gh-21) ([#21](https://github.com/ed-insights-ai/ed-insights-platform/issues/21)) | S0.5 |
| P0 | `tl-3zm` | Purge 712 retired-ordinal rows from exported parquets (gh-27) ([#27](https://github.com/ed-insights-ai/ed-insights-platform/issues/27)) | S0.5 |
| P0 | `tl-65z.1` | Make all 21 checks fail CLOSED when a query fails | The measuring instrument |
| P0 | `tl-ath` | Build the authoritative opponent-string identity map (canon.json) | S0.5 |
| P0 | `tl-da9` | Close the preseason blind spot in the season assertion | S0.5 |
| P0 | `tl-irx` | Create keelson-rib-touchline on the ed-insights-ai organization | S1 |
| P0 | `tl-oyr` | Scrape reports success on partial and rejected runs (gh-17) ([#17](https://github.com/ed-insights-ai/ed-insights-platform/issues/17)) | S0 |
| P0 | `tl-vkt` | Fix 111 games with NULL date and venue='NaN' (gh-24) ([#24](https://github.com/ed-insights-ai/ed-insights-platform/issues/24)) | S0.5 |
| P1 | `tl-09k` | Stop the loader writing literal 'NaN' into nullable text columns (gh-25) ([#25](https://github.com/ed-insights-ai/ed-insights-platform/issues/25)) | S0.5 |
| P1 | `tl-9ap` | Recover 166 SideArm red cards stored as yellow (gh-23) ([#23](https://github.com/ed-insights-ai/ed-insights-platform/issues/23)) | S0.5 |
| P2 | `tl-ce3` | Stop coercing missing shots_on_goal to 0 (gh-29) ([#29](https://github.com/ed-insights-ai/ed-insights-platform/issues/29)) | S0.5 |
| P3 | `tl-3rk` | Parse SideArm play-by-play — 59,844 substitutions discarded (gh-28) ([#28](https://github.com/ed-insights-ai/ed-insights-platform/issues/28)) | S0 |

```bash
bd ready --exclude-type=epic   # the live version of this table
bd show <id>                   # full mechanism, evidence, acceptance
bd update <id> --claim         # take it
```

## Epics

### The measuring instrument — fix the harness before it grades the repair

`tl-65z` · 0/8 complete

Every acceptance criterion in the repair plan is phrased as a before/after number
from `.keelson/workflows/data-integrity.yml` (9 checks) and `ground-truth.yml` (13 checks).
An adversarial audit on 2026-08-08 found the instrument is not fit to grade the repair.

- [ ] `tl-65z.1` **P0** Make all 21 checks fail CLOSED when a query fails
- [ ] `tl-65z.2` **P0** Fix the archive check — its predicate can never fire — *blocked by `tl-65z.1`*
- [ ] `tl-65z.3` **P0** Gender-aware duplication key — 176 → 98, and 39 false alarms → 0 — *blocked by `tl-65z.1`*
- [ ] `tl-65z.4` **P0** Cross-source — report real independence, not 'two unrelated websites' — *blocked by `tl-65z.1`*
- [ ] `tl-65z.5` **P0** Build the Site: city oracle — the defining defect has no check — *blocked by `tl-65z.1`*
- [ ] `tl-65z.7` **P0** A detector for a wrong is_conference_game backfill — *blocked by `tl-ath`, `tl-65z.1`*
- [ ] `tl-65z.6` **P1** Card fidelity — the 166 target double-counts 8 phantom markers — *blocked by `tl-o23`, `tl-65z.1`*
- [ ] `tl-65z.8` **P1** Correct seven smaller check defects — *blocked by `tl-65z.1`*

### S0 — Pipeline hardening

`tl-ado` · 0/3 complete

The destructive defects, and the ones that make a run lie about its own success. PR #14 (season assertion + merge safety) and PR #18 (repo growth) already landed; this epic is the residue.

- [~] `tl-bbu` **P0** Migration 005 deletes all data in both directions, and runs on every start (gh-19) ([#19](https://github.com/ed-insights-ai/ed-insights-platform/issues/19))
- [ ] `tl-oyr` **P0** Scrape reports success on partial and rejected runs (gh-17) ([#17](https://github.com/ed-insights-ai/ed-insights-platform/issues/17))
- [ ] `tl-3rk` **P3** Parse SideArm play-by-play — 59,844 substitutions discarded (gh-28) ([#28](https://github.com/ed-insights-ai/ed-insights-platform/issues/28))

### S0.5 — Repair the existing data

`tl-5vr` · 0/14 complete

The numbers in ed_insights are true; the labels are wrong. Ground-truth validation established 2,140/2,140 games re-parse exactly and 493/493 fixtures agree on score across two unrelated websites — but home/away, roster attribution and card type are fabricated or inverted. All of it is repairable offline from the 1.1 GB of cached HTML already on disk. No re-scrape required.

- [ ] `tl-37d` **P0** Fix SideArm rosters labelled with each other's team in 723 games (gh-21) ([#21](https://github.com/ed-insights-ai/ed-insights-platform/issues/21))
- [ ] `tl-3zm` **P0** Purge 712 retired-ordinal rows from exported parquets (gh-27) ([#27](https://github.com/ed-insights-ai/ed-insights-platform/issues/27))
- [ ] `tl-4ix` **P0** Backfill is_conference_game — gender-aware and season-aware — *blocked by `tl-ath`, `tl-bbu`*
- [ ] `tl-4jg` **P0** Verify the repair — before/after for every named defect — *blocked by `tl-9ap`, `tl-65z.7`, `tl-09k`, `tl-o23`, `tl-65z.4`, `tl-vkt`, `tl-hbo`, `tl-37d`, `tl-ce3`, `tl-65z.2`, `tl-65z.3`, `tl-bbu`, `tl-qbg`, `tl-65z.5`, `tl-dse`, `tl-3zm`, `tl-65z.1`, `tl-4ix`*
- [ ] `tl-ath` **P0** Build the authoritative opponent-string identity map (canon.json)
- [ ] `tl-da9` **P0** Close the preseason blind spot in the season assertion
- [ ] `tl-dse` **P0** Add player-team attribution to player_game_stats (gh-22) ([#22](https://github.com/ed-insights-ai/ed-insights-platform/issues/22)) — *blocked by `tl-ath`, `tl-37d`*
- [ ] `tl-hbo` **P0** Fix fabricated home/away in both parsers (gh-20) ([#20](https://github.com/ed-insights-ai/ed-insights-platform/issues/20)) — *blocked by `tl-vkt`*
- [ ] `tl-o23` **P0** Delete the 42 phantom rows and their poisoned cache directories (gh-26) ([#26](https://github.com/ed-insights-ai/ed-insights-platform/issues/26)) — *blocked by `tl-da9`*
- [ ] `tl-qbg` **P0** Add the canonical match key column — *blocked by `tl-ath`, `tl-vkt`, `tl-o23`, `tl-bbu`, `tl-hbo`*
- [ ] `tl-vkt` **P0** Fix 111 games with NULL date and venue='NaN' (gh-24) ([#24](https://github.com/ed-insights-ai/ed-insights-platform/issues/24))
- [ ] `tl-09k` **P1** Stop the loader writing literal 'NaN' into nullable text columns (gh-25) ([#25](https://github.com/ed-insights-ai/ed-insights-platform/issues/25))
- [ ] `tl-9ap` **P1** Recover 166 SideArm red cards stored as yellow (gh-23) ([#23](https://github.com/ed-insights-ai/ed-insights-platform/issues/23))
- [ ] `tl-ce3` **P2** Stop coercing missing shots_on_goal to 0 (gh-29) ([#29](https://github.com/ed-insights-ai/ed-insights-platform/issues/29))

### S1 — The canon and the first Observation

`tl-8wq` · 0/5 complete

New repo: **github.com/ed-insights-ai/keelson-rib-touchline**. Package skeleton copied
verbatim from keelson-rib-workiq.

- [ ] `tl-50e` **P0** src/canon.ts — the identity map with NSU reconstruction — *blocked by `tl-71j`, `tl-ath`*
- [ ] `tl-71j` **P0** Package skeleton from keelson-rib-workiq — *blocked by `tl-irx`*
- [ ] `tl-9wn` **P0** bin/observe.ts — write the first immutable Observation — *blocked by `tl-50e`*
- [ ] `tl-irx` **P0** Create keelson-rib-touchline on the ed-insights-ai organization
- [ ] `tl-8wq.1` **P1** src/keys.ts and src/gates.ts — the shared key and gate helpers — *blocked by `tl-71j`*

### S2 — Feed Health, the first board

`tl-c8g` · 0/7 complete

All nine integrity checks with evidence and causing `file:line`, rendered as the first board shipped — before anything pretty.

- [ ] `tl-du4` **P0** src/integrity.ts — nine checks with evidence and file:line — *blocked by `tl-9wn`*
- [ ] `tl-eus` **P0** touchline-refresh in observe-only form — *blocked by `tl-kla`*
- [ ] `tl-kla` **P0** bin/collect-feed.ts and the pressbox surface — *blocked by `tl-du4`*
- [ ] `tl-c8g.1` **P1** bin/collect-ledger.ts — the Observation Ledger board — *blocked by `tl-9wn`*
- [ ] `tl-tre` **P1** Boot self-check — every cadence-bearing region has a matching bound producer — *blocked by `tl-kla`, `tl-c8g.1`*
- [ ] `tl-c8g.2` **P2** touchline-retry-errors — recover the 34 orphaned error blobs — *blocked by `tl-kla`*
- [ ] `tl-c8g.3` **P2** The pressbox Archive region — *blocked by `tl-kla`*

### S3 — The Table and The Slate

`tl-m8v` · 0/4 complete

The first visible payoff of the structural bet: a real Δ against a real prior observation.

- [ ] `tl-6u9` **P1** season-men and season-women surfaces — *blocked by `tl-gjw`, `tl-kxg`*
- [ ] `tl-gjw` **P1** bin/collect-slate.ts — fixtures and results — *blocked by `tl-tre`*
- [ ] `tl-ilb` **P1** The in-process Matchday composer — *blocked by `tl-6u9`*
- [ ] `tl-kxg` **P1** bin/collect-table.ts — the standings board — *blocked by `tl-tre`*

### S4 — The refresh DAG and the wall clock

`tl-bxv` · 0/5 complete

Scheduled freshness end to end, unattended, against the project checkout — the requirement the harness heartbeat structurally cannot meet.

- [ ] `tl-4nx` **P0** GATE — validate --year 2026 against live schedule pages for all 13 programmes — *blocked by `tl-da9`*
- [ ] `tl-8rq` **P0** src/wallclock.ts with last-fired.json — *blocked by `tl-a2n`*
- [ ] `tl-a2n` **P0** The complete 7-node touchline-refresh — *blocked by `tl-4nx`, `tl-4jg`, `tl-eus`, `tl-oyr`*
- [ ] `tl-n8k` **P1** The launchd fallback plist — *blocked by `tl-a2n`*
- [ ] `tl-h9d` **P2** touchline_refresh as a durable op — *blocked by `tl-a2n`*

### S5 — Tools and chat ◆ v1

`tl-268` · 0/5 complete

**This epic is v1.** Cheapest stage, highest usefulness-to-code ratio.

- [ ] `tl-dig` **P1** The twelve tools — *blocked by `tl-9wn`*
- [ ] `tl-268.1` **P2** touchline-scout — the Thursday opponent workflow — *blocked by `tl-dig`*
- [ ] `tl-7c2` **P2** /table, /scout <abbr>, /dispatch — *blocked by `tl-dig`*
- [ ] `tl-fln` **P2** contributeDocs — make the rib self-describing — *blocked by `tl-dig`*
- [ ] `tl-lvx` **P2** Two named agents with a shared seed builder — *blocked by `tl-dig`*

### API correctness

`tl-wk1` · 0/1 complete

The FastAPI service answers "which programme is this row about?" five different ways in five files, none of them shared. The rib's canon supersedes all five for rib purposes, but apps/web reads the API directly and gets the wrong answers today.

- [ ] `tl-vf2` **P1** Unify the five inconsistent team matchers (gh-15, widened) ([#15](https://github.com/ed-insights-ai/ed-insights-platform/issues/15)) — *blocked by `tl-ath`, `tl-hbo`*

### S6 — The Match Page and the Dispatch

`tl-8m4` · 0/5 complete

Once a week the rib publishes a dated, versioned HTML page into Keelson's full-width drawer — the thing you would actually send someone.

- [ ] `tl-1g2` **P2** src/pages.ts + src/tools/emit.ts — the in-process publish seam — *blocked by `tl-dig`*
- [ ] `tl-1sb` **P2** The touchline-dispatch gate/author/publish DAG — *blocked by `tl-ijt`*
- [ ] `tl-ijt` **P2** The forbidden-metric render gate — *blocked by `tl-xb0`*
- [ ] `tl-oow` **P2** src/matchpage.ts — the deterministic match page — *blocked by `tl-1g2`*
- [ ] `tl-xb0` **P2** src/broadsheet.ts — the Sunday dispatch — *blocked by `tl-1g2`*

### S7 — The Race

`tl-00l` · 0/2 complete

The fun. Odds that move every Saturday, and a swing table that turns other people's games into your games.

- [ ] `tl-r5s` **P2** bin/collect-race.ts and race-history.jsonl — *blocked by `tl-xg3`*
- [ ] `tl-xg3` **P2** src/sim.ts — the Monte Carlo — *blocked by `tl-kxg`*

### S8 — Form, the clock, per-team panels, game_id fix

`tl-rbm` · 0/3 complete

Goal-timing segments over the 22,754 parsed event rows **no endpoint has ever aggregated**. Then the deferred D-09 correctness work.

- [ ] `tl-59s` **P3** ctx.registerRegion follow/unfollow with identity-hue allocation — *blocked by `tl-6u9`*
- [ ] `tl-9z1` **P3** Content-derived game_id (D-09) — *blocked by `tl-4jg`*
- [ ] `tl-bky` **P3** bin/collect-form.ts — form strips and goal-timing segments — *blocked by `tl-kxg`*

### S9 — Post-season and deferred correctness

`tl-4a1` · 0/2 complete

In November the Race board flips to a clinch/eliminate grid, then a bracket. By December the Press Box holds ~24 observations, 14 dispatches, ~130 match pages, and a staircase chart of the season's scraping — flat steps and all.

- [ ] `tl-5b5` **P4** Bracket mode and the season-in-review page — *blocked by `tl-r5s`*
- [ ] `tl-i4r` **P4** The sidearm_legacy scraper — so NSU stops being reconstructed

## How this is tracked

Issues live in [beads](https://github.com/gastownhall/beads) under `.beads/` — a dependency-aware tracker, so `bd ready` only ever shows work whose prerequisites are actually done. `.beads/issues.jsonl` is the committed export; the Dolt database itself is gitignored.

The Keelson `bead-work` workflow claims the next ready issue and drives it to a draft PR without being told which one to pick.

GitHub issues are kept for the ones that already had a written-up mechanism; the bead carries `external_ref: gh-N` and the two stay linked. New work goes in beads only.

