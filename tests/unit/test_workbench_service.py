import pytest

from app.services.workbench_service import WorkbenchService


class _StubPasClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        include_sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return self.status_code, self.payload

    async def get_projected_positions(self, session_id: str, correlation_id: str):
        return 200, {
            "positions": [
                {
                    "security_id": "EQ_1",
                    "instrument_name": "Equity 1",
                    "asset_class": "Equity",
                    "baseline_quantity": 10.0,
                    "proposed_quantity": 15.0,
                    "delta_quantity": 5.0,
                }
            ]
        }

    async def get_projected_summary(self, session_id: str, correlation_id: str):
        return 200, {
            "total_baseline_positions": 1,
            "total_proposed_positions": 1,
            "net_delta_quantity": 5.0,
        }

    async def create_simulation_session(
        self,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ):
        return 201, {"session": {"session_id": "sess_1", "version": 1}}

    async def add_simulation_changes(
        self,
        session_id: str,
        changes: list[dict],
        correlation_id: str,
    ):
        return 200, {"session_id": session_id, "version": 2}


class _StubPaClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload
        self.workbench_status_code = 200
        self.workbench_payload = {
            "portfolioId": "PF_1001",
            "period": "YTD",
            "groupBy": "ASSET_CLASS",
            "benchmarkCode": "MODEL_60_40",
            "portfolioReturnPct": 1.0,
            "benchmarkReturnPct": 3.1,
            "activeReturnPct": -2.1,
            "allocationBuckets": [
                {
                    "bucketKey": "EQUITY",
                    "bucketLabel": "EQUITY",
                    "currentQuantity": 10.0,
                    "proposedQuantity": 15.0,
                    "deltaQuantity": 5.0,
                    "currentWeightPct": 100.0,
                    "proposedWeightPct": 100.0,
                }
            ],
            "topChanges": [
                {
                    "securityId": "EQ_1",
                    "instrumentName": "Equity 1",
                    "deltaQuantity": 5.0,
                    "direction": "INCREASE",
                }
            ],
            "riskProxy": {"hhiCurrent": 10000.0, "hhiProposed": 10000.0, "hhiDelta": 0.0},
        }

    async def get_pas_input_twr(
        self,
        portfolio_id: str,
        as_of_date: str,
        periods: list[str],
        consumer_system: str,
        correlation_id: str,
    ):
        return self.status_code, self.payload

    async def get_workbench_analytics(self, payload: dict, correlation_id: str):  # noqa: ARG002
        return self.workbench_status_code, self.workbench_payload


class _StubDpmClient:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.payload = payload

    async def list_runs(self, params: dict, correlation_id: str):
        return self.status_code, self.payload

    async def simulate_proposal(
        self,
        body: dict,
        idempotency_key: str,
        correlation_id: str,
    ):
        return 200, {"status": "COMPLETED", "gate_decision": {"status": "PASS"}}


@pytest.mark.asyncio
async def test_workbench_overview_success():
    service = WorkbenchService(
        pas_client=_StubPasClient(
            200,
            {
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "base_currency": "USD",
                    "booking_center": "SG",
                    "cif_id": "CIF_1001",
                },
                "snapshot": {
                    "as_of_date": "2026-02-23",
                    "overview": {"total_market_value": 1000.0, "total_cash": 200.0},
                    "holdings": {
                        "holdingsByAssetClass": {
                            "Equity": [{"instrument_id": "EQ_1"}, {"instrument_id": "EQ_2"}]
                        }
                    },
                },
            },
        ),
        pa_client=_StubPaClient(
            200,
            {
                "resultsByPeriod": {
                    "YTD": {"net_cumulative_return": 3.2},
                }
            },
        ),
        dpm_client=_StubDpmClient(
            200,
            {
                "items": [
                    {
                        "rebalance_run_id": "rr_1",
                        "status": "READY",
                        "created_at": "2026-02-23T00:00:00Z",
                    }
                ]
            },
        ),
    )

    response = await service.get_workbench_overview(
        portfolio_id="PF_1001",
        correlation_id="corr-1",
    )

    assert response.portfolio.portfolio_id == "PF_1001"
    assert response.overview.position_count == 2
    assert response.performance_snapshot is not None
    assert response.performance_snapshot.return_pct == 3.2
    assert response.rebalance_snapshot is not None
    assert response.rebalance_snapshot.status == "READY"
    assert response.partial_failures == []


