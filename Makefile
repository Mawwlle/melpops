.PHONY: install lint fmt test run up down logs psq

# Зависимости из lock-файла
install:
	uv sync

# Линт и проверка форматирования
lint:
	uv run ruff check .
	uv run ruff format --check .

# Линт с автофиксом + форматирование
fmt:
	uv run ruff check . --fix
	uv run ruff format .

# Тесты
test:
	uv run pytest -q

# Запуск приложения локально (без docker)
run:
	uv run uvicorn src.app:app --reload --port 8000

# Поднять стек (app + postgres)
up:
	docker compose up -d --build

# Остановить и убрать контейнеры (объёмы данных не трогаем)
down:
	docker compose down

# Логи приложения
logs:
	docker compose logs -f app

# psql внутрь поднятого postgres
psq:
	docker compose exec postgres psql -U postgres -d melpops
