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
# 1. Run the setup script (installs deps, creates .env)
./scripts/setup.sh

# 2. Start all services
make up

# 3. Wait ~30 seconds, then verify everything works
./scripts/smoke-test.sh

# Open:
#   - Frontend:  http://localhost:3000
#   - API docs:  http://localhost:8000/docs
#   - Postgres:  localhost:54321 (user: postgres, password: postgres)
```

### Make Targets

| Target | Description |
|--------|-------------|
| `make up` | Start all services in the background |
| `make down` | Stop all services |
| `make logs` | Tail logs from all services |
| `make reset` | Tear down (including volumes) and rebuild |
| `make ps` | Show running containers |
| `make migrate` | Run Alembic migrations inside the API container |

### Local Development (without Docker)

#### Web App (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

The web app runs on [http://localhost:3000](http://localhost:3000) with routes for `/`, `/about`, `/login`, `/signup`, and `/dashboard`.

#### API (FastAPI)

```bash
cd apps/api
uv sync
uvicorn src.main:app --reload --port 8000
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
