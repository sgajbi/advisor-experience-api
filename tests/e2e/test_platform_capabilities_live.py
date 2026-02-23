import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

BFF_URL = "http://127.0.0.1:8100/api/v1/platform/capabilities"


def _fetch() -> dict:
    query = urllib.parse.urlencode({"consumerSystem": "BFF", "tenantId": "default"})
    with urllib.request.urlopen(f"{BFF_URL}?{query}", timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _assert_payload(payload: dict) -> None:
    if payload.get("data", {}).get("partialFailure"):
        raise AssertionError(f"Expected no partial failure, got: {payload}")

    sources = payload.get("data", {}).get("sources", {})
    expected = {"pas", "pa", "dpm"}
    if set(sources.keys()) != expected:
        raise AssertionError(f"Expected sources {expected}, got {set(sources.keys())}")

    passthrough = {
        "pas": "portfolio-analytics-system",
        "pa": "performance-analytics",
        "dpm": "dpm-rebalance-engine",
    }
    for key, source_name in passthrough.items():
        actual = sources[key].get("sourceService")
        if actual != source_name:
            raise AssertionError(f"Expected {key}.sourceService={source_name}, got {actual}")


def main() -> None:
    deadline = time.time() + 120
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            payload = _fetch()
            _assert_payload(payload)
            print("E2E platform capabilities assertion passed")
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

    raise SystemExit(f"E2E validation failed: {last_error}")


if __name__ == "__main__":
    main()
