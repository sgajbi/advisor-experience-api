from fastapi.testclient import TestClient

from app.main import app
from app.middleware.correlation import resolve_trace_id


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


def test_trace_id_falls_back_to_x_trace_id_when_traceparent_invalid():
    client = TestClient(app)
    response = client.get(
        "/health",
        headers={
            "traceparent": "invalid-traceparent",
            "X-Trace-Id": "trace-from-header",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id") == "trace-from-header"


def test_trace_id_generated_when_missing():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Trace-Id")


def test_resolve_trace_id_uses_generated_value_for_invalid_traceparent_without_fallback():
    class _FakeHeaders:
        def __init__(self, values: dict[str, str]):
            self._values = values

        def get(self, key: str):
            return self._values.get(key)

    class _FakeRequest:
        headers = _FakeHeaders({"traceparent": "invalid"})

    resolved = resolve_trace_id(_FakeRequest())
    assert len(resolved) == 32
