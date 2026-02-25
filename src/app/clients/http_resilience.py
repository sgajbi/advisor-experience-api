import asyncio
from typing import Any

import httpx


def _response_payload(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text}
    if isinstance(payload, dict):
        return payload
    return {"detail": payload}


async def request_with_retry(
    *,
    method: str,
    url: str,
    timeout_seconds: float,
    max_retries: int = 2,
    backoff_seconds: float = 0.2,
    retry_status_codes: set[int] | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    attempts = max_retries + 1
    for attempt in range(attempts):
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params, headers=headers)
                else:
                    response = await client.post(
                        url,
                        headers=headers,
                        json=json_body,
                        data=data,
                        files=files,
                    )

            should_retry_status = retry_status_codes and response.status_code in retry_status_codes
            if should_retry_status and attempt < max_retries:
                await asyncio.sleep(backoff_seconds * (2**attempt))
                continue
            return response.status_code, _response_payload(response)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            if attempt >= max_retries:
                return 503, {"detail": f"upstream communication failure: {exc.__class__.__name__}"}
            await asyncio.sleep(backoff_seconds * (2**attempt))

    return 503, {"detail": "upstream communication failure: exhausted retries"}
