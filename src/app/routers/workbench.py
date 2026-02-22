from fastapi import APIRouter, Request

from app.clients.decisioning_client import DecisioningClient
from app.clients.performance_client import PerformanceClient
from app.clients.portfolio_core_client import PortfolioCoreClient
from app.config import settings
from app.contracts.workbench import WorkbenchOverviewResponse
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service import WorkbenchService

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


@router.get("/{portfolio_id}/overview", response_model=WorkbenchOverviewResponse)
async def get_workbench_overview(portfolio_id: str, request: Request):
    _ = request
    service = WorkbenchService(
        portfolio_client=PortfolioCoreClient(
            base_url=settings.portfolio_core_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
        performance_client=PerformanceClient(
            base_url=settings.performance_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
        decisioning_client=DecisioningClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
    )
    correlation_id = correlation_id_var.get()
    return await service.get_overview(portfolio_id=portfolio_id, correlation_id=correlation_id)
