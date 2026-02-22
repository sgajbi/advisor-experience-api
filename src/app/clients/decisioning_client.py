import httpx


class DecisioningClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def get_rebalance_snapshot(self, portfolio_id: str, correlation_id: str) -> dict:
        # Placeholder endpoint usage; can be replaced with supportability lookup endpoint contract.
        url = f"{self._base_url}/rebalance/runs"
        headers = {"X-Correlation-Id": correlation_id}
        params = {"portfolio_id": portfolio_id, "limit": 1}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
        items = data.get("items", [])
        if not items:
            return {"status": "NO_RUN", "last_rebalance_run_id": None, "last_run_at_utc": None}
        latest = items[0]
        return {
            "status": latest.get("status", "UNKNOWN"),
            "last_rebalance_run_id": latest.get("rebalance_run_id"),
            "last_run_at_utc": latest.get("created_at"),
        }
