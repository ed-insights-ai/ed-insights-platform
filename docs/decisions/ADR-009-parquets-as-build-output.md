# ADR-009: Parquets as Reproducible Build Output

**Date:** 2026-08-09
**Status:** Accepted
**Supersedes:** ADR-004

## Context

ADR-004 chose git-tracked parquet files while the pipeline covered two
programmes and set a revisit trigger at roughly five programmes or 100 MB.
The committed archive now covers 13 programmes. Before this decision, git
tracked 528 parquet files: 524 under `data/structured/` and four top-level
exports.

Those binary files are derived from the committed cached HTML, but every
parser repair rewrites hundreds of them. Repair PRs consequently exceed
GitHub Copilot review's 300-file ceiling even when the reviewable source
change is small. A derived artifact was structurally disabling the
independent review step intended to scrutinize data repairs.

The network scraper is not a bootstrap path. Discovery makes HTTP requests,
and historical box scores may no longer be served. The committed
`data/raw_html/{school}/{year}/game_NN.html` archive is the durable offline
input.

`source_url` also cannot be derived safely from the cache path. It is stored
on every game and served by the API, so replacing it with a blank or
synthetic URL would be a user-visible regression.

## Decision

Parquet files under `packages/pipeline/data/structured/` and the top-level
`packages/pipeline/data/*.parquet` exports are ignored build output, not
version-controlled source.

A fresh clone rebuilds the structured corpus with:

```bash
cd packages/pipeline
uv run reparse
```

`reparse` performs no discovery and makes no network request. It walks the
committed HTML archive, reconstructs each stable `game_id`, routes the page
through the configured StatCrew or SideArm parser, and uses the existing
storage merge functions to replace `data/structured/`.

Exact source URLs live in the small, reviewable
`packages/pipeline/data/source_urls.csv` manifest. Reparse rejects blank,
duplicate, missing, and unused mappings rather than writing a placeholder.
Any future expansion of the committed HTML archive must update this manifest
in the same change.

`make data` exposes the offline rebuild. `make seed` invokes it when the
canonical games parquet is absent. The data-integrity and ground-truth
workflows regenerate before reading parquets, declare that checkout
mutation, and preserve their fail-closed alarm when regeneration or a
parquet reader does not run.

Postgres remains the source used by the application. Cached HTML remains the
archival source from which structured data can be reproduced. Parquets are
an intermediate representation between them.

## Consequences

**Good:**

- Parser repair PRs no longer include hundreds of binary parquet changes.
- Fresh-clone bootstrap is deterministic, offline, and credential-free.
- The API-visible `source_url` value survives a rebuild exactly.
- Missing inputs and parser failures stop the rebuild instead of producing a
  plausible partial corpus.
- Reviewable data provenance is retained in a text manifest.

**Bad:**

- A fresh clone must spend time rebuilding parquets before loading Postgres.
- Git history no longer records binary output snapshots.
- The source URL manifest must be maintained whenever the committed archive
  grows.
- Integrity workflows write ignored build output and therefore require the
  checkout mutation lock even though their database checks remain read-only.

## Repair sequencing

Concurrent bead `tl-9ap` regenerates the same parquet paths and must merge
before the one-time removal PR. The removal branch must then rebase onto
`main`; it must not merge first.

The repair beads that benefit from smaller, reviewable diffs include
`tl-9ap`, `tl-dse`, `tl-ce3`, `tl-09k`, `tl-5vr.3`, and `tl-3rk`.
`tl-3zm` is already closed, so this decision discards none of its repair
work; it removes only the obligation to commit future regenerated outputs.
