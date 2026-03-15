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

## Canonical Startup

```bash
docker compose up
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
