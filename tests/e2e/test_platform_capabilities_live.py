import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

BFF_URL = "http://127.0.0.1:8100/api/v1/platform/capabilities"
HEALTH_READY_URL = "http://127.0.0.1:8100/health/ready"


def _fetch() -> dict:
    query = urllib.parse.urlencode({"consumerSystem": "BFF", "tenantId": "default"})
    with urllib.request.urlopen(f"{BFF_URL}?{query}", timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _assert_payload(payload: dict) -> None:
    if payload.get("data", {}).get("partialFailure"):
        raise AssertionError(f"Expected no partial failure, got: {payload}")

    sources = payload.get("data", {}).get("sources", {})
    expected = {"pas", "pa", "dpm", "ras"}
    if set(sources.keys()) != expected:
        raise AssertionError(f"Expected sources {expected}, got {set(sources.keys())}")

    passthrough = {
        "pas": "lotus-core",
        "pa": "performance-analytics",
        "dpm": "lotus-advise",
        "ras": "lotus-report",
    }
    for key, source_name in passthrough.items():
        actual = sources[key].get("sourceService")
        if actual != source_name:
            raise AssertionError(f"Expected {key}.sourceService={source_name}, got {actual}")


def test_platform_capabilities_live_upstreams() -> None:
    deadline = time.time() + 120
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            payload = _fetch()
            _assert_payload(payload)
            return
        except (
            AssertionError,
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            ConnectionResetError,
            ConnectionRefusedError,
            socket.timeout,
            socket.error,
        ) as exc:
            last_error = exc
            time.sleep(2)

    raise AssertionError(f"E2E validation failed: {last_error}")


def test_platform_health_ready_live() -> None:
    deadline = time.time() + 60
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_READY_URL, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if payload.get("status") == "ready":
                return
            raise AssertionError(f"Unexpected health payload: {payload}")
        except (
            AssertionError,
            urllib.error.URLError,
            TimeoutError,
            ValueError,
            ConnectionResetError,
            ConnectionRefusedError,
            socket.timeout,
            socket.error,
        ) as exc:
            last_error = exc
            time.sleep(2)

    raise AssertionError(f"Health readiness validation failed: {last_error}")


if __name__ == "__main__":
    test_platform_capabilities_live_upstreams()

