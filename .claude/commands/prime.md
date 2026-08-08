---
description: Come up to speed on Touchline — measures live state rather than reciting documented numbers
allowed-tools: Bash, Read, Glob, Grep
---

# Prime — Touchline

Bring yourself up to speed on this effort in one pass, at the start of a session or after a
compaction.

## What makes this different from a generic prime

A generic prime maps an unfamiliar codebase. **This codebase is already mapped** — the layout
is in `CLAUDE.md`, the design is in `docs/specs/touchline-rib.md`, and the plan is in beads.
Re-deriving any of that is wasted context.

What actually goes stale here is **state**: which work is actionable, what is in flight, and
above all *what the data currently looks like*.

So this command has one rule that overrides everything else:

> **Measure. Do not recite.**
>
> Never report a defect figure you read in a document. Every number in your summary must come
> from a query you just ran. This project has been burned five times by a figure that was true
> when written and false when used — including one that would have deleted 79 legitimate games
> and one that would have collapsed 40 real fixtures.
>
> If a document disagrees with the database, **the database wins and the document is a bug** —
> say so and offer to fix it.

## Constraints

- **Do not read source files.** Not `.py`, not `.ts`, not tests. This is orientation, not
  investigation. If a task needs source, that is the task's job.
- **Do not launch subagents or workflows.** Read-only, single pass.
- **SELECT only.** Never write to `ed_insights`.
- Target well under 15k tokens. Prefer one batched command over many small ones.
- Skip anything already in your context. If `bd prime` output is present from the SessionStart
  hook, do not re-run it — the memories are already loaded.

## Step 1 — The narrative and the queue

Read [`STATUS.md`](../../STATUS.md) in full. It is short and it is the *why*.

Read only the head of [`ROADMAP.md`](../../ROADMAP.md) — through the "Pick up next" table. The
per-epic detail below that is reference, not orientation.

## Step 2 — Live state, one batch

```bash
cd "$(git rev-parse --show-toplevel)"
echo "=== BRANCH / RECENT ==="; git branch --show-current; git log --oneline -5
echo "=== OPEN PRs ==="; gh pr list --json number,title,isDraft,statusCheckRollup \
  --jq '.[] | "#\(.number) \(if .isDraft then "[draft] " else "" end)\(.title) — \([.statusCheckRollup[]?.conclusion] | if length==0 then "no checks" else (map(select(.=="SUCCESS")) | length | tostring) + "/" + (["x"]|length|tostring) end)"' 2>/dev/null || echo "(gh unavailable)"
echo "=== IN PROGRESS ==="; bd list --status in_progress 2>/dev/null | head -12
echo "=== READY ==="; bd ready --exclude-type=epic 2>/dev/null | head -14
echo "=== LEARNED THE HARD WAY ==="; bd memories 2>/dev/null | head -30
echo "=== KEELSON ==="; keelson workflow status 2>/dev/null | head -6 || echo "(server down or unreachable)"
ls .keelson/workflows/ 2>/dev/null
```

If `gh pr list` shows an open PR whose checks are green, say so explicitly — an unmerged green
PR is the cheapest available progress and is easy to forget.

## Step 3 — Measure the data yourself

Run this. Do not skip it and do not substitute figures from `STATUS.md`, the spec, or your
own memory of earlier in the session.

```bash
psql -U lume -d ed_insights -tA <<'SQL'
\echo '-- metric | now | target'
\echo -n 'games total|'
select count(*)||'|2140 (2098 after phantom deletion)' from games;
\echo -n 'phantom rows (year outside season_year..+1)|'
select count(*)||'|0' from games where date is not null
  and extract(year from date) not in (season_year, season_year+1);
\echo -n 'date IS NULL|'
select count(*)||'|0' from games where date is null;
\echo -n 'is_conference_game NULL|'
select count(*)||'|0, gender+season aware' from games where is_conference_game is null;
\echo -n 'red cards stored|'
select count(*)||'|158 (166 markers less 8 in phantom dirs)' from game_events where event_type='red_card';
\echo -n 'HU+HUW rows claiming home|'
select count(*)||'|roughly half of 337' from games g join schools s on s.id=g.school_id
  where s.abbreviation in ('HU','HUW') and g.home_team='Harding';
-- The pair MUST be unordered (least/greatest). Grouping by home_team and then asking
-- for count(distinct home_team) > 1 is self-contradictory — rows that disagree on home
-- land in different groups, so it returns 0 and reads as "already fixed". That exact
-- bug was written here once and caught only because this command insists on measuring.
\echo -n 'two-perspective fixtures contradicting on home|'
select count(*)||'|0 (523, measured with all 2,140 games dated; 471 across 2,029 dated games before PR #42)' from (
  select s.gender, g.date, least(g.home_team,g.away_team) a, greatest(g.home_team,g.away_team) b
  from games g join schools s on s.id=g.school_id where g.date is not null
  group by 1,2,3,4 having count(*)>1 and count(distinct g.home_team)>1) d;
-- Note this one groups on the ORDERED (home, away) triple deliberately: it mirrors the
-- data-integrity `duplication` check's own key, so the numbers are comparable to it.
\echo -n 'duplicate groups (gender, date, home, away)|'
select count(*)||'|138 now, 98 after phantoms go' from (select s.gender,g.date,g.home_team,g.away_team
  from games g join schools s on s.id=g.school_id where g.date is not null
  group by 1,2,3,4 having count(*)>1) d;
\echo -n 'score disagreements, gender-aware|'
select count(*)||'|0 (39 gender-blind are all m-vs-w pairs)' from (select s.gender,g.date,g.home_team,g.away_team
  from games g join schools s on s.id=g.school_id where g.date is not null group by 1,2,3,4
  having count(*)>1 and count(distinct coalesce(g.home_score,-1)||':'||coalesce(g.away_score,-1))>1) d;
\echo -n 'events in db|'
select count(*)||'|22782 to match the parquets (28 lost at load)' from game_events;
SQL
```

Any metric already at target is finished work — say so rather than reporting it as a defect.
Any metric that has moved *away* from target is a regression and is the most important thing
on the page.

## Step 4 — Report

Six short sections. No preamble, no restating this command back.

1. **Where we are** — one paragraph, from STATUS.md, in your own words.
2. **In flight** — claimed beads, open PRs and their CI, any running Keelson workflow.
3. **Data vitals** — the table from step 3, marking each row on-target / outstanding /
   regressed. Stamp it: *measured at &lt;time&gt;*.
4. **Next** — the two or three highest-value actionable beads with their ids, and why those
   rather than the others. Respect the dependency order; `bd ready` already does.
5. **Drift** — any place a committed document disagrees with what you just measured. This
   section is the point of the whole command. If it is empty, say "none" — do not pad it.
6. **Days to kickoff** — season starts **27 August 2026**.

Then stop and wait. Do not start work off the back of a prime unless asked.

## If something is missing

- `bd` not found → beads is not installed; the plan is still readable in `.beads/issues.jsonl`
  and `ROADMAP.md`.
- Postgres unreachable → say so plainly and mark every vital *unmeasured*. **Do not fall back
  to documented figures** — an unmeasured vital reported as a number is exactly the failure
  this project keeps making.
- Keelson down → `keelson start`. Note that a restart cancels any in-flight workflow run, so
  check `keelson workflow status` before restarting.
