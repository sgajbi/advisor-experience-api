.PHONY: install lint typecheck monetary-float-guard openapi-gate migration-smoke migration-apply test test-unit test-integration test-coverage test-e2e test-e2e-live security-audit check ci ci-local ci-local-docker ci-local-docker-down run clean docker-up docker-down e2e-up e2e-down

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .
	ruff format --check .
	$(MAKE) monetary-float-guard

monetary-float-guard:
	python scripts/check_monetary_float_usage.py

typecheck:
	mypy src

openapi-gate:
	python -m pytest tests/contract/test_workbench_contract.py -q

migration-smoke:
	python scripts/migration_contract_check.py --mode no-schema

migration-apply:
	python scripts/migration_contract_check.py --mode no-schema

security-audit:
	python -m pip_audit -r requirements-audit.txt

test:
	$(MAKE) test-unit

test-unit:
	python -m pytest tests/unit tests/contract

test-integration:
	python -m pytest tests/integration

test-coverage:
	python -m pytest tests/unit tests/contract tests/integration --cov=src/app --cov-branch --cov-report=term-missing --cov-fail-under=99

test-e2e:
	python -m pytest tests/e2e -q

e2e-up:
	docker compose -f docker-compose.e2e.yml up -d --build

e2e-down:
	docker compose -f docker-compose.e2e.yml down -v --remove-orphans

test-e2e-live:
	python -m pytest tests/e2e/test_platform_capabilities_live.py -q

check: lint typecheck openapi-gate test

ci: lint typecheck openapi-gate migration-smoke test-integration test-coverage security-audit

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
