from typing import Any

import httpx

from app.middleware.correlation import propagation_headers


class ReportingClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def get_portfolio_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/aggregations/portfolios/{portfolio_id}"
        params = {"asOfDate": as_of_date, "live": "true"}
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            return response.status_code, self._response_payload(response)

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/capabilities"
        params = {"consumerSystem": consumer_system, "tenantId": tenant_id}
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            return response.status_code, self._response_payload(response)

    async def post_portfolio_summary(
        self,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/portfolios/{portfolio_id}/summary"
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code, self._response_payload(response)

    async def post_portfolio_review(
        self,
        portfolio_id: str,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/reports/portfolios/{portfolio_id}/review"
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code, self._response_payload(response)

    def _response_payload(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}
        if isinstance(payload, dict):
            return payload
        return {"detail": payload}
