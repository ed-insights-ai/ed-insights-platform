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

### Web App (Next.js)

```bash
cd apps/web
npm install
npm run dev
```

The web app runs on [http://localhost:3000](http://localhost:3000) with routes for `/`, `/about`, `/login`, `/signup`, and `/dashboard`.

## Related

- [`sports-data-pipeline`](https://github.com/ed-insights-ai/sports-data-pipeline) — frozen tutorial/reference repo (read-only)
