.PHONY: install lint typecheck test check run

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy src

test:
	python -m pytest

check: lint typecheck test

run:
	uvicorn app.main:app --reload --app-dir src --port 8100
