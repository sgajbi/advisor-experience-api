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


def test_proposal_create_success(monkeypatch):
    async def _fake_create_proposal(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 200, {"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.create_proposal",
        _fake_create_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals",
        json={
            "body": {
                "created_by": "advisor_1",
                "simulate_request": {"options": {"enable_proposal_simulation": True}},
            }
        },
        headers={"Idempotency-Key": "idem-create-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["proposal_id"] == "pp_1"


def test_proposal_list_success(monkeypatch):
    async def _fake_list_proposals(self, params, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        assert params["state"] == "DRAFT"
        return 200, {
            "items": [{"proposal_id": "pp_1", "current_state": "DRAFT"}],
            "next_cursor": None,
        }

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.list_proposals",
        _fake_list_proposals,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals?state=DRAFT&limit=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["items"][0]["proposal_id"] == "pp_1"


def test_get_proposal_success(monkeypatch):
    async def _fake_get_proposal(self, proposal_id, include_evidence, correlation_id):  # noqa: ANN001
        _ = self, include_evidence, correlation_id
        assert proposal_id == "pp_1"
        return 200, {"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.get_proposal",
        _fake_get_proposal,
    )

    client = TestClient(app)
    response = client.get("/api/v1/proposals/pp_1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["proposal"]["current_state"] == "DRAFT"


def test_submit_proposal_success(monkeypatch):
    seen = {}

    async def _fake_transition_proposal(self, proposal_id, body, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        seen["proposal_id"] = proposal_id
        seen["body"] = body
        return 200, {"proposal_id": proposal_id, "current_state": "RISK_REVIEW"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.transition_proposal",
        _fake_transition_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/submit",
        json={
            "actor_id": "advisor_1",
            "expected_state": "DRAFT",
            "review_type": "RISK",
            "reason": {"comment": "submit"},
        },
    )

    assert response.status_code == 200
    assert seen["proposal_id"] == "pp_1"
    assert seen["body"]["event_type"] == "SUBMITTED_FOR_RISK_REVIEW"


def test_submit_proposal_forwards_upstream_error(monkeypatch):
    async def _fake_transition_proposal(self, proposal_id, body, correlation_id):  # noqa: ANN001
        _ = self, proposal_id, body, correlation_id
        return 409, {"detail": "STATE_CONFLICT"}

    monkeypatch.setattr(
        "app.clients.dpm_client.DpmClient.transition_proposal",
        _fake_transition_proposal,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/proposals/pp_1/submit",
        json={"actor_id": "advisor_1", "expected_state": "DRAFT"},
    )

    assert response.status_code == 409
