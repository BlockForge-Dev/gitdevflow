.PHONY: help install lint format type-check test test-cov docs docs-serve build publish clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	poetry install --with dev,docs
	pre-commit install

lint: ## Run Ruff linter and Black check
	poetry run ruff check src/ tests/
	poetry run black --check src/ tests/

format: ## Run Ruff and Black formatters
	poetry run ruff format src/ tests/
	poetry run black src/ tests/

type-check: ## Run mypy type checker
	poetry run mypy src/

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage report
	poetry run pytest --cov=src/gitdevflow --cov-report=html --cov-report=term

docs: ## Build documentation
	poetry run mkdocs build

docs-serve: ## Serve documentation locally
	poetry run mkdocs serve

build: ## Build distribution packages
	poetry build

publish: ## Publish to PyPI
	poetry publish

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/ site/
	find . -type d -name __pycache__ -exec rm -rf {} +
