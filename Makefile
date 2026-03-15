.PHONY: up down logs reset ps migrate

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

reset:
	docker compose down -v && docker compose up -d

ps:
	docker compose ps

migrate:
	@for f in packages/pipeline/migrations/*.sql; do \
		echo "Running $$f ..."; \
		docker compose exec -T db psql -U postgres -d postgres -f "/docker-entrypoint-initdb.d/$$(basename $$f)"; \
	done
	@echo "Migrations complete."
