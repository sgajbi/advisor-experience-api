from fastapi import APIRouter, File, Form, Query, UploadFile

from app.clients.pas_client import PasClient
from app.clients.pas_ingestion_client import PasIngestionClient
from app.config import settings
from app.contracts.intake import EnvelopeResponse, IntakeBundleRequest, LookupResponse
from app.middleware.correlation import correlation_id_var
from app.services.intake_service import IntakeService

router = APIRouter(tags=["intake", "lookups"])


def _intake_service() -> IntakeService:
    return IntakeService(
        pas_ingestion_client=PasIngestionClient(
            base_url=settings.portfolio_data_ingestion_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
        pas_query_client=PasClient(
            base_url=settings.portfolio_data_platform_base_url,
            timeout_seconds=settings.upstream_timeout_seconds,
        ),
    )


@router.post(
    "/api/v1/intake/portfolio-bundle",
    response_model=EnvelopeResponse,
    summary="Ingest Portfolio Bundle via PAS",
    description="Pass-through endpoint for PAS ingestion /ingest/portfolio-bundle.",
)
async def ingest_portfolio_bundle(request: IntakeBundleRequest) -> EnvelopeResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.ingest_portfolio_bundle(body=request.body, correlation_id=correlation_id)


@router.post(
    "/api/v1/intake/uploads/preview",
    response_model=EnvelopeResponse,
    summary="Preview PAS Upload",
    description="Pass-through endpoint for PAS upload preview /ingest/uploads/preview.",
)
async def preview_upload(
    entity_type: str = Form(..., alias="entityType"),
    file: UploadFile = File(...),
    sample_size: int = Form(20, alias="sampleSize", ge=1, le=100),
) -> EnvelopeResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.preview_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        sample_size=sample_size,
        correlation_id=correlation_id,
    )


@router.post(
    "/api/v1/intake/uploads/commit",
    response_model=EnvelopeResponse,
    summary="Commit PAS Upload",
    description="Pass-through endpoint for PAS upload commit /ingest/uploads/commit.",
)
async def commit_upload(
    entity_type: str = Form(..., alias="entityType"),
    file: UploadFile = File(...),
    allow_partial: bool = Form(False, alias="allowPartial"),
) -> EnvelopeResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.commit_upload(
        entity_type=entity_type,
        filename=file.filename or "upload.csv",
        content=await file.read(),
        allow_partial=allow_partial,
        correlation_id=correlation_id,
    )


@router.get(
    "/api/v1/lookups/portfolios",
    response_model=LookupResponse,
    summary="Portfolio Lookup Catalog",
    description="Returns PAS-backed portfolio lookup options for UI selectors.",
)
async def get_portfolio_lookups() -> LookupResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_portfolio_lookups(correlation_id=correlation_id)


@router.get(
    "/api/v1/lookups/instruments",
    response_model=LookupResponse,
    summary="Instrument Lookup Catalog",
    description="Returns PAS-backed instrument lookup options for UI selectors.",
)
async def get_instrument_lookups(limit: int = Query(default=200, ge=1, le=1000)) -> LookupResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_instrument_lookups(limit=limit, correlation_id=correlation_id)


@router.get(
    "/api/v1/lookups/currencies",
    response_model=LookupResponse,
    summary="Currency Lookup Catalog",
    description="Returns PAS-backed currency codes from portfolio and instrument reference data.",
)
async def get_currency_lookups() -> LookupResponse:
    service = _intake_service()
    correlation_id = correlation_id_var.get()
    return await service.get_currency_lookups(correlation_id=correlation_id)
