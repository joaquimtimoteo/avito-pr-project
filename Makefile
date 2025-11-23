# Makefile для управления Docker Compose проектом

# Запускает контейнеры в фоновом режиме и пересобирает образ, если нужно
up:
	docker-compose up --build

# Останавливает и удаляет контейнеры
down:
	docker-compose down

# Останавливает и удаляет контейнеры, включая тома (удаляет данные БД)
destroy:
	docker-compose down -v

# Показывает логи сервиса backend
logs:
	docker-compose logs -f backend

# Перезапускает сервисы
restart:
	docker-compose restart

.PHONY: up down destroy logs restart
