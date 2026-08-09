# Pipeline — Component Rules

- Use `uv` for dependency management and running scripts.
- All Python code uses `snake_case`.
- Data outputs go to `packages/pipeline/data/`. Parquets are ignored build output (ADR-009); rebuild them offline with `uv run reparse` from the committed pre-2026 `data/raw_html/` archive and `data/source_urls.csv`. Do not use the networked `uv run scrape` command as a fresh-clone bootstrap. Newly fetched raw HTML remains ignored.
- Do **not** modify `config/schools.toml` without explicit instruction.
- `sports-data-pipeline` (github.com/ed-insights-ai/sports-data-pipeline) is a **read-only frozen reference**. Do not modify or depend on it at runtime.
