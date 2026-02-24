from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.reporting import ReportingSnapshotResponse
from app.middleware.correlation import correlation_id_var

router = APIRouter(prefix="/api/v1/reports", tags=["Reporting"])


@router.get(
    "/{portfolio_id}/snapshot",
    response_model=ReportingSnapshotResponse,
    summary="Get reporting snapshot",
    description=(
        "Fetches report-ready aggregated snapshot rows from reporting-aggregation-service "
        "for one portfolio and as-of date."
    ),
)
async def get_reporting_snapshot(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    as_of_date: Annotated[
        str,
        Query(alias="asOfDate", description="Business as-of date (YYYY-MM-DD)."),
    ],
) -> ReportingSnapshotResponse:
    client = ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
    )
    correlation_id = correlation_id_var.get()
    status_code, payload = await client.get_portfolio_snapshot(
        portfolio_id=portfolio_id,
        as_of_date=as_of_date,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting snapshot unavailable: {payload}",
        )

    return ReportingSnapshotResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="reporting-aggregation-service",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        generatedAt=datetime.now(UTC),
        rows=payload.get("rows", []),
    )
