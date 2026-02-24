from fastapi.testclient import TestClient

from app.main import app


def test_reporting_snapshot_success(monkeypatch):
    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ARG001
        return (
            200,
            {
                "generatedAt": "2026-02-24T07:00:00Z",
                "rows": [
                    {"bucket": "TOTAL", "metric": "market_value_base", "value": 1250000.0},
                    {"bucket": "TOTAL", "metric": "return_ytd_pct", "value": 4.2},
                ],
            },
        )

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    assert response.status_code == 200
    body = response.json()
    assert body["portfolioId"] == "DEMO_DPM_EUR_001"
    assert body["generatedAt"].startswith("2026-02-24T07:00:00")
    assert len(body["rows"]) == 2


def test_reporting_snapshot_invalid_generated_at_fallback(monkeypatch):
    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ARG001
        return (
            200,
            {
                "generatedAt": "invalid",
                "rows": [{"bucket": "TOTAL", "metric": "market_value_base", "value": 1.0}],
            },
        )

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    assert response.status_code == 200
    body = response.json()
    assert body["generatedAt"] is not None


def test_reporting_snapshot_upstream_error(monkeypatch):
    async def _mock_get_portfolio_snapshot(self, portfolio_id, as_of_date, correlation_id):  # noqa: ARG001
        return 503, {"detail": "upstream unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.get_portfolio_snapshot",
        _mock_get_portfolio_snapshot,
    )

    client = TestClient(app)
    response = client.get("/api/v1/reports/DEMO_DPM_EUR_001/snapshot?asOfDate=2026-02-24")
    assert response.status_code == 502


def test_reporting_summary_success(monkeypatch):
    async def _mock_post_summary(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        return 200, {
            "scope": {"portfolio_id": portfolio_id},
            "wealth": {"total_market_value": 123.0},
        }

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_summary",
        _mock_post_summary,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/summary",
        json={"as_of_date": "2026-02-24", "sections": ["WEALTH"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["portfolioId"] == "DEMO_DPM_EUR_001"
    assert body["asOfDate"] == "2026-02-24"
    assert body["data"]["wealth"]["total_market_value"] == 123.0


def test_reporting_review_success(monkeypatch):
    async def _mock_post_review(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        return 200, {"portfolio_id": portfolio_id, "overview": {"total_market_value": 1000.0}}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_review",
        _mock_post_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/review",
        json={"asOfDate": "2026-02-24", "sections": ["OVERVIEW"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["portfolioId"] == "DEMO_DPM_EUR_001"
    assert body["asOfDate"] == "2026-02-24"
    assert body["data"]["overview"]["total_market_value"] == 1000.0


def test_reporting_summary_upstream_error(monkeypatch):
    async def _mock_post_summary(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        return 503, {"detail": "summary unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_summary",
        _mock_post_summary,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/summary",
        json={"as_of_date": "2026-02-24"},
    )
    assert response.status_code == 502


def test_reporting_review_upstream_error(monkeypatch):
    async def _mock_post_review(self, portfolio_id, payload, correlation_id):  # noqa: ARG001
        return 503, {"detail": "review unavailable"}

    monkeypatch.setattr(
        "app.clients.reporting_client.ReportingClient.post_portfolio_review",
        _mock_post_review,
    )

    client = TestClient(app)
    response = client.post(
        "/api/v1/reports/DEMO_DPM_EUR_001/review",
        json={"as_of_date": "2026-02-24"},
    )
    assert response.status_code == 502
