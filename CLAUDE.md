# Ed Insights Platform — Monorepo Constitution

## Repository Layout

```
ed-insights-platform/
├── apps/
│   ├── web/          # Next.js frontend (Supabase auth + dashboard)
│   └── api/          # FastAPI backend
├── packages/
│   └── pipeline/     # Python data-collection pipeline
├── .env.example
├── docker-compose.yml
└── README.md
```

## Tech Stack

| Component | Language | Framework |
|-----------|----------|-----------|
| `apps/web` | TypeScript | Next.js, Tailwind, Supabase |
| `apps/api` | Python | FastAPI, SQLAlchemy |
| `packages/pipeline` | Python | BeautifulSoup, pandas |

## Naming Conventions

- **Components/classes**: PascalCase
- **Routes/URLs**: kebab-case
- **Python identifiers**: snake_case
- **TypeScript identifiers**: camelCase (variables/functions), PascalCase (types/components)

## Local Development Environment

**No Docker.** This runs on a macOS VM without Docker Desktop.

### PostgreSQL (Homebrew)
- **Server:** Postgres 15 via `brew services` — always running
- **Host:** `localhost:5432` (default port)
- **User:** `lume` (socket auth, no password)
- **Database:** `ed_insights`
- **psql:** `psql -U lume -d ed_insights`
- **Pipeline URL:** `postgresql://lume@localhost:5432/ed_insights`
- **API URL:** `postgresql+asyncpg://lume@localhost:5432/ed_insights`

### Data
- 18 schools (13 men's + 5 women's GAC soccer programs + NSU disabled)
- 2,852 games, 103,621 player stats, 27,238 events, 5,704 team stats
- Loaded from `packages/pipeline/data/structured/` parquet files
- Reload: `cd packages/pipeline && DATABASE_URL="postgresql://lume@localhost:5432/ed_insights" uv run load-db`

### API (FastAPI)
```bash
cd apps/api && uv run uvicorn src.main:app --port 8000 --reload
```
Endpoints: `/api/schools`, `/api/games`, `/api/stats/team`, `/api/stats/players`

### Web (Next.js)
```bash
cd apps/web && npm run dev
```
Runs on port 3000 (or 3001). Needs `NEXT_PUBLIC_API_URL=http://localhost:8000`.

### Pipeline
```bash
cd packages/pipeline && uv run scrape        # scrape all enabled schools
cd packages/pipeline && uv run load-db       # load parquets → postgres
cd packages/pipeline && uv run pytest -v     # run tests
```

## Documentation

| Document | Purpose |
|----------|---------|
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branching, commits, local dev, Gas Town workflow |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview, components, data flow, design principles |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records (ADRs) |
| [docs/GASTOWN.md](docs/GASTOWN.md) | How we use Gas Town on this project |

## Rules

- Polecats stay in their assigned component directory.
- `sports-data-pipeline` (github.com/ed-insights-ai/sports-data-pipeline) is a **frozen** tutorial/reference repo. Do not modify it. The production pipeline lives in `packages/pipeline/`.
- Cross-component changes require coordination through the rig.
