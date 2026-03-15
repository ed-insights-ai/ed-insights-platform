# ADR-004: Parquet Files Tracked in Git

**Date:** 2026-03-15
**Status:** Accepted

## Context

The pipeline scrapes game data from school websites and writes structured
output as Parquet files under `packages/pipeline/data/structured/`. We
needed to decide where those files live.

Options considered:

1. **Git (this repo)** — commit them alongside the code
2. **Cloud storage (S3/GCS/R2)** — store externally, download in CI
3. **DVC** — data version control layer on top of remote storage
4. **Git LFS** — large file storage extension to git

We currently have ~90 files covering HU and HUW (2016–2025). Each school
adds ~40–50 files. At this scale, the largest parquets are a few hundred KB.

## Decision

Track Parquet files in git. The `.gitignore` at the repo root excludes
`data/` and `*.parquet` broadly, but `packages/pipeline/data/` is
explicitly opted in via a negation rule so the structured output is committed.

## Consequences

**Good:**
- Zero infra to set up — no S3 buckets, no DVC config, no credentials
- `git clone` gives you working data immediately; `docker compose up` just works
- Parquet diffs are visible in git history; data changes are tied to code changes
- Polecats and CI have the data available without extra setup steps
- Works well at current scale (2 schools, ~90 files, total < 10 MB)

**Bad:**
- Repo size grows with each new school (~40–50 files per school)
- CI checks out data files it doesn't need for lint/test jobs
- Not appropriate for large datasets (10+ schools, multi-year video, etc.)
- Re-scraping produces binary diffs that aren't human-readable

**Accepted tradeoff:** At our current scale (2 schools, MVP phase), the
simplicity of git-tracked data far outweighs the overhead of external
storage. We revisit this decision when we add more than ~5 schools or the
data directory exceeds ~100 MB.

## Revisit Trigger

Open a new ADR (superseding this one) if any of these occur:
- Adding a 4th+ school pushes total data beyond 100 MB
- CI checkout time becomes noticeable (> 30s)
- We need to share data with a team member who shouldn't have repo write access
