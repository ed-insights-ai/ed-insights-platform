# Pipeline — Component Rules

- Use `uv` for dependency management and running scripts.
- All Python code uses `snake_case`.
- Data outputs go to `packages/pipeline/data/`. **Parquets are tracked in git** (ADR-004); raw scraped HTML under `data/raw_html/` is not tracked for newly fetched pages, though pages committed before 2026 remain tracked as an archive.
- Do **not** modify `config/schools.toml` without explicit instruction.
- `sports-data-pipeline` (github.com/ed-insights-ai/sports-data-pipeline) is a **read-only frozen reference**. Do not modify or depend on it at runtime.
