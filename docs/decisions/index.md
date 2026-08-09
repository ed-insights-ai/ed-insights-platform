# Architecture Decision Records

We record significant architectural decisions as ADRs so future-us (and
new contributors) can understand *why* things are the way they are.

## When to Write an ADR

Write one when you're choosing between real alternatives and the decision
affects how others will build. If you'd explain it in a PR comment anyway,
it probably deserves an ADR.

## Template

```markdown
# ADR-NNN: Title

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNN

## Context

What's the situation? What problem are we solving? What constraints exist?

## Decision

What did we decide? Be specific.

## Consequences

What follows from this decision — both good and bad?
```

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](ADR-001-monorepo-structure.md) | Monorepo structure | Accepted |
| [002](ADR-002-fastapi-over-supabase-direct.md) | FastAPI over Supabase direct | Accepted |
| [003](ADR-003-statcrew-sidearm-scraper-strategy.md) | StatCrew + SideArm scraper strategy | Accepted |
| [004](ADR-004-parquet-files-in-git.md) | Parquet files tracked in git | Superseded by ADR-009 |
| [005](ADR-005-sidearm-scraper-variants.md) | SideArm CMS scraper variant strategy | Accepted |
| [006](ADR-006-opponent-conference-model.md) | Opponent and conference data model | Accepted |
| [007](ADR-007-gac-school-membership.md) | GAC soccer school membership — authoritative list | Accepted |
| [008](ADR-008-touchline-keelson-rib.md) | Touchline — a Keelson rib as the season intelligence layer | Proposed |
| [009](ADR-009-parquets-as-build-output.md) | Parquets as reproducible build output | Accepted |
