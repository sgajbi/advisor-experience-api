from fastapi.testclient import TestClient

from app.main import app


def test_e2e_platform_capability_aggregation_and_health(monkeypatch) -> None:
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-core",
            "contractVersion": "v1",
            "policyVersion": "pas-default-v1",
            "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
            "workflows": [{"workflow_key": "portfolio_bulk_onboarding", "enabled": True}],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pa(*args, **kwargs):
        return 200, {
            "sourceService": "performance-analytics",
            "contractVersion": "v1",
            "policyVersion": "pa-default-v1",
            "features": [{"key": "pa.analytics.twr", "enabled": True}],
            "workflows": [{"workflow_key": "performance_snapshot", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _dpm(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-advise",
            "contractVersion": "v1",
            "policyVersion": "dpm-default-v1",
            "features": [{"key": "dpm.proposals.lifecycle", "enabled": True}],
            "workflows": [{"workflow_key": "proposal_lifecycle", "enabled": True}],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _ras(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-report",
            "contractVersion": "v1",
            "policyVersion": "ras-default-v1",
            "features": [{"key": "ras.reporting.portfolio_summary", "enabled": True}],
            "workflows": [{"workflow_key": "portfolio_reporting", "enabled": True}],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pas_policy(*args, **kwargs):
        return 200, {
            "policyProvenance": {
                "policyVersion": "pas-default-v1",
                "policySource": "tenant",
                "matchedRuleId": "tenant.default.consumers.lotus-gateway",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW", "HOLDINGS"],
            "warnings": [],
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_effective_policy", _pas_policy)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.reporting_client.ReportingClient.get_capabilities", _ras)

    client = TestClient(app)
    capabilities = client.get("/api/v1/platform/capabilities"
        "?consumerSystem=lotus-gateway&tenantId=default")
    health = client.get("/health")

    assert capabilities.status_code == 200
    assert health.status_code == 200
    body = capabilities.json()["data"]
    assert body["partialFailure"] is False
    assert set(body["sources"].keys()) == {"pas", "pa", "dpm", "ras"}


def test_e2e_workbench_sandbox_flow(monkeypatch) -> None:
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
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_input_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.simulate_proposal", _dpm_simulate)

    client = TestClient(app)
    created = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions", json={"created_by": "advisor_1"}
    )
    updated = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions/sess_1/changes",
        json={
            "changes": [{"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 2}],
            "evaluate_policy": True,
        },
    )

    assert created.status_code == 200
    assert updated.status_code == 200
    assert created.json()["session_id"] == "sess_1"
    assert updated.json()["policy_feedback"]["status"] == "PASS"


def test_e2e_proposal_transition_flow(monkeypatch) -> None:
    async def _create(self, body, idempotency_key, correlation_id):  # noqa: ANN001
        _ = self, body, idempotency_key, correlation_id
        return 200, {"proposal": {"proposal_id": "pp_1", "current_state": "DRAFT"}}

    async def _transition(  # noqa: ANN001
        self, proposal_id, body, idempotency_key, correlation_id
    ):
        _ = self, correlation_id
        assert proposal_id == "pp_1"
        assert idempotency_key == "idem-submit-e2e-1"
        return 200, {
            "proposal_id": "pp_1",
            "current_state": "RISK_REVIEW",
            "event_type": body["event_type"],
        }

    monkeypatch.setattr("app.clients.dpm_client.DpmClient.create_proposal", _create)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.transition_proposal", _transition)

    client = TestClient(app)
    created = client.post(
        "/api/v1/proposals",
        json={
            "body": {
                "created_by": "advisor_1",
                "simulate_request": {"options": {"enable_proposal_simulation": True}},
            }
        },
        headers={"Idempotency-Key": "idem-create-e2e-1"},
    )
    submitted = client.post(
        "/api/v1/proposals/pp_1/submit",
        json={"actor_id": "advisor_1", "expected_state": "DRAFT", "review_type": "RISK"},
        headers={"Idempotency-Key": "idem-submit-e2e-1"},
    )

    assert created.status_code == 200
    assert submitted.status_code == 200
    assert created.json()["data"]["proposal"]["proposal_id"] == "pp_1"
    assert submitted.json()["data"]["current_state"] == "RISK_REVIEW"


def test_e2e_reporting_snapshot_summary_review(monkeypatch) -> None:
    async def _snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        return 200, {
            "generatedAt": "2026-02-24T07:00:00Z",
            "rows": [{"bucket": "TOTAL", "metric": "market_value_base", "value": 1250000.0}],
        }

    async def _summary(self, portfolio_id, payload, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        return 200, {
            "scope": {"portfolio_id": portfolio_id},
            "wealth": {"total_market_value": 123.0},
        }

    async def _review(self, portfolio_id, payload, correlation_id):  # noqa: ANN001
        _ = self, correlation_id
        return 200, {"portfolio_id": portfolio_id, "overview": {"total_market_value": 1000.0}}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot", _snapshot
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_summary", _summary
    )
    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_review", _review
    )

    client = TestClient(app)
    snapshot = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    summary = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/summary",
        json={"as_of_date": "2026-02-24", "sections": ["WEALTH"]},
    )
    review = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/review",
        json={"asOfDate": "2026-02-24", "sections": ["OVERVIEW"]},
    )

    assert snapshot.status_code == 200
    assert summary.status_code == 200
    assert review.status_code == 200
    assert snapshot.json()["portfolioId"] == "DEMO_DPM_EUR_001"
    assert summary.json()["data"]["wealth"]["total_market_value"] == 123.0
    assert review.json()["data"]["overview"]["total_market_value"] == 1000.0


def test_e2e_platform_capabilities_partial_failure_when_one_upstream_fails(
    monkeypatch,
) -> None:
    async def _pas(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-core",
            "contractVersion": "v1",
            "policyVersion": "pas-default-v1",
            "features": [{"key": "pas.integration.core_snapshot", "enabled": True}],
            "workflows": [],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pa(*args, **kwargs):
        return 503, {"detail": "lotus-performance unavailable"}

    async def _dpm(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-advise",
            "contractVersion": "v1",
            "policyVersion": "dpm-default-v1",
            "features": [{"key": "dpm.proposals.lifecycle", "enabled": True}],
            "workflows": [],
            "supportedInputModes": ["pas_ref", "inline_bundle"],
        }

    async def _ras(*args, **kwargs):
        return 200, {
            "sourceService": "lotus-report",
            "contractVersion": "v1",
            "policyVersion": "ras-default-v1",
            "features": [{"key": "ras.reporting.portfolio_summary", "enabled": True}],
            "workflows": [],
            "supportedInputModes": ["pas_ref"],
        }

    async def _pas_policy(*args, **kwargs):
        return 200, {
            "policyProvenance": {
                "policyVersion": "pas-default-v1",
                "policySource": "tenant",
                "matchedRuleId": "tenant.default.consumers.lotus-gateway",
                "strictMode": False,
            },
            "allowedSections": ["OVERVIEW"],
            "warnings": [],
        }

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_capabilities", _pas)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_capabilities", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.get_capabilities", _dpm)
    monkeypatch.setattr("app.clients.reporting_client.ReportingClient.get_capabilities", _ras)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_effective_policy", _pas_policy)

    client = TestClient(app)
    response = client.get("/api/v1/platform/capabilities"
        "?consumerSystem=lotus-gateway&tenantId=default")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["partialFailure"] is True
    assert any(item["service"] == "pa" for item in body["errors"])
    assert body["normalized"]["moduleHealth"]["pa"] == "unavailable"


def test_e2e_reporting_snapshot_maps_upstream_failure_to_gateway_error(monkeypatch) -> None:
    async def _snapshot_failure(self, portfolio_id, as_of_date, correlation_id):  # noqa: ANN001
        _ = self, portfolio_id, as_of_date, correlation_id
        return 503, {"detail": "lotus-report unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _snapshot_failure,
    )
    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")

    assert response.status_code == 502
    assert "Reporting snapshot unavailable" in response.json()["detail"]


def test_e2e_sandbox_policy_feedback_unavailable_when_dpm_simulation_fails(monkeypatch) -> None:
    async def _pas_core(*args, **kwargs):
        return 200, {
            "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
            "snapshot": {
                "as_of_date": "2026-02-23",
                "overview": {"total_market_value": 1000.0, "total_cash": 100.0},
            },
        }

    async def _pas_create(*args, **kwargs):
        return 201, {"session": {"session_id": "sess_2", "version": 1}}

    async def _pas_add(*args, **kwargs):
        return 200, {"session_id": "sess_2", "version": 2}

    async def _pas_positions(*args, **kwargs):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "baseline_quantity": 10,
                    "proposed_quantity": 11,
                    "delta_quantity": 1,
                }
            ]
        }

    async def _pas_summary(*args, **kwargs):
        return 200, {
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 1.0,
        }

    async def _pa(*args, **kwargs):
        return 200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.2}}}

    async def _dpm_runs(*args, **kwargs):
        return 200, {"items": []}

    async def _dpm_simulate_failure(*args, **kwargs):
        return 503, {"detail": "lotus-manage policy service unavailable"}

    monkeypatch.setattr("app.clients.pas_client.PasClient.get_core_snapshot", _pas_core)
    monkeypatch.setattr("app.clients.pas_client.PasClient.create_simulation_session", _pas_create)
    monkeypatch.setattr("app.clients.pas_client.PasClient.add_simulation_changes", _pas_add)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_projected_positions", _pas_positions)
    monkeypatch.setattr("app.clients.pas_client.PasClient.get_projected_summary", _pas_summary)
    monkeypatch.setattr("app.clients.pa_client.PaClient.get_pas_input_twr", _pa)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.list_runs", _dpm_runs)
    monkeypatch.setattr("app.clients.dpm_client.DpmClient.simulate_proposal", _dpm_simulate_failure)

    client = TestClient(app)
    created = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions",
        json={"created_by": "advisor_2"},
    )
    updated = client.post(
        "/api/v1/workbench/PF_1001/sandbox/sessions/sess_2/changes",
        json={
            "changes": [{"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 1}],
            "evaluate_policy": True,
        },
    )

    assert created.status_code == 200
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["policy_feedback"]["status"] == "UNAVAILABLE"
    assert "DPM_POLICY_SIMULATION_UNAVAILABLE" in payload["warnings"]
