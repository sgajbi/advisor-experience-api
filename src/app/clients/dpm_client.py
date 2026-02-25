from typing import Any

from app.clients.http_resilience import request_with_retry
from app.middleware.correlation import propagation_headers


class DpmClient:
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

    async def simulate_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/rebalance/proposals/simulate",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
        )

    async def create_proposal(
        self,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            "/rebalance/proposals",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
        )

    async def list_proposals(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/rebalance/proposals",
            params=cleaned_params,
            headers=self._headers(correlation_id),
        )

    async def list_runs(
        self,
        params: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        cleaned_params = {key: value for key, value in params.items() if value is not None}
        return await self._get(
            "/rebalance/runs",
            params=cleaned_params,
            headers=self._headers(correlation_id),
        )

    async def get_proposal(
        self,
        proposal_id: str,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/rebalance/proposals/{proposal_id}",
            params={"include_evidence": str(include_evidence).lower()},
            headers=self._headers(correlation_id),
        )

    async def get_proposal_version(
        self,
        proposal_id: str,
        version_no: int,
        include_evidence: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/rebalance/proposals/{proposal_id}/versions/{version_no}",
            params={"include_evidence": str(include_evidence).lower()},
            headers=self._headers(correlation_id),
        )

    async def create_proposal_version(
        self,
        proposal_id: str,
        body: dict[str, Any],
        idempotency_key: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/rebalance/proposals/{proposal_id}/versions",
            body=body,
            headers=self._headers(correlation_id, {"Idempotency-Key": idempotency_key}),
        )

    async def transition_proposal(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/rebalance/proposals/{proposal_id}/transitions",
            body=body,
            headers=self._headers(correlation_id),
        )

    async def record_approval(
        self,
        proposal_id: str,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._post(
            f"/rebalance/proposals/{proposal_id}/approvals",
            body=body,
            headers=self._headers(correlation_id),
        )

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/rebalance/proposals/{proposal_id}/workflow-events",
            params={},
            headers=self._headers(correlation_id),
        )

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/rebalance/proposals/{proposal_id}/approvals",
            params={},
            headers=self._headers(correlation_id),
        )

    async def get_capabilities(
        self,
        consumer_system: str,
        tenant_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            "/integration/capabilities",
            params={"consumerSystem": consumer_system, "tenantId": tenant_id},
            headers=self._headers(correlation_id),
        )

    def _headers(
        self,
        correlation_id: str,
        extras: dict[str, str] | None = None,
    ) -> dict[str, str]:
        headers = propagation_headers(correlation_id)
        if extras:
            headers.update(extras)
        return headers

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        return await request_with_retry(
            method="POST",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            json_body=body,
            headers=headers,
        )

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        return await request_with_retry(
            method="GET",
            url=url,
            timeout_seconds=self._timeout,
            max_retries=self._max_retries,
            backoff_seconds=self._retry_backoff_seconds,
            params=params,
            headers=headers,
        )
