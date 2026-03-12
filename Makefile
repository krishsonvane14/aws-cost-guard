.PHONY: help install clean all

.DEFAULT_GOAL := help

help: ## Show all available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project with dev dependencies
	pip install -e ".[dev]"

lock: ## Regenerate requirements.txt and requirements.lock
	pip-compile pyproject.toml --output-file requirements.txt
	pip-compile pyproject.toml --extra dev --output-file requirements.lock

lint: ## Run ruff linter on src/ and tests/
	ruff check src/ tests/

format: ## Run ruff formatter on src/ and tests/
	ruff format src/ tests/

typecheck: ## Run mypy type checker on src/
	mypy src/

test: ## Run pytest test suite
	pytest

test-cov: ## Run tests with HTML coverage report
	pytest --cov=src --cov-report=html
	@echo "Open htmlcov/index.html"

docker-build: ## Build Docker image locally
	docker build -t aws-cost-guard:local .

docker-run: ## Run Docker image with env vars from shell
	docker run --rm -e DISCORD_WEBHOOK_URL -e AWS_DEFAULT_REGION aws-cost-guard:local

clean: ## Remove build/cache artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov *.egg-info .coverage

all: lint typecheck test ## Run lint, typecheck, and tests
