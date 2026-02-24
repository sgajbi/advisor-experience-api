from fastapi.testclient import TestClient

from app.main import app


def test_workbench_router_success(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "portfolio": {
                "portfolio_id": "PF_1001",
                "base_currency": "USD",
                "booking_center": "SG",
                "cif_id": "CIF_1001",
            },
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 250.0},
                "holdings": {"holdingsByAssetClass": {"Equity": [{"id": "EQ_1"}]}},
            },
        }

    async def _pa(*args, **kwargs):
        return 200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 2.5}}}

    async def _dpm(*args, **kwargs):
        return 200, {
            "items": [
                {
                    "rebalance_run_id": "rr_100",
                    "status": "PENDING_REVIEW",
                    "created_at": "2026-02-23T01:00:00Z",
                }
            ]
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_snapshot_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert body["overview"]["position_count"] == 1
    assert body["performance_snapshot"]["period"] == "YTD"
    assert body["rebalance_snapshot"]["status"] == "PENDING_REVIEW"


def test_workbench_router_partial_failure(monkeypatch):
    async def _pas(*args, **kwargs):
        return 200, {
            "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 100.0},
            },
        }

    async def _pa(*args, **kwargs):
        return 503, {"detail": "paused"}

    async def _dpm(*args, **kwargs):
        return 503, {"detail": "paused"}

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_snapshot_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["performance_snapshot"] is None
    assert body["rebalance_snapshot"] is None
    assert len(body["partial_failures"]) == 2


def test_workbench_portfolio_360_router(monkeypatch):
    async def _pas_core(*args, **kwargs):
        return 200, {
            "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 100.0},
                "holdings": {
                    "holdingsByAssetClass": {
                        "Equity": [
                            {"instrument_id": "EQ_1", "instrument_name": "Equity 1", "quantity": 10}
                        ]
                    }
                },
            },
        }

    async def _pa(*args, **kwargs):
        return 200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.5}}}

    async def _dpm_runs(*args, **kwargs):
        return 200, {"items": []}

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas_core)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_snapshot_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)

    client = TestClient(app)
    response = client.get("/api/v1/workbench/PF_1001/portfolio-360")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolio"]["portfolio_id"] == "PF_1001"
    assert len(body["current_positions"]) == 1


def test_workbench_sandbox_changes_router(monkeypatch):
    async def _pas_core(*args, **kwargs):
        return 200, {
            "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 100.0},
            },
        }

    async def _pas_create(*args, **kwargs):
        return 201, {"session": {"session_id": "sess_1", "version": 1}}

    async def _pas_add(*args, **kwargs):
        return 200, {"session_id": "sess_1", "version": 2}

    async def _pas_positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "baseline_quantity": 10,
                    "proposed_quantity": 12,
                    "delta_quantity": 2,
                }
            ]
        }

    async def _pas_summary(*args, **kwargs):
        return 200, {
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 2.0,
        }

    async def _pa(*args, **kwargs):
        return 200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.5}}}

    async def _dpm_runs(*args, **kwargs):
        return 200, {"items": []}

    async def _dpm_simulate(*args, **kwargs):
        return 200, {"status": "COMPLETED", "gate_decision": {"status": "PASS"}}

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas_core)
    monkeypatch.setattr("app.clients.pas_client.PasClient.create_simulation_session", _pas_create)
    monkeypatch.setattr("app.clients.pas_client.PasClient.add_simulation_changes", _pas_add)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_projected_positions", _pas_positions)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_projected_summary", _pas_summary)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_snapshot_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.simulate_proposal", _dpm_simulate)

    client = TestClient(app)
    created = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions", json={"created_by": "advisor_1"}
    )
    assert created.status_code == 200
    assert created.json()["session_id"] == "sess_1"

    updated = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions/sess_1/changes",
        json={
            "changes": [{"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 2}],
            "evaluate_policy": True,
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["session_id"] == "sess_1"
    assert body["session_version"] == 2
    assert body["policy_feedback"]["status"] == "PASS"
