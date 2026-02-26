from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.services.workbench_service import WorkbenchService


class _StubPasClient:
    def __init__(self):
        self.core_status = 200
        self.core_payload: dict = {
            "portfolio": {"portfolio_id": "P1", "base_currency": "USD"},
            "snapshot": {"as_of_date": "2026-02-24", "overview": {}, "holdings": {}},
        }
        self.positions_status = 200
        self.positions_payload: dict = {"positions": []}
        self.summary_status = 200
        self.summary_payload: dict = {
            "total_baseline_positions": 0,
            "total_proposed_positions": 0,
            "net_delta_quantity": 0.0,
        }
        self.create_status = 201
        self.create_payload: dict = {"session": {"session_id": "sess-1", "version": 1}}
        self.change_status = 200
        self.change_payload: dict = {"version": 2}

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        include_sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return self.core_status, self.core_payload

    async def get_projected_positions(self, session_id: str, correlation_id: str):
        return self.positions_status, self.positions_payload

    async def get_projected_summary(self, session_id: str, correlation_id: str):
        return self.summary_status, self.summary_payload

    async def create_simulation_session(
        self, portfolio_id: str, created_by: str | None, ttl_hours: int, correlation_id: str
    ):
        return self.create_status, self.create_payload

    async def add_simulation_changes(
        self, session_id: str, changes: list[dict], correlation_id: str
    ):
        return self.change_status, self.change_payload


