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
- 14 school rows (7 men's + 7 women's GAC soccer programs; NSU is `enabled=false` and has
  0 games, so 13 programmes carry data)
- 2,140 games, 77,586 player stats, 22,754 events, 4,280 team stats

(The previous figures — 18 schools / 2,852 games / 103,621 player stats / 27,238 events /
5,704 team stats — predate migration 005 and match the stale merged parquet export
`data/structured/all/games.parquet`, which still carries 712 rows from retired school
ordinals. Verify counts against Postgres, not against `data/*.parquet`.)
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
| [STATUS.md](STATUS.md) | **Read this first after time away** — plain-language state of the effort |
| [ROADMAP.md](ROADMAP.md) | What we are building and what to pick up next — generated from beads |
| [docs/BRIEF.md](docs/BRIEF.md) | The product brief — the thesis, the boards, the nine open forks, and what we chose not to build |
| [docs/specs/touchline-rib.md](docs/specs/touchline-rib.md) | The Touchline build plan, S0 → S9 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Branching, commits, local dev, Gas Town workflow |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System overview, components, data flow, design principles |
| [docs/decisions/](docs/decisions/) | Architecture Decision Records (ADRs) |
| [docs/GASTOWN.md](docs/GASTOWN.md) | How we use Gas Town on this project |

## Where the work lives

Issues are tracked in **beads** (`bd`), not GitHub. Beads is dependency-aware, so
`bd ready` only ever shows work whose prerequisites are actually done — which matters
here because the data repair has a strict order and doing it out of order produces
plausible-looking wrong answers.

```bash
bd ready --exclude-type=epic   # what can be started right now
bd show <id>                   # mechanism, evidence, acceptance criteria
bd update <id> --claim         # take it
python3 scripts/roadmap.py     # regenerate ROADMAP.md after changing issues
```

Beads that mirror a GitHub issue carry `external_ref: gh-N`; both stay in sync until
the GitHub backlog is retired. New work goes in beads only.

Two Keelson workflows validate the data and one drives the queue:

```bash
keelson workflow run data-integrity --project ed-insights-platform  # 9 deterministic checks
keelson workflow run ground-truth   --project ed-insights-platform  # re-parse cached HTML
keelson workflow run bead-work      --project ed-insights-platform  # claim next bead → draft PR
```

## Audit before you trust

Plans and acceptance criteria on this project get an adversarial pass before anyone
executes them — a subagent prompted to *break* the thing, with database access so its
findings carry evidence rather than opinion, and its load-bearing claims re-verified
before acting.

This is not ceremony. An audit of the 64-issue repair plan returned 14 findings, four of
them damaging, after several rounds of ordinary verification had missed all four.

**The failure mode it exists to catch:** *a rule that looks obviously right, where nobody
asked what legitimate data it excludes.* Two real instances so far —

- `extract(year from date) != season_year` as a phantom-row detector condemns **79
  legitimate games**: nine programmes played their COVID season in spring 2021, correctly
  filed under `season_year=2020`. The right predicate is
  `NOT IN (season_year, season_year + 1)`, which returns exactly the 42 real phantoms.
- A canonical match key on `(date, sorted institution pair)` without **gender** collapses
  **40 genuinely distinct fixtures** — a men's and a women's match, same date, same two
  schools — and 39 of the 40 carry different scores.

Acceptance criteria are where this hides, because they read as self-evidently correct.
Audit them specifically. Ask of every predicate: *what valid row does this throw away?*

## Rules

- Polecats stay in their assigned component directory.
- `sports-data-pipeline` (github.com/ed-insights-ai/sports-data-pipeline) is a **frozen** tutorial/reference repo. Do not modify it. The production pipeline lives in `packages/pipeline/`.
- Cross-component changes require coordination through the rig.


<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:6cd5cc61 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:
   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   git push
   git status
   ```
5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**
- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->
