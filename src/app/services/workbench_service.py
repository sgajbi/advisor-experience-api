import asyncio
from datetime import UTC, date, datetime
from typing import Any, cast

from fastapi import HTTPException, status

from app.clients.dpm_client import DpmClient
from app.clients.pa_client import PaClient
from app.clients.pas_client import PasClient
from app.config import settings
from app.contracts.workbench import (
    WorkbenchOverviewResponse,
    WorkbenchOverviewSummary,
    WorkbenchPartialFailure,
    WorkbenchPerformanceSnapshot,
    WorkbenchPortfolioSummary,
    WorkbenchRebalanceSnapshot,
)


class WorkbenchService:
    def __init__(
        self,
        pas_client: PasClient,
        pa_client: PaClient,
        dpm_client: DpmClient,
    ):
        self._pas_client = pas_client
        self._pa_client = pa_client
        self._dpm_client = dpm_client

    async def get_workbench_overview(
        self,
        portfolio_id: str,
        correlation_id: str,
    ) -> WorkbenchOverviewResponse:
        as_of_date = date.today().isoformat()
        pas_status, pas_payload = await self._pas_client.get_core_snapshot(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            include_sections=["OVERVIEW", "PERFORMANCE", "HOLDINGS"],
            consumer_system="BFF",
            correlation_id=correlation_id,
        )
        self._raise_for_pas_error(pas_status, pas_payload)

        portfolio, overview, as_of_date = self._parse_pas_core_snapshot(
            fallback_portfolio_id=portfolio_id,
            payload=pas_payload,
            fallback_as_of_date=as_of_date,
        )

        pa_task = self._pa_client.get_pas_snapshot_twr(
            portfolio_id=portfolio_id,
            as_of_date=as_of_date,
            periods=["YTD"],
            consumer_system="BFF",
            correlation_id=correlation_id,
        )
        dpm_task = self._dpm_client.list_runs(
            params={"portfolio_id": portfolio_id, "limit": 1},
            correlation_id=correlation_id,
        )
        gathered = await asyncio.gather(pa_task, dpm_task, return_exceptions=True)
        pa_result = cast(object, gathered[0])
        dpm_result = cast(object, gathered[1])

        partial_failures: list[WorkbenchPartialFailure] = []
        warnings: list[str] = []

        performance_snapshot = self._parse_pa_snapshot(
            result=pa_result,
            partial_failures=partial_failures,
            warnings=warnings,
        )
        rebalance_snapshot = self._parse_dpm_snapshot(
            result=dpm_result,
            partial_failures=partial_failures,
            warnings=warnings,
        )

        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=as_of_date,
            portfolio=portfolio,
            overview=overview,
            performance_snapshot=performance_snapshot,
            rebalance_snapshot=rebalance_snapshot,
            warnings=warnings,
            partial_failures=partial_failures,
        )

    def _raise_for_pas_error(self, upstream_status: int, payload: dict[str, Any]) -> None:
        if upstream_status < status.HTTP_400_BAD_REQUEST:
            return
        detail = str(payload.get("detail", payload))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PAS core snapshot unavailable: {detail}",
        )

    def _parse_pas_core_snapshot(
        self,
        fallback_portfolio_id: str,
        payload: dict[str, Any],
        fallback_as_of_date: str,
    ) -> tuple[WorkbenchPortfolioSummary, WorkbenchOverviewSummary, str]:
        portfolio_payload = payload.get("portfolio", {}) if isinstance(payload, dict) else {}
        snapshot_payload = payload.get("snapshot", {}) if isinstance(payload, dict) else {}

        if not isinstance(portfolio_payload, dict) or not isinstance(snapshot_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid PAS core snapshot payload structure.",
            )

        overview_payload = snapshot_payload.get("overview", {})
        if not isinstance(overview_payload, dict):
            overview_payload = {}
        holdings_payload = snapshot_payload.get("holdings", {})
        holdings_by_asset_class = {}
        if isinstance(holdings_payload, dict):
            candidate = holdings_payload.get("holdingsByAssetClass", {})
            if isinstance(candidate, dict):
                holdings_by_asset_class = candidate

        total_market_value = float(overview_payload.get("total_market_value", 0.0))
        total_cash = float(overview_payload.get("total_cash", 0.0))
        cash_weight = 0.0
        if total_market_value > 0:
            cash_weight = max(0.0, total_cash / total_market_value)

        position_count = 0
        for positions in holdings_by_asset_class.values():
            if isinstance(positions, list):
                position_count += len(positions)

        as_of_date = str(snapshot_payload.get("as_of_date", fallback_as_of_date))
        portfolio = WorkbenchPortfolioSummary(
            portfolio_id=str(portfolio_payload.get("portfolio_id", fallback_portfolio_id)),
            client_id=(
                str(portfolio_payload["cif_id"])
                if portfolio_payload.get("cif_id") is not None
                else None
            ),
            base_currency=str(portfolio_payload.get("base_currency", "USD")),
            booking_center_code=(
                str(portfolio_payload["booking_center"])
                if portfolio_payload.get("booking_center") is not None
                else None
            ),
        )
        overview = WorkbenchOverviewSummary(
            market_value_base=total_market_value,
            cash_weight_pct=cash_weight,
            position_count=position_count,
        )
        return portfolio, overview, as_of_date

    def _parse_pa_snapshot(
        self,
        result: object,
        partial_failures: list[WorkbenchPartialFailure],
        warnings: list[str],
    ) -> WorkbenchPerformanceSnapshot | None:
        if isinstance(result, Exception):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="pa",
                    error_code="UPSTREAM_EXCEPTION",
                    detail=str(result),
                )
            )
            warnings.append("PA_SNAPSHOT_UNAVAILABLE")
            return None

        if not isinstance(result, tuple) or len(result) != 2:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="pa",
                    error_code="INVALID_UPSTREAM_RESPONSE",
                    detail=f"unexpected result type: {type(result)}",
                )
            )
            warnings.append("PA_SNAPSHOT_UNAVAILABLE")
            return None

        pa_status, pa_payload = result
        if not isinstance(pa_payload, dict):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="pa",
                    error_code="INVALID_UPSTREAM_PAYLOAD",
                    detail=f"unexpected payload type: {type(pa_payload)}",
                )
            )
            warnings.append("PA_SNAPSHOT_UNAVAILABLE")
            return None

        if pa_status >= status.HTTP_400_BAD_REQUEST:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="pa",
                    error_code=f"HTTP_{pa_status}",
                    detail=str(pa_payload.get("detail", pa_payload)),
                )
            )
            warnings.append("PA_SNAPSHOT_UNAVAILABLE")
            return None

        results_by_period = pa_payload.get("resultsByPeriod", {})
        if not isinstance(results_by_period, dict):
            warnings.append("PA_SNAPSHOT_INVALID")
            return None

        if "YTD" in results_by_period:
            period_key = "YTD"
        else:
            keys = iter(results_by_period)
            try:
                period_key = next(keys)
            except StopIteration:
                return None

        if period_key is None:
            return None

        period_payload = results_by_period.get(period_key, {})
        if not isinstance(period_payload, dict):
            return None

        return WorkbenchPerformanceSnapshot(
            period=period_key,
            return_pct=period_payload.get("net_cumulative_return"),
            benchmark_return_pct=None,
        )

    def _parse_dpm_snapshot(
        self,
        result: object,
        partial_failures: list[WorkbenchPartialFailure],
        warnings: list[str],
    ) -> WorkbenchRebalanceSnapshot | None:
        if isinstance(result, Exception):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="dpm",
                    error_code="UPSTREAM_EXCEPTION",
                    detail=str(result),
                )
            )
            warnings.append("DPM_REBALANCE_UNAVAILABLE")
            return None

        if not isinstance(result, tuple) or len(result) != 2:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="dpm",
                    error_code="INVALID_UPSTREAM_RESPONSE",
                    detail=f"unexpected result type: {type(result)}",
                )
            )
            warnings.append("DPM_REBALANCE_UNAVAILABLE")
            return None

        dpm_status, dpm_payload = result
        if not isinstance(dpm_payload, dict):
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="dpm",
                    error_code="INVALID_UPSTREAM_PAYLOAD",
                    detail=f"unexpected payload type: {type(dpm_payload)}",
                )
            )
            warnings.append("DPM_REBALANCE_UNAVAILABLE")
            return None

        if dpm_status >= status.HTTP_400_BAD_REQUEST:
            partial_failures.append(
                WorkbenchPartialFailure(
                    source_service="dpm",
                    error_code=f"HTTP_{dpm_status}",
                    detail=str(dpm_payload.get("detail", dpm_payload)),
                )
            )
            warnings.append("DPM_REBALANCE_UNAVAILABLE")
            return None

        items = dpm_payload.get("items", [])
        if not isinstance(items, list) or not items:
            return WorkbenchRebalanceSnapshot(status="NOT_AVAILABLE")

        latest = items[0]
        if not isinstance(latest, dict):
            return WorkbenchRebalanceSnapshot(status="NOT_AVAILABLE")

        created_at = latest.get("created_at")
        last_run_at_utc = None
        if isinstance(created_at, str):
            last_run_at_utc = created_at
        elif isinstance(created_at, datetime):
            last_run_at_utc = created_at.astimezone(UTC).isoformat()

        return WorkbenchRebalanceSnapshot(
            status=str(latest.get("status", "UNKNOWN")),
            last_rebalance_run_id=(
                str(latest["rebalance_run_id"])
                if latest.get("rebalance_run_id") is not None
                else None
            ),
            last_run_at_utc=last_run_at_utc,
        )
