# Architecture

## System Overview

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  apps/web   │────▶│  apps/api   │────▶│   Postgres   │
│  (Next.js)  │     │  (FastAPI)  │     │   (port 5432)│
└─────────────┘     └─────────────┘     └──────────────┘
                                              ▲
                    ┌─────────────────┐        │
                    │packages/pipeline│────────┘
                    │   (scraper)     │
                    └─────────────────┘

Auth: Supabase (hosted) ──▶ apps/web (client-side)
```

## Components

### `apps/web` — Next.js Frontend

The user-facing dashboard. Built with Next.js, Tailwind CSS, and Supabase
for authentication. Displays school data, team rosters, and athletic stats.

Talks to the API at `NEXT_PUBLIC_API_URL` for all data. Auth is handled
client-side through Supabase's JS SDK.

### `apps/api` — FastAPI Backend

The REST API that serves data to the frontend (and eventually to mobile
clients and AI tools). Built with FastAPI and SQLAlchemy. Connects directly
to Postgres.

Why a separate API instead of calling Supabase directly from the frontend?
See [ADR-002](decisions/ADR-002-fastapi-over-supabase-direct.md).

### `packages/pipeline` — Data Collection Pipeline

Python scraper that collects collegiate athletic data from public sources.
Normalizes the data and loads it into Postgres.

The pipeline runs independently — scrape, transform, load — and the API
reads what it wrote.

#### Scraper Variant Strategy

Not all schools expose data the same way. The pipeline uses a three-tier
strategy keyed by the `scraper` field in `config/schools.toml`:

| Variant | `scraper` value | Discovery method | Boxscore format |
|---|---|---|---|
| StatCrew (Harding) | `statcrew` | HTML regex on schedule page | `.htm` static files |
| SideArm New (Nuxt 3/Vue) | `sidearm` | HTML regex on schedule page | `/stats/{year}/{opp}/boxscore/{id}` |
| SideArm New (API) | `sidearm_api` | `GET /api/v2/Schedule/{id}` JSON | same |
| SideArm Legacy (KnockoutJS) | `sidearm_legacy` | ⚠️ Not yet implemented | `boxscore.aspx?id={id}` |

Legacy SideArm sites redirect `/schedule/{year}` to the homepage — schedule
data loads via client-side XHR. These 14 programs are `enabled = false` until
the legacy scraper is built. See [ADR-005](decisions/ADR-005-sidearm-scraper-variants.md).

**GAC program coverage (28 total):**
- ✅ 14 programs scraped (StatCrew + SideArm New)
- ⏳ 14 programs pending (SideArm Legacy: ATU, ECU, HSU, SOSU, SAU, SWOSU, UAM + women's)

## Data Flow

```
StatCrew HTML           SideArm New (HTML/API)     SideArm Legacy (XHR)
     │                          │                          │ (⚠️ pending)
     └──────────────────────────┴──────────────────────────┘
                                │
                                ▼
              packages/pipeline (scrape + normalize)
                    │                   │
                    ▼                   ▼
              Postgres           data/*.parquet
           (structured)          (local cache)
                    │
                    ▼
            apps/api (FastAPI)
                    │
                    ▼
            apps/web (Next.js)
                    │
                    ▼
             User sees data
```

## Key Design Principles

- **Python for data, TypeScript for UI.** The API and pipeline are Python
  because that's where the data science and ML tooling lives. The frontend
  is TypeScript because that's what Next.js wants.

- **Supabase for auth only.** We use Supabase's hosted auth service, not
  its database or API features. Our data lives in our own Postgres.

- **`docker compose up` is the dev loop.** One command starts everything.
  No "install these 5 things first" — Docker handles it.

- **Monorepo at this scale.** Everything in one repo because we're small,
  share a docker-compose file, and benefit from seeing the full picture.
  See [ADR-001](decisions/ADR-001-monorepo-structure.md).

## What We Decided NOT to Do

- **No separate vector DB service.** When we need embeddings, we'll use
  pgvector in our existing Postgres. Adding a dedicated vector DB is
  premature at our scale.

- **No Streamlit dashboards in production.** Streamlit is great for
  prototyping and proof-of-concept, but the production UI is Next.js.
  Streamlit prototypes stay in research branches.

- **No monorepo tooling (Turborepo, Nx, etc.) yet.** Two apps and one
  package don't need build orchestration. We'll add it when the pain
  justifies it. YAGNI.
