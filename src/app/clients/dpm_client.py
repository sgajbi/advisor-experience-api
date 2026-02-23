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
        return await self._post(
            "/rebalance/proposals/simulate",
            body=body,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Correlation-Id": correlation_id,
            },
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
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Correlation-Id": correlation_id,
            },
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
            headers={"X-Correlation-Id": correlation_id},
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
            headers={"X-Correlation-Id": correlation_id},
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
            headers={"X-Correlation-Id": correlation_id},
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
            headers={"X-Correlation-Id": correlation_id},
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
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Correlation-Id": correlation_id,
            },
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
            headers={"X-Correlation-Id": correlation_id},
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
            headers={"X-Correlation-Id": correlation_id},
        )

    async def get_workflow_events(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/rebalance/proposals/{proposal_id}/workflow-events",
            params={},
            headers={"X-Correlation-Id": correlation_id},
        )

    async def get_approvals(
        self,
        proposal_id: str,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._get(
            f"/rebalance/proposals/{proposal_id}/approvals",
            params={},
            headers={"X-Correlation-Id": correlation_id},
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
            headers={"X-Correlation-Id": correlation_id},
        )

    async def _post(
        self,
        path: str,
        body: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body, headers=headers)
            return response.status_code, self._response_payload(response)

    async def _get(
        self,
        path: str,
        params: dict[str, Any],
        headers: dict[str, str],
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            return response.status_code, self._response_payload(response)

    def _response_payload(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}
        if isinstance(payload, dict):
            return payload
        return {"detail": payload}
