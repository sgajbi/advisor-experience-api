from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.clients.reporting_client import ReportingClient
from app.config import settings
from app.contracts.reporting import (
    ReportingReviewResponse,
    ReportingSnapshotResponse,
    ReportingSummaryResponse,
)
from app.middleware.correlation import correlation_id_var

router = APIRouter(prefix="/api/v1/reports", tags=["Reporting"])


@router.get(
    "/{portfolio_id}/snapshot",
    response_model=ReportingSnapshotResponse,
    summary="Get reporting snapshot",
    description=(
        "Fetches report-ready aggregated snapshot rows from lotus-report "
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
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
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

    generated_at_raw = payload.get("generatedAt")
    generated_at = datetime.now(UTC)
    if isinstance(generated_at_raw, str):
        try:
            generated_at = datetime.fromisoformat(generated_at_raw.replace("Z", "+00:00"))
        except ValueError:
            generated_at = datetime.now(UTC)

    return ReportingSnapshotResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        generatedAt=generated_at,
        rows=payload.get("rows", []),
    )


@router.post(
    "/{portfolio_id}/summary",
    response_model=ReportingSummaryResponse,
    summary="Get reporting summary",
    description=(
        "Fetches report-ready portfolio summary payload from lotus-report "
        "for one portfolio and as-of date."
    ),
)
async def get_reporting_summary(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    request: dict,
) -> ReportingSummaryResponse:
    client = ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
    correlation_id = correlation_id_var.get()
    status_code, payload = await client.post_portfolio_summary(
        portfolio_id=portfolio_id,
        payload=request,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting summary unavailable: {payload}",
        )
    as_of_date = str(request.get("as_of_date", request.get("asOfDate", "")))
    return ReportingSummaryResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        data=payload,
    )


@router.post(
    "/{portfolio_id}/review",
    response_model=ReportingReviewResponse,
    summary="Get reporting review",
    description=(
        "Fetches report-ready portfolio review payload from lotus-report "
        "for one portfolio and as-of date."
    ),
)
async def get_reporting_review(
    portfolio_id: Annotated[
        str,
        Path(
            description="Canonical portfolio identifier.",
            examples=["DEMO_DPM_EUR_001"],
        ),
    ],
    request: dict,
) -> ReportingReviewResponse:
    client = ReportingClient(
        base_url=settings.reporting_aggregation_base_url,
        timeout_seconds=settings.upstream_timeout_seconds,
        max_retries=settings.upstream_max_retries,
        retry_backoff_seconds=settings.upstream_retry_backoff_seconds,
    )
    correlation_id = correlation_id_var.get()
    status_code, payload = await client.post_portfolio_review(
        portfolio_id=portfolio_id,
        payload=request,
        correlation_id=correlation_id,
    )
    if status_code >= status.HTTP_400_BAD_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Reporting review unavailable: {payload}",
        )
    as_of_date = str(request.get("as_of_date", request.get("asOfDate", "")))
    return ReportingReviewResponse(
        correlationId=correlation_id,
        contractVersion=settings.contract_version,
        sourceService="lotus-report",
        portfolioId=portfolio_id,
        asOfDate=as_of_date,
        data=payload,
    )
