.PHONY: install lint typecheck test test-unit test-integration check ci-local run clean

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy src

test:
	$(MAKE) test-unit

test-unit:
	python -m pytest tests/unit tests/contract

test-integration:
	python -m pytest tests/integration

check: lint typecheck test

ci-local: check test-integration

run:
	uvicorn app.main:app --reload --app-dir src --port 8100

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', '.ruff_cache', '.mypy_cache']]; pathlib.Path('.coverage').unlink(missing_ok=True)"
