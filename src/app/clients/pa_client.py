from typing import Any

from app.clients.http_resilience import request_with_retry
from app.middleware.correlation import propagation_headers


class PaClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_retries: int = 2,
        retry_backoff_seconds: float = 0.2,
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/integration/capabilities"
        params = {"consumerSystem": consumer_system, "tenantId": tenant_id}
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )

    async def get_pas_input_twr(
        self,
        portfolio_id: str,
        as_of_date: str,
        periods: list[str],
        consumer_system: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/performance/twr/pas-input"
        headers = propagation_headers(correlation_id)
        payload = {
            "portfolioId": portfolio_id,
            "asOfDate": as_of_date,
            "periods": periods,
            "consumerSystem": consumer_system,
        }
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_workbench_analytics(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/analytics/workbench"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )

    async def get_workbench_risk_proxy(
        self,
        payload: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/analytics/workbench/risk-proxy"
        headers = propagation_headers(correlation_id)
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=payload,
            headers=headers,
        )
