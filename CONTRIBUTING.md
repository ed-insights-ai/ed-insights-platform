# Contributing to Ed Insights Platform

We're a small team building tools for collegiate athletic data. This guide
covers how we work — branching, commits, local dev, and our Gas Town workflow.

## Branching Model

- Feature branches off `main`: `feature/<short-description>`
- One PR per feature — keep them focused
- Rebase onto `main` before opening a PR
- Delete branches after merge

## Commit Convention

Format: `<type>(<scope>): <description>`

**Types:**
- `feat` — new functionality
- `fix` — bug fix
- `docs` — documentation only
- `chore` — build, deps, config
- `refactor` — restructure without behavior change

**Scopes:** `web`, `api`, `pipeline`, `docs`

Examples:
```
feat(api): add school detail endpoint
fix(web): handle missing Supabase env gracefully
docs: add ADR for monorepo decision
chore(pipeline): bump beautifulsoup4 to 4.12
```

## Running Locally

### Full stack (recommended)

```bash
# One-time setup
./scripts/setup.sh

# Start everything in Docker
make up

# Or: start db + api in Docker, web locally with hot reload
make dev

# Verify
./scripts/smoke-test.sh
```

Services:
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- Postgres: localhost:54321

Use `make dev` for frontend work — file changes are reflected instantly without rebuilding containers.

## When to Write an ADR

Write an Architecture Decision Record when you're making a choice that:

- Introduces a new technology or framework
- Establishes an architectural pattern others will follow
- Involves a significant tradeoff (performance vs simplicity, etc.)
- Would surprise someone reading the code six months from now

ADRs live in `docs/decisions/`. Use the template in that directory's index.

## Gas Town Workflow

We use [Gas Town](docs/GASTOWN.md) to coordinate work across the team. The
basic cycle:

1. **Decompose** — Break work into focused beads (issues)
2. **Sling** — Assign a bead to a polecat (worker)
3. **Implement** — Polecat works on a feature branch
4. **Review** — PR goes up, CI runs, human reviews
5. **Merge** — Refinery merges approved work to `main`

### Bead sizing

Learned the hard way: no one-liner beads. If a change is trivial, batch it
with related small fixes into a single bead. A good bead is 1-4 hours of
focused work.

### The research-then-implement pattern

For anything unfamiliar (new data source, new library, unknown API):

1. Create a research bead first — investigate, document findings
2. Then create implementation beads based on what you learned

This prevents wasted effort building the wrong thing.

See [docs/GASTOWN.md](docs/GASTOWN.md) for the full Gas Town guide.
