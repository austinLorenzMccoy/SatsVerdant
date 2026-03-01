# SatsVerdant Backend Makefile

.PHONY: help install dev test lint format clean run migrate

help:  ## Show this help message
	@echo "SatsVerdant Backend - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies with Poetry
	poetry install

dev:  ## Install with dev dependencies
	poetry install --with dev

run:  ## Run development server
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Run tests with coverage
	poetry run pytest -v --cov=app --cov-report=term-missing

test-watch:  ## Run tests in watch mode
	poetry run pytest-watch

lint:  ## Run linters (ruff, mypy)
	poetry run ruff check app tests
	poetry run mypy app

format:  ## Format code with black and isort
	poetry run black app tests
	poetry run isort app tests

format-check:  ## Check code formatting
	poetry run black --check app tests
	poetry run isort --check-only app tests

migrate:  ## Run database migrations
	poetry run alembic upgrade head

migrate-create:  ## Create new migration (usage: make migrate-create msg="description")
	poetry run alembic revision --autogenerate -m "$(msg)"

migrate-down:  ## Rollback last migration
	poetry run alembic downgrade -1

db-init:  ## Initialize database
	poetry run python -m app.db.init_db

shell:  ## Open Python shell with app context
	poetry run python

clean:  ## Clean up cache and build files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage

docker-build:  ## Build Docker image
	docker-compose build

docker-up:  ## Start Docker containers
	docker-compose up -d

docker-down:  ## Stop Docker containers
	docker-compose down

docker-logs:  ## View Docker logs
	docker-compose logs -f

lock:  ## Update poetry.lock file
	poetry lock

export:  ## Export to requirements.txt
	poetry export -f requirements.txt --output requirements.txt --without-hashes

.DEFAULT_GOAL := help
