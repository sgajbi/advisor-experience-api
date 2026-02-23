from fastapi.testclient import TestClient

from app.main import app


def test_ingest_portfolio_bundle_success(monkeypatch):
    async def _fake_ingest(*args, **kwargs):
        return 202, {"message": "queued"}

    monkeypatch.setattr(
        "app.clients.pas_ingestion_client.PasIngestionClient.ingest_portfolio_bundle",
        _fake_ingest,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/portfolio-bundle",
        json={"body": {"sourceSystem": "UI", "portfolios": []}},
    )

    assert response.status_code == 200
    assert response.json()["data"]["message"] == "queued"


def test_preview_upload_success(monkeypatch):
    async def _fake_preview(*args, **kwargs):
        return 200, {"entity_type": "portfolios", "valid_rows": 1}

    monkeypatch.setattr(
        "app.clients.pas_ingestion_client.PasIngestionClient.preview_upload",
        _fake_preview,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/uploads/preview",
        data={"entityType": "portfolios", "sampleSize": "20"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["data"]["entity_type"] == "portfolios"


def test_commit_upload_success(monkeypatch):
    async def _fake_commit(*args, **kwargs):
        return 202, {"entity_type": "portfolios", "published_rows": 1}

    monkeypatch.setattr(
        "app.clients.pas_ingestion_client.PasIngestionClient.commit_upload",
        _fake_commit,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/intake/uploads/commit",
        data={"entityType": "portfolios", "allowPartial": "true"},
        files={"file": ("sample.csv", b"portfolio_id\nPF1\n", "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["data"]["published_rows"] == 1


def test_lookups_success(monkeypatch):
    async def _fake_portfolios(*args, **kwargs):
        return 200, {"portfolios": [{"portfolio_id": "PF_1"}]}

    async def _fake_instruments(*args, **kwargs):
        return 200, {"instruments": [{"security_id": "SEC_1", "currency": "USD"}]}

    monkeypatch.setattr("app.clients.pas_client.PasClient.list_portfolios", _fake_portfolios)
    monkeypatch.setattr("app.clients.pas_client.PasClient.list_instruments", _fake_instruments)

    client = TestClient(app)

    portfolio_response = client.get("/api/v1/lookups/portfolios")
    instrument_response = client.get("/api/v1/lookups/instruments?limit=50")
    currency_response = client.get("/api/v1/lookups/currencies")

    assert portfolio_response.status_code == 200
    assert portfolio_response.json()["items"][0]["id"] == "PF_1"

    assert instrument_response.status_code == 200
    assert instrument_response.json()["items"][0]["id"] == "SEC_1"

    assert currency_response.status_code == 200
    assert currency_response.json()["items"][0]["id"] == "USD"