class _StubPaClient:
    def __init__(self):
        self.snapshot_status = 200
        self.snapshot_payload: dict = {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.2}}}
        self.analytics_status = 200
        self.analytics_payload: dict = {
            "allocationBuckets": [],
            "topChanges": [],
            "riskProxy": {},
            "portfolioReturnPct": 1.0,
            "benchmarkReturnPct": 0.8,
            "activeReturnPct": 0.2,
        }

    async def get_pas_input_twr(
        self,
        portfolio_id: str,
        as_of_date: str,
        periods: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return self.snapshot_status, self.snapshot_payload

    async def get_workbench_analytics(self, payload: dict, correlation_id: str):
        return self.analytics_status, self.analytics_payload

    async def get_workbench_risk_proxy(self, payload: dict, correlation_id: str):
        return 200, {"riskProxy": {"hhiCurrent": 1234.0, "hhiProposed": 1500.0, "hhiDelta": 266.0}}


class _StubDpmClient:
    def __init__(self):
        self.list_runs_status = 200
        self.list_runs_payload: dict = {"items": []}
        self.simulate_status = 200
        self.simulate_payload: dict = {"status": "AVAILABLE"}

    async def list_runs(self, params: dict, correlation_id: str):
        return self.list_runs_status, self.list_runs_payload

    async def simulate_proposal(self, body: dict, idempotency_key: str, correlation_id: str):
        return self.simulate_status, self.simulate_payload


def _build_service() -> tuple[WorkbenchService, _StubPasClient, _StubPaClient, _StubDpmClient]:
    pas = _StubPasClient()
    pa = _StubPaClient()
    dpm = _StubDpmClient()
    return WorkbenchService(pas_client=pas, pa_client=pa, dpm_client=dpm), pas, pa, dpm


def _build_service_with_risk_client() -> tuple[
    WorkbenchService, _StubPasClient, _StubPaClient, _StubDpmClient, _StubPaClient
]:
    pas = _StubPasClient()
    pa = _StubPaClient()
    dpm = _StubDpmClient()
    risk = _StubPaClient()
    return (
        WorkbenchService(pas_client=pas, pa_client=pa, dpm_client=dpm, risk_client=risk),
        pas,
        pa,
        dpm,
        risk,
    )


def test_raise_for_pas_error_includes_upstream_detail():
    service, _, _, _ = _build_service()
    with pytest.raises(HTTPException) as exc:
        service._raise_for_pas_error(500, {"detail": "downstream unavailable"})
    assert exc.value.status_code == 502
    assert "downstream unavailable" in str(exc.value.detail)


def test_parse_pas_core_snapshot_invalid_structure_raises():
    service, _, _, _ = _build_service()
    with pytest.raises(HTTPException) as exc:
        service._parse_pas_core_snapshot("P1", {"portfolio": [], "snapshot": {}}, "2026-02-24")
    assert exc.value.status_code == 502


def test_parse_pas_core_snapshot_uses_fallback_defaults():
    service, _, _, _ = _build_service()
    portfolio, overview, as_of_date = service._parse_pas_core_snapshot(
        fallback_portfolio_id="P1",
        payload={"portfolio": {}, "snapshot": {"overview": {"total_market_value": 0.0}}},
        fallback_as_of_date="2026-02-24",
    )
    assert portfolio.portfolio_id == "P1"
    assert portfolio.base_currency == "USD"
    assert overview.cash_weight_pct == 0.0
    assert as_of_date == "2026-02-24"


@pytest.mark.parametrize(
    ("result", "warning"),
    [
        (RuntimeError("boom"), "PA_SNAPSHOT_UNAVAILABLE"),
        (("bad",), "PA_SNAPSHOT_UNAVAILABLE"),
    ],
)
def test_parse_pa_snapshot_handles_exception_and_invalid_result_shape(result, warning):
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_pa_snapshot(result, partial_failures, warnings)
    assert parsed is None
    assert warning in warnings
    assert len(partial_failures) == 1


def test_parse_pa_snapshot_handles_invalid_payload_types():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_pa_snapshot((200, "bad-payload"), partial_failures, warnings)
    assert parsed is None
    assert "PA_SNAPSHOT_UNAVAILABLE" in warnings


def test_parse_pa_snapshot_handles_http_error_payload():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_pa_snapshot((503, {"detail": "pa down"}), partial_failures, warnings)
    assert parsed is None
    assert partial_failures[0].error_code == "HTTP_503"


def test_parse_pa_snapshot_handles_non_dict_period_map():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_pa_snapshot((200, {"resultsByPeriod": []}), partial_failures, warnings)
    assert parsed is None
    assert "PA_SNAPSHOT_INVALID" in warnings


def test_parse_pa_snapshot_falls_back_to_first_period_key():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_pa_snapshot(
        (200, {"resultsByPeriod": {"QTD": {"net_cumulative_return": 2.2}}}),
        partial_failures,
        warnings,
    )
    assert parsed is not None
    assert parsed.period == "QTD"
    assert parsed.return_pct == 2.2


@pytest.mark.parametrize(
    ("result", "warning"),
    [
        (RuntimeError("boom"), "DPM_REBALANCE_UNAVAILABLE"),
        (("bad",), "DPM_REBALANCE_UNAVAILABLE"),
    ],
)
def test_parse_dpm_snapshot_handles_exception_and_invalid_result_shape(result, warning):
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_dpm_snapshot(result, partial_failures, warnings)
    assert parsed is None
    assert warning in warnings
    assert len(partial_failures) == 1


def test_parse_dpm_snapshot_handles_invalid_payload_type():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_dpm_snapshot((200, "bad-payload"), partial_failures, warnings)
    assert parsed is None
    assert partial_failures[0].error_code == "INVALID_UPSTREAM_PAYLOAD"


def test_parse_dpm_snapshot_handles_http_error():
    service, _, _, _ = _build_service()
    partial_failures = []
    warnings = []
    parsed = service._parse_dpm_snapshot((500, {"detail": "dpm down"}), partial_failures, warnings)
    assert parsed is None
    assert partial_failures[0].error_code == "HTTP_500"


def test_parse_dpm_snapshot_with_no_items_returns_not_available():
    service, _, _, _ = _build_service()
    parsed = service._parse_dpm_snapshot((200, {"items": []}), [], [])
    assert parsed is not None
    assert parsed.status == "NOT_AVAILABLE"


def test_parse_dpm_snapshot_with_datetime_created_at_converts_to_utc():
    service, _, _, _ = _build_service()
    created = datetime(2026, 2, 24, 10, 15, tzinfo=UTC)
    parsed = service._parse_dpm_snapshot(
        (200, {"items": [{"status": "READY", "created_at": created, "rebalance_run_id": "rr-1"}]}),
        [],
        [],
    )
    assert parsed is not None
    assert parsed.last_rebalance_run_id == "rr-1"
    assert parsed.last_run_at_utc is not None
    assert parsed.last_run_at_utc.endswith("+00:00")


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"valuation": {"market_value_base": 100}}, 100.0),
        ({"valuation": {"market_value": 101}}, 101.0),
        ({"current_value_base": 102}, 102.0),
        ({"value_base": 103}, 103.0),
        ({"valuation": {"market_value_base": "bad"}}, None),
    ],
)
def test_parse_position_market_value_variants(payload, expected):
    service, _, _, _ = _build_service()
    assert service._parse_position_market_value(payload) == expected


def test_extract_current_positions_handles_non_dict_holdings():
    service, _, _, _ = _build_service()
    assert service._extract_current_positions({"holdings": []}) == []


def test_extract_current_positions_computes_weight_and_sorts():
    service, _, _, _ = _build_service()
    payload = {
        "overview": {"total_market_value": 1000.0},
        "holdings": {
            "holdingsByAssetClass": {
                "Equity": [
                    {
                        "instrument_id": "B",
                        "instrument_name": "B Name",
                        "quantity": 2,
                        "valuation": {"market_value": 200.0},
                    },
                    {
                        "instrument_id": "A",
                        "instrument_name": "A Name",
                        "quantity": 1,
                        "valuation": {"market_value": 100.0},
                    },
                ]
            }
        },
    }
    rows = service._extract_current_positions(payload)
    assert [row.security_id for row in rows] == ["A", "B"]
    assert rows[0].weight_pct == pytest.approx(10.0)
    assert rows[1].weight_pct == pytest.approx(20.0)


