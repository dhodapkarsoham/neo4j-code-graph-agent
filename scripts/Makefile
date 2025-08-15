.PHONY: help install install-dev test test-cov lint format clean docker-build docker-run docker-stop setup-pre-commit run-dev

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install -e ".[dev]"

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run all linting checks
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/
	bandit -r src/
	safety check

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/



setup-pre-commit: ## Install pre-commit hooks
	pre-commit install

run-dev: ## Run development server
	python start.py

run-prod: ## Run production server
	uvicorn src.web_ui:app --host 0.0.0.0 --port 8000 --workers 4

check-all: ## Run all checks (test, lint, security)
	make test
	make lint
	make security-check

security-check: ## Run security checks
	bandit -r src/ -f json -o bandit-report.json
	safety check --json --output safety-report.json

update-deps: ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt

ci-local: ## Run CI checks locally
	make format
	make lint
	make test-cov
	make security-check
