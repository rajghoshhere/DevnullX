.PHONY: install lint format typecheck test migrate migrate-down up down logs

PYTHON ?= python3

install:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

lint:
	.venv/bin/ruff check src tests

format:
	.venv/bin/ruff format src tests
	.venv/bin/ruff check --fix src tests

typecheck:
	.venv/bin/pyright

test:
	.venv/bin/pytest

migrate:
	.venv/bin/alembic upgrade head

migrate-down:
	.venv/bin/alembic downgrade -1

up:
	docker compose --env-file .env up --build

down:
	docker compose --env-file .env down

logs:
	docker compose --env-file .env logs -f api
