from fastapi.testclient import TestClient

from app.main import app


def test_health_live_and_ready_endpoints():
    client = TestClient(app)
    assert client.get("/health/live").json() == {"status": "live"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_unhandled_exception_handler_returns_problem_json():
    @app.get("/_test/error")
    async def _test_error():
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/_test/error")
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["title"] == "Internal Server Error"
    assert body["status"] == 500
    assert body["error_code"] == "INTERNAL_ERROR"