@pytest.mark.asyncio
async def test_workbench_overview_partial_failures():
    service = WorkbenchService(
        pas_client=_StubPasClient(
            200,
            {
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "base_currency": "USD",
                },
                "snapshot": {
                    "as_of_date": "2026-02-23",
                    "overview": {"total_market_value": 500.0, "total_cash": 50.0},
                },
            },
        ),
        pa_client=_StubPaClient(503, {"detail": "pa unavailable"}),
        dpm_client=_StubDpmClient(500, {"detail": "dpm unavailable"}),
    )

    response = await service.get_workbench_overview(
        portfolio_id="PF_1001",
        correlation_id="corr-2",
    )

    assert response.performance_snapshot is None
    assert response.rebalance_snapshot is None
    assert len(response.partial_failures) == 2
    assert response.warnings == ["PA_SNAPSHOT_UNAVAILABLE", "DPM_REBALANCE_UNAVAILABLE"]


@pytest.mark.asyncio
async def test_workbench_portfolio_360_with_projected_state():
    service = WorkbenchService(
        pas_client=_StubPasClient(
            200,
            {
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "base_currency": "USD",
                    "booking_center": "SG",
                    "cif_id": "CIF_1001",
                },
                "snapshot": {
                    "as_of_date": "2026-02-23",
                    "overview": {"total_market_value": 1000.0, "total_cash": 200.0},
                    "holdings": {
                        "holdingsByAssetClass": {
                            "Equity": [
                                {
                                    "instrument_id": "EQ_1",
                                    "instrument_name": "Equity 1",
                                    "quantity": 10,
                                    "valuation": {"market_value": 420.5},
                                }
                            ]
                        }
                    },
                },
            },
        ),
        pa_client=_StubPaClient(200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.0}}}),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )
    response = await service.get_portfolio_360(
        portfolio_id="PF_1001",
        correlation_id="corr-3",
        session_id="sess_1",
    )
    assert response.active_session_id == "sess_1"
    assert len(response.current_positions) == 1
    assert response.current_positions[0].market_value_base == 420.5
    assert response.current_positions[0].weight_pct == pytest.approx(42.05)
    assert len(response.projected_positions) == 1
    assert response.projected_summary is not None
    assert response.projected_summary.net_delta_quantity == 5.0


@pytest.mark.asyncio
async def test_workbench_apply_sandbox_changes_with_policy_eval():
    service = WorkbenchService(
        pas_client=_StubPasClient(
            200,
            {
                "portfolio": {"portfolio_id": "PF_1001", "base_currency": "USD"},
                "snapshot": {
                    "as_of_date": "2026-02-23",
                    "overview": {"total_market_value": 1000, "total_cash": 200},
                },
            },
        ),
        pa_client=_StubPaClient(200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.0}}}),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )
    response = await service.apply_sandbox_changes(
        portfolio_id="PF_1001",
        session_id="sess_1",
        correlation_id="corr-4",
        changes=[{"security_id": "EQ_1", "transaction_type": "BUY", "quantity": 5}],
        evaluate_policy=True,
    )
    assert response.session_id == "sess_1"
    assert response.session_version == 2
    assert response.policy_feedback is not None
    assert response.policy_feedback.status == "PASS"


@pytest.mark.asyncio
async def test_workbench_analytics_response():
    service = WorkbenchService(
        pas_client=_StubPasClient(
            200,
            {
                "portfolio": {
                    "portfolio_id": "PF_1001",
                    "base_currency": "USD",
                },
                "snapshot": {
                    "as_of_date": "2026-02-23",
                    "overview": {"total_market_value": 1000.0, "total_cash": 200.0},
                    "holdings": {
                        "holdingsByAssetClass": {
                            "Equity": [
                                {
                                    "instrument_id": "EQ_1",
                                    "instrument_name": "Equity 1",
                                    "quantity": 10,
                                    "market_value_base": 300.0,
                                }
                            ]
                        }
                    },
                },
            },
        ),
        pa_client=_StubPaClient(200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 1.0}}}),
        dpm_client=_StubDpmClient(200, {"items": []}),
    )
    response = await service.get_workbench_analytics(
        portfolio_id="PF_1001",
        correlation_id="corr-5",
        period="YTD",
        group_by="ASSET_CLASS",
        benchmark_code="MODEL_60_40",
        session_id="sess_1",
    )
    assert response.portfolio_id == "PF_1001"
    assert response.group_by == "ASSET_CLASS"
    assert len(response.allocation_buckets) == 1
    assert response.top_changes[0].security_id == "EQ_1"
    assert response.risk_proxy.hhi_current == 10000.0
