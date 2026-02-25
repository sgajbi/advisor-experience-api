import json

import httpx
import pytest

from app.clients.http_resilience import request_with_retry


class _FlakyAsyncClient:
    calls = 0

    def __init__(self, timeout: float):
        _ = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        _FlakyAsyncClient.calls += 1
        if _FlakyAsyncClient.calls == 1:
            raise httpx.TimeoutException("timed out")
        return httpx.Response(
            200,
            content=json.dumps({"ok": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            request=httpx.Request("GET", "http://test"),
        )


@pytest.mark.asyncio
async def test_request_with_retry_retries_on_timeout(monkeypatch):
    _FlakyAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _FlakyAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
    )

    assert status == 200
    assert payload == {"ok": True}
    assert _FlakyAsyncClient.calls == 2
