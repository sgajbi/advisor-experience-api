import pytest
from fastapi import HTTPException

from app.services.intake_service import IntakeService


class _PasIngestionStub:
    async def ingest_portfolio_bundle(self, body, correlation_id):  # noqa: ANN001
        _ = body, correlation_id
        return 202, {"message": "ok"}

    async def preview_upload(self, entity_type, filename, content, sample_size, correlation_id):  # noqa: ANN001
        _ = entity_type, filename, content, sample_size, correlation_id
        return 200, {"entity_type": "portfolios", "valid_rows": 1}

    async def commit_upload(self, entity_type, filename, content, allow_partial, correlation_id):  # noqa: ANN001
        _ = entity_type, filename, content, allow_partial, correlation_id
        return 202, {"entity_type": "portfolios", "published_rows": 1}


class _PasQueryStub:
    async def get_portfolio_lookups(self, correlation_id):  # noqa: ANN001
        _ = correlation_id
        return 200, {"items": [{"id": "PF_1", "label": "PF_1"}]}

    async def get_instrument_lookups(self, limit, correlation_id):  # noqa: ANN001
        _ = limit, correlation_id
        return 200, {"items": [{"id": "SEC_1", "label": "SEC_1 | Apple Inc."}]}

    async def get_currency_lookups(self, correlation_id):  # noqa: ANN001
        _ = correlation_id
        return 200, {"items": [{"id": "EUR", "label": "EUR"}, {"id": "USD", "label": "USD"}]}


@pytest.mark.asyncio
async def test_intake_service_happy_paths():
    service = IntakeService(
        pas_ingestion_client=_PasIngestionStub(),
        pas_query_client=_PasQueryStub(),
    )

    ingest = await service.ingest_portfolio_bundle(
        body={"sourceSystem": "UI"},
        correlation_id="corr-1",
    )
    assert ingest.data["message"] == "ok"

    preview = await service.preview_upload(
        entity_type="portfolios",
        filename="sample.csv",
        content=b"x",
        sample_size=10,
        correlation_id="corr-1",
    )
    assert preview.data["valid_rows"] == 1

    commit = await service.commit_upload(
        entity_type="portfolios",
        filename="sample.csv",
        content=b"x",
        allow_partial=False,
        correlation_id="corr-1",
    )
    assert commit.data["published_rows"] == 1

    portfolio_lookups = await service.get_portfolio_lookups(correlation_id="corr-1")
    assert portfolio_lookups.items[0].id == "PF_1"

    instrument_lookups = await service.get_instrument_lookups(limit=50, correlation_id="corr-1")
    assert instrument_lookups.items[0].id == "SEC_1"

    currency_lookups = await service.get_currency_lookups(correlation_id="corr-1")
    assert [item.id for item in currency_lookups.items] == ["EUR", "USD"]


@pytest.mark.asyncio
async def test_intake_service_raises_upstream_error():
    class _ErrorPasIngestionStub(_PasIngestionStub):
        async def ingest_portfolio_bundle(self, body, correlation_id):  # noqa: ANN001
            _ = body, correlation_id
            return 400, {"detail": "bad request"}

    service = IntakeService(
        pas_ingestion_client=_ErrorPasIngestionStub(),
        pas_query_client=_PasQueryStub(),
    )

    try:
        await service.ingest_portfolio_bundle(body={"x": 1}, correlation_id="corr-1")
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        raise AssertionError("Expected HTTPException")
