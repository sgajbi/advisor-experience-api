from typing import Any

import httpx

from app.middleware.correlation import propagation_headers


class PasClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

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

    async def get_effective_policy(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/policy/effective"
        params = {"consumerSystem": consumer_system, "tenantId": tenant_id}
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            return response.status_code, self._response_payload(response)

    async def list_portfolios(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/portfolios"
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=headers)
            return response.status_code, self._response_payload(response)

    async def get_core_snapshot(
        self,
        portfolio_id: str,
        as_of_date: str,
        include_sections: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/portfolios/{portfolio_id}/core-snapshot"
        headers = propagation_headers(correlation_id)
        payload = {
            "asOfDate": as_of_date,
            "includeSections": include_sections,
            "consumerSystem": consumer_system,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code, self._response_payload(response)

    async def list_instruments(
        self,
        limit: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/instruments"
        headers = propagation_headers(correlation_id)
        params = {"skip": 0, "limit": limit}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            return response.status_code, self._response_payload(response)

    async def get_portfolio_lookups(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_lookup(
            path="/lookups/portfolios", params={}, correlation_id=correlation_id
        )

    async def get_instrument_lookups(
        self,
        limit: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_lookup(
            path="/lookups/instruments",
            params={"limit": limit},
            correlation_id=correlation_id,
        )

    async def get_currency_lookups(
        self,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get_lookup(
            path="/lookups/currencies", params={}, correlation_id=correlation_id
        )

    async def _get_lookup(
        self,
        path: str,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            return response.status_code, self._response_payload(response)

    async def create_simulation_session(
        self,
        portfolio_id: str,
        created_by: str | None,
        ttl_hours: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/simulation-sessions"
        headers = propagation_headers(correlation_id)
        payload = {
            "portfolio_id": portfolio_id,
            "created_by": created_by,
            "ttl_hours": ttl_hours,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code, self._response_payload(response)

    async def add_simulation_changes(
        self,
        session_id: str,
        changes: list[dict[str, Any]],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/simulation-sessions/{session_id}/changes"
        headers = propagation_headers(correlation_id)
        payload = {"changes": changes}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            return response.status_code, self._response_payload(response)

    async def get_projected_positions(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/simulation-sessions/{session_id}/projected-positions"
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=headers)
            return response.status_code, self._response_payload(response)

    async def get_projected_summary(
        self,
        session_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/simulation-sessions/{session_id}/projected-summary"
        headers = propagation_headers(correlation_id)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, headers=headers)
            return response.status_code, self._response_payload(response)

    def _response_payload(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}
        if isinstance(payload, dict):
            return payload
        return {"detail": payload}
