from fastapi.testclient import TestClient

from app.main import app


def test_proposal_simulate_success(monkeypatch):
    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 200, {"status": "READY", "proposal_run_id": "pr_1"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.simulate_proposal",
        _fake_simulate_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/simulate",
        json={
            "body": {
                "portfolio_snapshot": {"portfolio_id": "pf_1", "base_currency": "USD"},
                "market_data_snapshot": {"prices": [], "fx_rates": []},
                "shelf_entries": [],
                "proposed_cash_flows": [],
                "proposed_trades": [],
                "options": {"enable_proposal_simulation": True},
            }
        },
        headers={"Idempotency-Key": "idem-1", "X-Correlation-Id": "corr-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["correlation_id"] == "corr-1"
    assert payload["data"]["status"] == "READY"


def test_proposal_simulate_forwards_upstream_error(monkeypatch):
    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 409, {"detail": "conflict"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.simulate_proposal",
        _fake_simulate_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/simulate",
        json={"body": {"options": {"enable_proposal_simulation": True}}},
        headers={"Idempotency-Key": "idem-1"},
    )

    assert response.status_code == 409


def test_proposal_simulate_generates_idempotency_when_missing(monkeypatch):
    seen = {}

    async def _fake_simulate_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, correlation_id
        seen["idempotency_key"] = idempotency_key
        return 200, {"status": "READY"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.simulate_proposal",
        _fake_simulate_proposal,
    )

    client = TestClient(app)
    response = client.post("/api/v1/proposals/simulate", json={"body": {}})
    assert response.status_code == 200
    assert str(seen.get("idempotency_key", "")).startswith("bff-")
