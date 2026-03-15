# ADR-002: FastAPI Over Supabase Direct

**Date:** 2025-01-15
**Status:** Accepted

## Context

Supabase provides a client SDK that lets frontend apps query the database
directly (with RLS for auth). This is fast to build with but creates a
tight coupling between the frontend and the database schema.

We know we'll need:
- Python for ML inference and DuckDB analytics
- An API that serves mobile apps and AI agents, not just the web UI
- Custom business logic that doesn't fit in Postgres functions

## Decision

Use FastAPI as the API layer. The frontend calls FastAPI, not Supabase
directly. Supabase is used only for authentication (hosted auth service).

```
Web → FastAPI → Postgres     (data)
Web → Supabase               (auth only)
```

## Consequences

**Good:**
- API is reusable: web, mobile, AI agents all use the same endpoints
- Python ecosystem for data science (pandas, scikit-learn, DuckDB)
- Database schema changes don't break the frontend — the API absorbs them
- Can add caching, rate limiting, and custom auth at the API layer

**Bad:**
- More code to write than using Supabase's auto-generated API
- Extra network hop (web → API → DB instead of web → DB)
- Need to maintain API docs and versioning as it grows

**Accepted tradeoff:** The upfront cost of building an API layer pays off
as soon as we have a second client (mobile app, CLI tool, or AI agent).
