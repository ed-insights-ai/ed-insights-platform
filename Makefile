.PHONY: up down logs reset ps migrate dev

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
	docker compose exec api alembic upgrade head

dev:
	docker compose up -d db api
	cd apps/web && npm run dev
