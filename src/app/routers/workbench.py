from fastapi import APIRouter

from app.clients.dpm_client import DpmClient
from app.clients.pa_client import PaClient
from app.clients.pas_client import PasClient
from app.config import settings
from app.contracts.workbench import WorkbenchOverviewResponse
from app.middleware.correlation import correlation_id_var
from app.services.workbench_service import WorkbenchService

router = APIRouter(prefix="/api/v1/workbench", tags=["workbench"])


def _workbench_service() -> WorkbenchService:
    return WorkbenchService(
        pas_client=PasClient(
            base_url=settings.portfolio_data_platform_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
        pa_client=PaClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
        dpm_client=DpmClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
    )


@router.get(
    "/{portfolio_id}/overview",
    response_model=WorkbenchOverviewResponse,
    summary="Get Workbench Overview",
    description=(
        "Aggregates PAS core snapshot, PA performance snapshot, and latest DPM rebalance "
        "status into a single decision-console overview contract."
    ),
)
async def get_workbench_overview(portfolio_id: str) -> WorkbenchOverviewResponse:
    service = _workbench_service()
    correlation_id = correlation_id_var.get()
    return await service.get_workbench_overview(
        portfolio_id=portfolio_id,
        correlation_id=correlation_id,
    )
