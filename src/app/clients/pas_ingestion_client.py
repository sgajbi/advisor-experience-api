from typing import Any

import httpx


class PasIngestionClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def ingest_portfolio_bundle(
        self,
        body: dict[str, Any],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}/ingest/portfolio-bundle"
        headers = {"X-Correlation-Id": correlation_id}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body, headers=headers)
            return response.status_code, self._response_payload(response)

    async def preview_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        sample_size: int,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._upload(
            "/ingest/uploads/preview",
            entity_type=entity_type,
            filename=filename,
            content=content,
            extra_data={"sampleSize": str(sample_size)},
            correlation_id=correlation_id,
        )

    async def commit_upload(
        self,
        entity_type: str,
        filename: str,
        content: bytes,
        allow_partial: bool,
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return await self._upload(
            "/ingest/uploads/commit",
            entity_type=entity_type,
            filename=filename,
            content=content,
            extra_data={"allowPartial": "true" if allow_partial else "false"},
            correlation_id=correlation_id,
        )

    async def _upload(
        self,
        path: str,
        entity_type: str,
        filename: str,
        content: bytes,
        extra_data: dict[str, str],
        correlation_id: str,
    ) -> tuple[int, dict[str, Any]]:
        url = f"{self._base_url}{path}"
        headers = {"X-Correlation-Id": correlation_id}
        form_data = {"entityType": entity_type, **extra_data}
        files = {"file": (filename, content)}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, data=form_data, files=files, headers=headers)
            return response.status_code, self._response_payload(response)

    def _response_payload(self, response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text}
        if isinstance(payload, dict):
            return payload
        return {"detail": payload}
