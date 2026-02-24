from fastapi.testclient import TestClient

from app.main import app


def test_correlation_header_is_returned():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-Id": "corr_test_1"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == "corr_test_1"
    assert response.headers.get("X-Request-Id")
    assert response.headers.get("X-Trace-Id")


def test_legacy_correlation_header_alias_is_supported():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-ID": "corr_test_legacy"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == "corr_test_legacy"
