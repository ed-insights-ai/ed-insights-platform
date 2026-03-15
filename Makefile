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
	docker compose exec api alembic upgrade head
