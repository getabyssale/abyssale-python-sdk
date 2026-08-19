.PHONY: install generate lint format typecheck test check build

install:
	pip install -e '.[dev]'

# Requires the codegen extra: pip install -e '.[codegen]'
generate:
	python scripts/generate.py

lint:
	ruff check src tests scripts examples
	ruff format --check src tests scripts examples

format:
	ruff check --fix src tests scripts examples
	ruff format src tests scripts examples

typecheck:
	mypy
	mypy examples --ignore-missing-imports

test:
	pytest

# The release gate — the equivalent of the Node SDK's `prepublishOnly`.
check: lint typecheck test

build: check
	python -m build
