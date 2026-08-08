# Where we are

*Plain-language status. Updated as things land — last updated 8 August 2026.*

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

- **Which team was home** is invented, not observed — right about a third of the time.
  The scraper assumed whichever school's website it read must be the home team.
- **Which team a player played for** is swapped in 723 games; the two rosters wear each
  other's names.
- **Red cards from twelve of the thirteen programmes are filed as yellow** — 166 of them in
  the cached pages, of which 158 survive once duplicate copies are deleted. Harding's own 43
  are stored correctly, because Harding is the one programme on a different platform. So the
  repair takes the database from 43 red cards to 201, not to 158.
- **28 events** are destroyed on every database load, one of them a goal.

None of it is lost. It is all in the 1.1 GB of web pages already saved on disk — it just
got labelled wrong on the way in. **No re-scraping is needed.**

A dashboard built on this today would confidently show you a home record that is fiction.

## Is this cleaning the data, or the process that broke it?

Both, and mostly they are the same action. The database is *derived* — the real record is
those saved pages. So for nearly every defect, "fix the data" means "fix the parser, then
re-read the pages." Patching rows alone would be worse than useless: the next scrape would
recreate the mess.

Exactly one item is pure cleanup — deleting 42 duplicate rows and the poisoned cache
folders that produced them. Everything else is a code fix.

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

Three times now, in different disguises: **a rule that looks obviously right, where nobody
asked what legitimate data it excludes.**

- A phantom-row detector written as `date year != season year` would have deleted **79 real
  games** — nine programmes played their COVID season in spring, correctly filed under the
  previous year.
- A match key on `(date, two schools)` without **gender** would have collapsed **40 real
  fixtures** — a men's and a women's match, same day, same two schools, 39 of them with
  different scores.
- A test reporting `0` when it could not look, in the same words it uses for a genuine zero.

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

## What is next

1. **Four measurement bugs in the inspectors** — checks that measure the wrong thing, so
   they are wrong on every run rather than only when something breaks. Notably the oracle
   that produced the headline home/away figure is in neither workflow, so that number is not
   currently reproducible by the instrument meant to grade its repair.
2. **The data repair itself** — parser and loader fixes, then re-read the cached pages.
3. **The rib** — the ledger, the boards, the chat.

## The free regression test the repair creates

**586 fixtures were scraped twice**, once from each school's site — two independent
transcriptions of the same match. Once the labels are fixed those pairs must agree forever.
If a future scrape breaks the roster logic again, the two perspectives stop matching and it
shows up immediately. That is not a one-time cleanup; it is a regression test the season
generates by itself.

## Getting back up to speed

```bash
bd ready --exclude-type=epic   # what can be started right now
bd show <id>                   # mechanism, evidence, acceptance criteria
bd memories                    # what we have learned the hard way
python3 scripts/roadmap.py     # regenerate ROADMAP.md
```

There is also a live board in Keelson — open `http://127.0.0.1:7878`, the **Chamber**
surface, and the `touchline-queue` lens. It reads the work queue directly rather than
summarising a snapshot, and refreshes itself every 30 minutes while pinned.

## One caveat on trust

The verdict *"the numbers are true, the labels are wrong"* is directionally right but was
an overclaim as originally stated, and the spec now says so. The labels half is fully
supported. The numbers half rests mainly on **139 fixtures** where two different platforms
*and* two different parsers agree — real evidence, but narrower than "two unrelated
websites" implied, since 454 of the pairs are the same parser reading two copies of the
same platform.
