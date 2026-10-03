.PHONY: install check fmt test run

install:
	uv sync

fmt:
	uv run ruff format .
	uv run ruff check --fix .

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy
	uv run pytest

test:
	uv run pytest

run:
	uv run uvicorn preflight.api.app:create_app --factory --reload