@pytest.mark.asyncio
async def test_load_projected_state_raises_when_positions_unavailable():
    service, pas, _, _ = _build_service()
    pas.positions_status = 503
    with pytest.raises(HTTPException) as exc:
        await service._load_projected_state("sess-1", "corr-1")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_load_projected_state_raises_when_summary_unavailable():
    service, pas, _, _ = _build_service()
    pas.summary_status = 503
    with pytest.raises(HTTPException) as exc:
        await service._load_projected_state("sess-1", "corr-1")
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_load_projected_state_skips_non_dict_rows():
    service, pas, _, _ = _build_service()
    pas.positions_payload = {"positions": ["bad", {"security_id": "EQ_1", "proposed_quantity": 1}]}
    pas.summary_payload = {
        "total_baseline_positions": 1,
        "total_proposed_positions": 1,
        "net_delta_quantity": 1.0,
    }
    rows, summary = await service._load_projected_state("sess-1", "corr-1")
    assert len(rows) == 1
    assert rows[0].security_id == "EQ_1"
    assert summary.net_delta_quantity == 1.0


@pytest.mark.asyncio
async def test_create_sandbox_session_raises_on_pas_error():
    service, pas, _, _ = _build_service()
    pas.create_status = 500
    with pytest.raises(HTTPException) as exc:
        await service.create_sandbox_session("P1", "corr-1", created_by=None, ttl_hours=1)
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_apply_sandbox_changes_raises_on_pas_error():
    service, pas, _, _ = _build_service()
    pas.change_status = 500
    with pytest.raises(HTTPException) as exc:
        await service.apply_sandbox_changes(
            portfolio_id="P1",
            session_id="sess-1",
            correlation_id="corr-1",
            changes=[{"security_id": "EQ_1"}],
            evaluate_policy=False,
        )
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_apply_sandbox_changes_without_policy_evaluation():
    service, _, _, _ = _build_service()
    response = await service.apply_sandbox_changes(
        portfolio_id="P1",
        session_id="sess-1",
        correlation_id="corr-1",
        changes=[{"security_id": "EQ_1"}],
        evaluate_policy=False,
    )
    assert response.policy_feedback is None
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_get_workbench_analytics_raises_on_pa_error():
    service, _, pa, _ = _build_service()
    pa.analytics_status = 503
    with pytest.raises(HTTPException) as exc:
        await service.get_workbench_analytics(
            portfolio_id="P1",
            correlation_id="corr-1",
            period="YTD",
            group_by="ASSET_CLASS",
            benchmark_code="MODEL",
            session_id=None,
        )
    assert exc.value.status_code == 502


@pytest.mark.asyncio
async def test_get_workbench_analytics_raises_on_invalid_payload_shape():
    service, _, pa, _ = _build_service()
    pa.analytics_payload = {
        "allocationBuckets": [{"bucketKey": "EQ", "currentQuantity": "bad-number"}],
        "topChanges": [],
        "riskProxy": {},
    }
    with pytest.raises(HTTPException) as exc:
        await service.get_workbench_analytics(
            portfolio_id="P1",
            correlation_id="corr-1",
            period="YTD",
            group_by="ASSET_CLASS",
            benchmark_code="MODEL",
            session_id=None,
        )
    assert exc.value.status_code == 502
    assert "Invalid lotus-performance workbench analytics payload" in str(exc.value.detail)


@pytest.mark.asyncio
async def test_get_workbench_analytics_handles_non_dict_risk_proxy():
    service, _, pa, _ = _build_service()
    pa.analytics_payload = {
        "allocationBuckets": [],
        "topChanges": [],
        "riskProxy": "bad-shape",
        "portfolioReturnPct": 1.0,
        "benchmarkReturnPct": 0.8,
        "activeReturnPct": 0.2,
    }
    response = await service.get_workbench_analytics(
        portfolio_id="P1",
        correlation_id="corr-1",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL",
        session_id=None,
    )
    assert response.risk_proxy.hhi_current == 0.0


@pytest.mark.asyncio
async def test_evaluate_policy_feedback_handles_dpm_failure():
    service, _, _, dpm = _build_service()
    dpm.simulate_status = 503
    dpm.simulate_payload = {"detail": "policy engine down"}
    warnings: list[str] = []
    partial_failures = []
    feedback = await service._evaluate_policy_feedback(
        portfolio_id="P1",
        session_id="sess-1",
        session_version=2,
        projected_positions=[],
        correlation_id="corr-1",
        warnings=warnings,
        partial_failures=partial_failures,
    )
    assert feedback.status == "UNAVAILABLE"
    assert warnings == ["DPM_POLICY_SIMULATION_UNAVAILABLE"]
    assert partial_failures[0].source_service == "lotus-manage"


