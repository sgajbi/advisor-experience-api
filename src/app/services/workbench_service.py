import asyncio
from datetime import date

from app.clients.decisioning_client import DecisioningClient
from app.clients.performance_client import PerformanceClient
from app.clients.portfolio_core_client import PortfolioCoreClient
from app.config import settings
from app.contracts.workbench import PartialFailure, WorkbenchOverviewResponse


class WorkbenchService:
    def __init__(
        self,
        portfolio_client: PortfolioCoreClient,
        performance_client: PerformanceClient,
        decisioning_client: DecisioningClient,
    ):
        self._portfolio_client = portfolio_client
        self._performance_client = performance_client
        self._decisioning_client = decisioning_client

    async def get_overview(self, portfolio_id: str, correlation_id: str) -> WorkbenchOverviewResponse:
        partial_failures: list[PartialFailure] = []

        portfolio_task = self._portfolio_client.get_portfolio_overview(portfolio_id, correlation_id)
        perf_task = self._performance_client.get_performance_snapshot(portfolio_id, correlation_id)
        rebalance_task = self._decisioning_client.get_rebalance_snapshot(portfolio_id, correlation_id)

        portfolio_res, perf_res, rebalance_res = await asyncio.gather(
            portfolio_task, perf_task, rebalance_task, return_exceptions=True
        )

        if isinstance(portfolio_res, Exception):
            raise RuntimeError(f"Portfolio core dependency failed: {portfolio_res}")

        if isinstance(perf_res, Exception):
            partial_failures.append(
                PartialFailure(
                    source_service="performance-intelligence-service",
                    error_code="UPSTREAM_ERROR",
                    detail=str(perf_res),
                )
            )
            perf_res = None

        if isinstance(rebalance_res, Exception):
            partial_failures.append(
                PartialFailure(
                    source_service="portfolio-decisioning-service",
                    error_code="UPSTREAM_ERROR",
                    detail=str(rebalance_res),
                )
            )
            rebalance_res = None

        return WorkbenchOverviewResponse(
            correlation_id=correlation_id,
            contract_version=settings.contract_version,
            as_of_date=portfolio_res.get("as_of_date", str(date.today())),
            portfolio=portfolio_res["portfolio"],
            overview=portfolio_res["overview"],
            performance_snapshot=perf_res,
            rebalance_snapshot=rebalance_res,
            warnings=[],
            partial_failures=partial_failures,
        )
