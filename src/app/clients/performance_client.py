import httpx


class PerformanceClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def get_performance_snapshot(self, portfolio_id: str, correlation_id: str) -> dict:
        # Placeholder shape; exact upstream mapping will be hardened in Sprint 2.
        url = f"{self._base_url}/performance/twr"
        headers = {"X-Correlation-Id": correlation_id}
        payload = {"portfolio_id": portfolio_id, "analyses": [{"period": "YTD"}]}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        return {
            "period": "YTD",
            "return_pct": data.get("return_pct"),
            "benchmark_return_pct": data.get("benchmark_return_pct"),
        }
