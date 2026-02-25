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


class _RetryStatusAsyncClient:
    calls = 0

    def __init__(self, timeout: float):
        _ = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        _RetryStatusAsyncClient.calls += 1
        if _RetryStatusAsyncClient.calls == 1:
            return httpx.Response(
                503, json={"detail": "try-again"}, request=httpx.Request("GET", "http://test")
            )
        return httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", "http://test"))


class _NetworkErrorAsyncClient:
    def __init__(self, timeout: float):
        _ = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        _ = url, params, headers
        raise httpx.NetworkError("disconnected")


class _TextPayloadAsyncClient:
    def __init__(self, timeout: float):
        _ = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None, data=None, files=None):
        _ = url, headers, json, data, files
        return httpx.Response(
            500,
            text="plain-text-error",
            request=httpx.Request("POST", "http://test"),
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


@pytest.mark.asyncio
async def test_request_with_retry_retries_on_status_code(monkeypatch):
    _RetryStatusAsyncClient.calls = 0
    monkeypatch.setattr("httpx.AsyncClient", _RetryStatusAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=2,
        backoff_seconds=0.0,
        retry_status_codes={503},
    )

    assert status == 200
    assert payload == {"ok": True}
    assert _RetryStatusAsyncClient.calls == 2


@pytest.mark.asyncio
async def test_request_with_retry_returns_503_after_network_error(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _NetworkErrorAsyncClient)

    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
    )

    assert status == 503
    assert payload["detail"] == "upstream communication failure: NetworkError"


@pytest.mark.asyncio
async def test_request_with_retry_wraps_non_json_payload(monkeypatch):
    monkeypatch.setattr("httpx.AsyncClient", _TextPayloadAsyncClient)

    status, payload = await request_with_retry(
        method="POST",
        url="http://service/workbench",
        timeout_seconds=1.0,
        max_retries=0,
        backoff_seconds=0.0,
        json_body={"x": 1},
    )

    assert status == 500
    assert payload == {"detail": "plain-text-error"}


@pytest.mark.asyncio
async def test_request_with_retry_handles_negative_retry_configuration():
    status, payload = await request_with_retry(
        method="GET",
        url="http://service/health",
        timeout_seconds=1.0,
        max_retries=-1,
        backoff_seconds=0.0,
    )

    assert status == 503
    assert payload == {"detail": "upstream communication failure: exhausted retries"}
