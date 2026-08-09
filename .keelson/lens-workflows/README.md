# Chamber lens workflows

These are **not** loaded from here. Chamber contributes a lens-refresh workflow only from
its own directory, so a file must be copied to:

```
~/.keelson/rib-chamber/lens-workflows/<name>.yml   →  contributed as chamber-lens-<name>
```

The filename decides the contributed name, overriding the file's own `name:` field. The
harness runs a pinned lens panel's refresh **only** for a rib-contributed workflow, so a
copy left in the global workflows directory will never drive a cadence however correct it is.

Contributions are collected at startup, so after adding or editing one:

```bash
keelson workflow status          # check nothing is mid-run — a restart CANCELS running workflows
cp .keelson/lens-workflows/vitals.yml ~/.keelson/rib-chamber/lens-workflows/vitals.yml
keelson stop && keelson start
```

**The copy is the deploy — a restart alone does nothing.** Nothing syncs these two paths and
nothing warns you when they disagree, so each can silently run ahead of the other. On
2026-08-09 both had: the deployed copy carried a duplicate-groups target the repo copy never
received, while the repo copy carried an events target the deployed copy never received, and
the board had been grading the *repaired* event count against the pre-repair target — emitting
a REGRESSED alarm on finished work. Editing the repo file and restarting *feels* like fixing
the instrument and changes nothing about what is actually grading the data.

So before trusting a board, confirm the two agree:

```bash
diff .keelson/lens-workflows/vitals.yml ~/.keelson/rib-chamber/lens-workflows/vitals.yml
```

They live in the repo so they survive the machine, and so a change to one shows up in review
like any other code.

## beads.yml → `chamber-lens-beads`

Backs the `touchline-queue` lens. A deterministic bash node measures the work queue with `bd`,
and exactly one agent turn composes the board from that measurement — the numbers are never the
agent's to invent. Pin the lens on the Chamber surface and it refreshes every 30 minutes.

Enhanced 2026-08-08 with learnings from [mantoni/beads-ui](https://github.com/mantoni/beads-ui)
(bead tl-6uh): the blocked lane is the **union** of dependency-blocked (`bd blocked`, which also
names each issue's blockers) and status-blocked (`bd list --status blocked`) — status alone
silently omits dependency-blocked work; ready rows carry an `unlocks:N` dependent-count so
leverage is measured, not asserted; the KPI header comes from one `bd status --json` call; and
the board adds a recently-closed momentum strip and a `bd stale` abandoned-work alarm. Every
section is fail-closed: a dead `bd` renders seven UNMEASURED sections, never an empty-but-healthy
board (proven, like vitals.yml, by running it against a stubbed failing `bd`).

Note the hardcoded repo path in its bash node: a panel refresh passes no project, so the
workflow has to know where to `cd`.

## vitals.yml → `chamber-lens-vitals`

Backs the `data-vitals` lens: the repair burn-down, measured live — the same table `/prime`
step 3 produces, without needing a Claude session. A bash node runs every metric as a
SELECT-only query **fail-closed per metric** (a psql failure or empty capture renders
`UNMEASURED`, never `0` — proven by pointing it at a nonexistent database) and computes the
verdict deterministically by distance-to-target against a worst-known baseline: `OK`,
`OUTSTANDING`, `REGRESSED`, or `UNMEASURED`. The agent turn only renders; it never derives
a number or a verdict.

Targets carry the 2026-08-08 corrections: red cards target **201** (43 StatCrew reds were
never wrong and are disjoint from the 158 recoverable SideArm reds — see
`bd memories red-cards`), and the duplicate/games targets state both their current-expected
and post-phantom-deletion values.
