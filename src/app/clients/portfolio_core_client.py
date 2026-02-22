from datetime import date

import httpx


class PortfolioCoreClient:
    def __init__(self, base_url: str, timeout_seconds: float):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def get_portfolio_overview(self, portfolio_id: str, correlation_id: str) -> dict:
        url = f"{self._base_url}/portfolios/{portfolio_id}"
        headers = {"X-Correlation-Id": correlation_id}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        return {
            "as_of_date": str(date.today()),
            "portfolio": {
                "portfolio_id": payload.get("portfolio_id", portfolio_id),
                "client_id": payload.get("cif_id"),
                "base_currency": payload.get("base_currency", "USD"),
                "booking_center_code": payload.get("booking_center"),
            },
            "overview": {
                "market_value_base": float(payload.get("market_value_base", 0.0)),
                "cash_weight_pct": float(payload.get("cash_weight_pct", 0.0)),
                "position_count": int(payload.get("position_count", 0)),
            },
        }
