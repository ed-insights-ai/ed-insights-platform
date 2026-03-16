# Ed Insights Platform

Monorepo for the Ed Insights AI platform — a suite of tools for collecting,
analyzing, and visualizing collegiate athletic data.

## Components

| Directory | Description | Stack |
|-----------|-------------|-------|
| `apps/web` | Frontend dashboard | Next.js, Supabase |
| `apps/api` | Backend REST API | FastAPI, Python |
| `packages/pipeline` | Data collection pipeline | Python, BeautifulSoup |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Docker Compose v2)
- Node 18+ (for local web development)
- Python 3.12+ (for local API development)
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)

## Quick Start

```bash
# 1. One-time setup (installs deps, creates .env)
make setup

# 2. Start all services
make up

# 3. Load data from parquet files into Postgres
make seed

# 4. Verify everything works
make check

# Open:
#   - Frontend:  http://localhost:3000
#   - API docs:  http://localhost:8000/docs
#   - Postgres:  localhost:54321 (user: postgres, password: postgres)
```

### Make Targets

Run `make help` to see all targets. Key ones:

| Target | Description |
|--------|-------------|
| `make setup` | One-time project setup (deps, env, symlinks) |
| `make up` | Start all services in Docker |
| `make dev` | Start db + api in Docker, web locally with hot reload |
| `make seed` | Load parquet data into Postgres |
| `make down` | Stop all services |
| `make reset` | Tear down (including volumes) and restart |
| `make lint` | Run linters (web + api + pipeline) |
| `make test` | Run tests (api + pipeline) |
| `make check` | Run smoke tests against running services |

### Local Development

For frontend work, use `make dev` — it runs the database and API in Docker while running Next.js locally with hot reload. Changes to files in `apps/web/` are reflected instantly in the browser.

For backend-only work:

```bash
cd apps/api
uv sync
uv run uvicorn src.main:app --reload --port 8000
```

The API runs on [http://localhost:8000](http://localhost:8000) with interactive docs at `/docs`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Port 3000 already in use | `lsof -ti:3000 \| xargs kill` |
| Port 8000 already in use | `lsof -ti:8000 \| xargs kill` |
| `.env` missing | `cp .env.example .env` |
| DB connection refused | `make reset` (recreates volumes) |
| Containers won't start | `docker compose down -v && docker compose up -d --build` |
| Supabase auth not working | Create a free project at [supabase.com](https://supabase.com), copy the URL and anon key from Settings > API, and add them to `.env` |

## Related

- [`sports-data-pipeline`](https://github.com/ed-insights-ai/sports-data-pipeline) — frozen tutorial/reference repo (read-only)
