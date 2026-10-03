.PHONY: install install-gpu check fmt test run

install:
	uv sync

# GPU machine only: adds torch, neuralset and the vendored tribev2 (large download).
install-gpu:
	uv sync --extra model

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
	uv run uvicorn tribe_worker.api:create_app --factory --host 0.0.0.0 --port 8001
