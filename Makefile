.PHONY: help install install-dev build publish test lint format clean version bump-version

# Variables
PYTHON_SDK_DIR = python-sdk
PYPROJECT = $(PYTHON_SDK_DIR)/pyproject.toml
VERSION = $(shell grep "^version" $(PYPROJECT) | sed 's/version = "\(.*\)"/\1/')

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "Installing dependencies..."
	cd $(PYTHON_SDK_DIR) && poetry install --no-dev

install-dev: ## Install dependencies including dev dependencies
	@echo "Installing dependencies including dev dependencies..."
	cd $(PYTHON_SDK_DIR) && poetry install

build: ## Build the package
	@echo "Building package..."
	cd $(PYTHON_SDK_DIR) && poetry build

publish: ## Publish package to PyPI
	@echo "Publishing package to PyPI..."
	cd $(PYTHON_SDK_DIR) && poetry publish

publish-test: ## Publish package to TestPyPI
	@echo "Publishing package to TestPyPI..."
	cd $(PYTHON_SDK_DIR) && poetry publish --repository testpypi

test: ## Run tests
	@echo "Running tests..."
	cd $(PYTHON_SDK_DIR) && poetry run pytest

test-cov: ## Run tests with coverage
	@echo "Running tests with coverage..."
	cd $(PYTHON_SDK_DIR) && poetry run pytest --cov=agentbox --cov-report=html --cov-report=term

lint: ## Run linting checks
	@echo "Running linting checks..."
	cd $(PYTHON_SDK_DIR) && poetry run ruff check .

lint-fix: ## Run linting checks and fix issues
	@echo "Running linting checks and fixing issues..."
	cd $(PYTHON_SDK_DIR) && poetry run ruff check --fix .

format: ## Format code with black
	@echo "Formatting code..."
	cd $(PYTHON_SDK_DIR) && poetry run black .

format-check: ## Check code formatting without making changes
	@echo "Checking code formatting..."
	cd $(PYTHON_SDK_DIR) && poetry run black --check .

check: format-check lint ## Run all checks (format and lint)

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	cd $(PYTHON_SDK_DIR) && rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache htmlcov .coverage
	find $(PYTHON_SDK_DIR) -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find $(PYTHON_SDK_DIR) -type f -name "*.pyc" -delete

version: ## Show current version
	@echo "Current version: $(VERSION)"

bump-patch: ## Bump patch version (1.0.4 -> 1.0.5)
	@echo "Bumping patch version..."
	cd $(PYTHON_SDK_DIR) && poetry version patch

bump-minor: ## Bump minor version (1.0.4 -> 1.1.0)
	@echo "Bumping minor version..."
	cd $(PYTHON_SDK_DIR) && poetry version minor

bump-major: ## Bump major version (1.0.4 -> 2.0.0)
	@echo "Bumping major version..."
	cd $(PYTHON_SDK_DIR) && poetry version major

bump-version: ## Bump version (interactive)
	@echo "Bumping version..."
	cd $(PYTHON_SDK_DIR) && poetry version

update: ## Update dependencies
	@echo "Updating dependencies..."
	cd $(PYTHON_SDK_DIR) && poetry update

lock: ## Lock dependencies
	@echo "Locking dependencies..."
	cd $(PYTHON_SDK_DIR) && poetry lock

shell: ## Open poetry shell
	@echo "Opening poetry shell..."
	cd $(PYTHON_SDK_DIR) && poetry shell

deploy: clean build publish ## Full deployment: clean, build, and publish

deploy-test: clean build publish-test ## Test deployment: clean, build, and publish to TestPyPI

ci: install-dev check test ## CI pipeline: install, check, and test

