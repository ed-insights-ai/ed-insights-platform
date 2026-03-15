# ADR-001: Monorepo Structure

**Date:** 2025-01-15
**Status:** Accepted

## Context

We have three components — a Next.js frontend, a FastAPI backend, and a
Python data pipeline. We needed to decide whether to keep them in separate
repos or combine them into a monorepo.

We're a small team (two builders). Our components share a docker-compose
file for local dev and will eventually share types/schemas. Our AI polecats
need full project context to work effectively.

## Decision

Put everything in one monorepo with this layout:

```
apps/web/          # Next.js
apps/api/          # FastAPI
packages/pipeline/ # Scraper
```

## Consequences

**Good:**
- Single `docker compose up` starts everything
- One PR can touch frontend + backend together
- Polecats see the full picture without cross-repo context
- Shared `.env.example` and consistent tooling

**Bad:**
- CI runs for all components on every push (acceptable at our size)
- Need discipline to keep components loosely coupled
- If we grow to 10+ devs, may need build orchestration (Turborepo etc.)

**Accepted tradeoff:** At our scale, the coordination cost of multiple repos
far outweighs the isolation benefits.
