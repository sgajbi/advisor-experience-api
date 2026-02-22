from typing import Any

import httpx


class DpmClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/rebalance/proposals/simulate"
        headers = {
            "Idempotency-Key": idempotency_key,
            "X-Correlation-Id": correlation_id,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body, headers=headers)
            payload = response.json()
            return response.status_code, payload
