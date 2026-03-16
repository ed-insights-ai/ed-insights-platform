# Ed Insights Pipeline

Production data-collection pipeline for the Ed Insights Platform. Scrapes collegiate athletic statistics from StatCrew HTML endpoints and outputs structured data.

## Setup

```bash
cd packages/pipeline
uv sync
```

## Usage

```bash
# Scrape all enabled schools
uv run scrape --all

# Scrape a single school
uv run scrape --school HU

# Full pipeline (scrape → load → export → audit)
uv run pipeline-run --all-enabled

# Load parquets into PostgreSQL (requires Docker)
uv run load-db

# Run tests
uv run pytest
```

## Related

The [`sports-data-pipeline`](https://github.com/ed-insights-ai/sports-data-pipeline) repo is a **frozen tutorial/reference** — it is not actively developed. This package is the production pipeline.
