from fastapi.testclient import TestClient

from app.main import app


def test_correlation_header_is_returned():
    client = TestClient(app)
    response = client.get("/health", headers={"X-Correlation-Id": "corr_test_1"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-Id") == "corr_test_1"
