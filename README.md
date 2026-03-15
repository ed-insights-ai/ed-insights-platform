# Ed Insights Platform

Monorepo for the Ed Insights AI platform — a suite of tools for collecting,
analyzing, and visualizing collegiate athletic data.

## Components

| Directory | Description | Stack |
|-----------|-------------|-------|
| `apps/web` | Frontend dashboard | Next.js, Supabase |
| `apps/api` | Backend REST API | FastAPI, Python |
| `packages/pipeline` | Data collection pipeline | Python, BeautifulSoup |

## Getting Started

```bash
# Copy environment template
cp .env.example .env
# Fill in values, then:
docker compose up
```

## Related

- [`sports-data-pipeline`](https://github.com/ed-insights-ai/sports-data-pipeline) — frozen tutorial/reference repo (read-only)
