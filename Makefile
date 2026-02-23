.PHONY: install lint typecheck test test-unit test-integration test-e2e-live check ci-local ci-local-docker ci-local-docker-down run clean docker-up docker-down e2e-up e2e-down

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

e2e-up:
	docker compose -f docker-compose.e2e.yml up -d --build

e2e-down:
	docker compose -f docker-compose.e2e.yml down -v --remove-orphans

test-e2e-live:
	python tests/e2e/test_platform_capabilities_live.py

check: lint typecheck test

ci-local: check test-integration

ci-local-docker:
	docker compose -f docker-compose.ci-local.yml up --build --abort-on-container-exit --exit-code-from ci-local ci-local

ci-local-docker-down:
	docker compose -f docker-compose.ci-local.yml down -v --remove-orphans

run:
	uvicorn app.main:app --reload --app-dir src --port 8100

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', '.ruff_cache', '.mypy_cache']]; pathlib.Path('.coverage').unlink(missing_ok=True)"
