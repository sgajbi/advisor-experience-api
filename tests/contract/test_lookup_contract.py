from fastapi.testclient import TestClient

from app.main import app


def test_lookup_contract_shape_passthrough(monkeypatch):
    async def _fake_portfolio_lookups(*args, **kwargs):
        return 200, {"items": [{"id": "PF_1", "label": "PF_1"}]}

    async def _fake_instrument_lookups(*args, **kwargs):
        return 200, {"items": [{"id": "SEC_1", "label": "SEC_1 | Apple Inc."}]}

    async def _fake_currency_lookups(*args, **kwargs):
        return 200, {"items": [{"id": "USD", "label": "USD"}]}

    monkeypatch.setattr(
        "app.clients.pas_client.PasClient.get_portfolio_lookups",
        _fake_portfolio_lookups,
    )
    monkeypatch.setattr(
        "app.clients.pas_client.PasClient.get_instrument_lookups",
        _fake_instrument_lookups,
    )
    monkeypatch.setattr(
        "app.clients.pas_client.PasClient.get_currency_lookups",
        _fake_currency_lookups,
    )

    client = TestClient(app)

    portfolio_response = client.get("/api/v1/lookups/portfolios")
    instrument_response = client.get("/api/v1/lookups/instruments?limit=200")
    currency_response = client.get("/api/v1/lookups/currencies")

    assert portfolio_response.status_code == 200
    assert instrument_response.status_code == 200
    assert currency_response.status_code == 200

    for response in [portfolio_response, instrument_response, currency_response]:
        payload = response.json()
        assert payload["contract_version"] == "v1"
        assert isinstance(payload["correlation_id"], str)
        assert payload["correlation_id"] != ""
        assert isinstance(payload["items"], list)
        assert isinstance(payload["items"][0]["id"], str)
        assert isinstance(payload["items"][0]["label"], str)


def test_lookup_contract_invalid_upstream_payload_maps_to_502(monkeypatch):
    async def _bad_payload(*args, **kwargs):
        return 200, {"items": [{"id": 100, "label": None}]}

    monkeypatch.setattr(
        "app.clients.pas_client.PasClient.get_portfolio_lookups",
        _bad_payload,
    )

    client = TestClient(app)
    response = client.get("/api/v1/lookups/portfolios")
    assert response.status_code == 502
