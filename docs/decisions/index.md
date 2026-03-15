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
