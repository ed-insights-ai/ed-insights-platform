.PHONY: help setup up down dev logs ps reset migrate seed test lint check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup: ## One-time project setup (deps, env, symlinks)
	./scripts/setup.sh

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

up: ## Start all services in Docker
	docker compose up -d

down: ## Stop all services
	docker compose down

dev: ## Start db + api in Docker, web locally with hot reload
	docker compose up -d db api
	cd apps/web && npm run dev

logs: ## Tail logs from all services
	docker compose logs -f

ps: ## Show running containers
	docker compose ps

reset: ## Tear down (including volumes) and restart
	docker compose down -v && docker compose up -d

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

migrate: ## Run Alembic migrations inside the API container
	docker compose exec api uv run alembic upgrade head

seed: ## Load parquet data into Postgres
	cd packages/pipeline && uv run load-db

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------

lint: ## Run linters (web + api + pipeline)
	cd apps/web && npx eslint src/
	cd apps/api && uv run ruff check src/
	cd packages/pipeline && uv run ruff check src/ scripts/

test: ## Run tests (api + pipeline)
	cd apps/api && uv run pytest tests/ -v
	cd packages/pipeline && uv run pytest tests/ -v

check: ## Run smoke tests against running services
	./scripts/smoke-test.sh
