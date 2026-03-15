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
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Getting Started

```bash
# 1. Copy the environment template and fill in your values
cp .env.example .env

# 2. Start all services
make up

# 3. Wait ~30 seconds for containers to initialize, then open:
#    - Frontend:  http://localhost:3000
#    - API docs:  http://localhost:8000/docs
#    - Postgres:  localhost:54321 (user: postgres, password: postgres)
```

### Make Targets

| Target | Description |
|--------|-------------|
| `make up` | Start all services in the background |
| `make down` | Stop all services |
| `make logs` | Tail logs from all services |
| `make reset` | Tear down (including volumes) and rebuild |
| `make ps` | Show running containers |

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

## Related

- [`sports-data-pipeline`](https://github.com/ed-insights-ai/sports-data-pipeline) — frozen tutorial/reference repo (read-only)