@pytest.mark.asyncio
async def test_evaluate_policy_feedback_uses_status_when_gate_decision_missing():
    service, _, _, dpm = _build_service()
    dpm.simulate_payload = {"status": "PASS"}
    feedback = await service._evaluate_policy_feedback(
        portfolio_id="P1",
        session_id="sess-1",
        session_version=3,
        projected_positions=[],
        correlation_id="corr-1",
        warnings=[],
        partial_failures=[],
    )
    assert feedback.status == "PASS"


def test_extract_current_positions_returns_empty_when_by_asset_class_not_dict():
    service, _, _, _ = _build_service()
    payload = {"overview": {}, "holdings": {"holdingsByAssetClass": []}}
    assert service._extract_current_positions(payload) == []


def test_extract_current_positions_skips_invalid_item_shapes():
    service, _, _, _ = _build_service()
    payload = {
        "overview": {"total_market_value": 100.0},
        "holdings": {"holdingsByAssetClass": {"Equity": ["bad", {"instrument_id": "EQ_1"}]}},
    }
    rows = service._extract_current_positions(payload)
    assert len(rows) == 1
    assert rows[0].security_id == "EQ_1"


def test_extract_current_positions_skips_asset_class_with_non_list_items():
    service, _, _, _ = _build_service()
    payload = {
        "overview": {"total_market_value": 100.0},
        "holdings": {"holdingsByAssetClass": {"Equity": {"instrument_id": "EQ_1"}}},
    }
    rows = service._extract_current_positions(payload)
    assert rows == []


def test_parse_position_market_value_skips_non_numeric_in_flat_keys():
    service, _, _, _ = _build_service()
    assert (
        service._parse_position_market_value({"market_value_base": "bad", "value_base": "bad"})
        is None
    )


def test_parse_pas_core_snapshot_handles_non_dict_overview_and_holdings_shapes():
    service, _, _, _ = _build_service()
    portfolio, overview, _ = service._parse_pas_core_snapshot(
        fallback_portfolio_id="P1",
        payload={
            "portfolio": {"portfolio_id": "P1"},
            "snapshot": {"overview": [], "holdings": {"holdingsByAssetClass": []}},
        },
        fallback_as_of_date="2026-02-24",
    )
    assert portfolio.portfolio_id == "P1"
    assert overview.market_value_base == 0.0
    assert overview.position_count == 0


def test_parse_pa_snapshot_empty_results_by_period_returns_none():
    service, _, _, _ = _build_service()
    result = service._parse_pa_snapshot((200, {"resultsByPeriod": {}}), [], [])
    assert result is None


def test_parse_pa_snapshot_non_dict_period_payload_returns_none():
    service, _, _, _ = _build_service()
    result = service._parse_pa_snapshot((200, {"resultsByPeriod": {"YTD": []}}), [], [])
    assert result is None


def test_parse_pa_snapshot_none_period_key_returns_none():
    service, _, _, _ = _build_service()
    result = service._parse_pa_snapshot(
        (200, {"resultsByPeriod": {None: {"net_cumulative_return": 1.0}}}),
        [],
        [],
    )
    assert result is None


def test_parse_dpm_snapshot_non_dict_latest_returns_not_available():
    service, _, _, _ = _build_service()
    result = service._parse_dpm_snapshot((200, {"items": ["bad"]}), [], [])
    assert result is not None
    assert result.status == "NOT_AVAILABLE"


def test_parse_dpm_snapshot_without_created_at_keeps_last_run_null():
    service, _, _, _ = _build_service()
    result = service._parse_dpm_snapshot((200, {"items": [{"status": "READY"}]}), [], [])
    assert result is not None
    assert result.last_run_at_utc is None


@pytest.mark.asyncio
async def test_workbench_analytics_prefers_split_risk_proxy_when_available():
    service, _, pa, _, _ = _build_service_with_risk_client()
    pa.analytics_payload = {
        "allocationBuckets": [],
        "topChanges": [],
        "riskProxy": {"hhiCurrent": 100.0, "hhiProposed": 100.0, "hhiDelta": 0.0},
        "portfolioReturnPct": 1.0,
        "benchmarkReturnPct": 0.8,
        "activeReturnPct": 0.2,
    }
    response = await service.get_workbench_analytics(
        portfolio_id="P1",
        correlation_id="corr-1",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL_60_40",
        session_id=None,
    )
    assert response.risk_proxy.hhi_current == 1234.0
