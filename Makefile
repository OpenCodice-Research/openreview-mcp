.PHONY: install test lint fmt serve clean publish

install:
	uv sync --all-extras

test:
	uv run pytest -v

lint:
	uv run ruff check src tests
	uv run mypy src

fmt:
	uv run ruff format src tests
	uv run ruff check --fix src tests

serve:
	uv run openreview-mcp --http --port 8000

serve-stdio:
	uv run openreview-mcp

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +

publish:
	uv build
	uv publish
