.PHONY: install dev test lint format

install:
	pip install -e ".[dev]"

dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest

lint:
	ruff check agent api config tests

format:
	ruff format agent api config tests
