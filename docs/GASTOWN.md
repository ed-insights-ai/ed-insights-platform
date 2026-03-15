# Gas Town on Ed Insights Platform

How we use Gas Town to coordinate work on this project.

## The Basics

Gas Town is our multi-agent workspace manager. It gives us:

- **Beads** — issues/tasks tracked in a local database
- **Polecats** — worker agents that implement beads on feature branches
- **Refinery** — merge queue that lands completed work on `main`
- **Witness** — monitor that keeps polecats healthy

## Workflow

```
Decompose → Bead → Sling → Implement → PR → Review → Merge
```

1. **Decompose** work into focused beads
2. **Sling** a bead to a polecat (or let the dispatcher assign it)
3. Polecat **implements** on a feature branch
4. Polecat opens a **PR** and CI runs
5. Human **reviews** the PR
6. **Refinery** merges approved work to `main`

## Bead Sizing Rules

Learned from retro — these matter:

- **No one-liners.** If a change is trivial (rename a variable, fix a typo),
  batch it with other small related fixes. A bead that takes 5 minutes
  wastes more time in overhead than it saves.
- **Sweet spot: 1-4 hours.** Big enough to be meaningful, small enough to
  review in one sitting.
- **If it needs research, split it.** Create a research bead first, then
  implementation beads based on findings.

## The Research-Then-Implement Pattern

For anything unfamiliar:

1. **Research bead** — investigate the approach, document findings in the
   bead's notes. Output is knowledge, not code.
2. **Implementation bead(s)** — build based on research findings. The
   research bead becomes a dependency.

Example from our project: ADR-003 came from a research bead about SideArm
scraping. We didn't write a single line of scraper code until we understood
the data source.

## Reading the Beads Backlog

```bash
bd list                    # All open beads
bd ready                   # Beads with no blockers (ready to work)
bd list --type=bug         # Just bugs
bd show <id>               # Full details on one bead
```

Beads have priorities (P0-P3) and types (bug, task, feature). P0 = drop
everything, P3 = nice to have.

## Convoy Naming

When we batch related beads into a group, we call it a convoy. Convoys
get a descriptive name like `foundation-docs` or `pipeline-statcrew`.
This is just for human readability — Gas Town doesn't enforce it.

## When to Sling vs. Do From Crew

- **Sling to a polecat** when the work is well-defined, self-contained,
  and doesn't need constant human judgment. Most implementation work.
- **Do from crew** (work it yourself) when the task needs creative
  direction, involves sensitive decisions, or is exploratory research
  that benefits from human intuition.

Rule of thumb: if you can write clear acceptance criteria, sling it.
