down:
	docker compose -f docker-compose.yml --env-file=.env down

prune:
	docker system prune -f

up:
	docker compose -f docker-compose.yml --env-file=.env up -d --build

restart:
	docker compose -f docker-compose.yml --env-file=.env down && docker compose -f docker-compose.yml --env-file=.env up -d --build