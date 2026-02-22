import pytest
from app.services.workbench_service import WorkbenchService


class _OkPortfolio:
    async def get_portfolio_overview(self, portfolio_id: str, correlation_id: str):
        _ = portfolio_id, correlation_id
        return {
            "as_of_date": "2026-02-22",
            "portfolio": {
                "portfolio_id": "PF_1",
                "client_id": "C_1",
                "base_currency": "USD",
                "booking_center_code": "SG",
            },
            "overview": {"market_value_base": 10.0, "cash_weight_pct": 0.2, "position_count": 3},
        }


class _FailPerf:
    async def get_performance_snapshot(self, portfolio_id: str, correlation_id: str):
        _ = portfolio_id, correlation_id
        raise RuntimeError("timeout")


class _OkDecisioning:
    async def get_rebalance_snapshot(self, portfolio_id: str, correlation_id: str):
        _ = portfolio_id, correlation_id
        return {"status": "READY", "last_rebalance_run_id": "rr_1", "last_run_at_utc": None}


@pytest.mark.asyncio
async def test_partial_failure_when_performance_unavailable():
    service = WorkbenchService(_OkPortfolio(), _FailPerf(), _OkDecisioning())
    result = await service.get_overview("PF_1", "corr_1")
    assert result.portfolio.portfolio_id == "PF_1"
    assert result.performance_snapshot is None
    assert len(result.partial_failures) == 1
