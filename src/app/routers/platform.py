from fastapi import APIRouter, Header, Query

from app.clients.dpm_client import DpmClient
from app.clients.pa_client import PaClient
from app.clients.pas_client import PasClient
from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.platform_capabilities import PlatformCapabilitiesResponse
from app.middleware.correlation import correlation_id_var
from app.services.platform_capabilities_service import PlatformCapabilitiesService

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


def _platform_capabilities_service() -> PlatformCapabilitiesService:
    return PlatformCapabilitiesService(
        dpm_client=DpmClient(
            base_url=settings.decisioning_service_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        pas_client=PasClient(
            base_url=settings.portfolio_data_platform_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        pa_client=PaClient(
            base_url=settings.performance_analytics_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        reporting_client=ReportingClient(
            base_url=settings.reporting_aggregation_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
            max_retries=settings.upstream_max_retries,
            retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
        ),
        contract_version=settings.contract_version,
    )


@router.get(
    "/capabilities",
    response_model=PlatformCapabilitiesResponse,
    summary="Get Aggregated Platform Capabilities",
    description=(
        "Aggregates PAS, PA, DPM, and RAS integration capabilities into one BFF contract "
        "for UI feature control and workflow negotiation."
    ),
)
async def get_platform_capabilities(
    consumer_system: str = Query("BFF", alias="consumerSystem"),
    tenant_id: str = Query("default", alias="tenantId"),
    x_correlation_id: str | None = Header(default=None, alias="X-Correlation-Id"),
) -> PlatformCapabilitiesResponse:
    service = _platform_capabilities_service()
    correlation_id = x_correlation_id or correlation_id_var.get() or ""
    return await service.get_platform_capabilities(
        consumer_system=consumer_system,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )
