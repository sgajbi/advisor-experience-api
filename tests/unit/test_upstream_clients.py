import json

import httpx
import pytest

from app.clients.dpm_client import DpmClient
from app.clients.pa_client import PaClient
from app.clients.pas_client import PasClient
from app.clients.pas_ingestion_client import PasIngestionClient
from app.clients.reporting_client import ReportingClient


class _FakeAsyncClient:
    responses: list[httpx.Response] = []
    calls: list[dict] = []

    def __init__(self, timeout: float):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None, headers=None):
        self.calls.append(
            {"method": "GET", "url": url, "params": params or {}, "headers": headers or {}}
        )
        return self._next_response("GET", url)

    async def post(self, url, json=None, data=None, files=None, headers=None):
        self.calls.append(
            {
                "method": "POST",
                "url": url,
                "json": json,
                "data": data,
                "files": files,
                "headers": headers or {},
            }
        )
        return self._next_response("POST", url)

    @classmethod
    def _next_response(cls, method: str, url: str) -> httpx.Response:
        if not cls.responses:
            raise AssertionError("No queued response available.")
        response = cls.responses.pop(0)
        if response.request is None:
            response.request = httpx.Request(method, url)  # type: ignore[misc]
        return response

    @classmethod
    def queue_json(cls, status_code: int, payload: dict | list):
        cls.responses.append(
            httpx.Response(
                status_code=status_code,
                content=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                request=httpx.Request("GET", "http://test"),
            )
        )

    @classmethod
    def queue_text(cls, status_code: int, text: str):
        cls.responses.append(
            httpx.Response(
                status_code=status_code,
                content=text.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                request=httpx.Request("GET", "http://test"),
            )
        )


@pytest.fixture(autouse=True)
def _patch_async_client(monkeypatch):
    _FakeAsyncClient.responses = []
    _FakeAsyncClient.calls = []
    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)


@pytest.mark.asyncio
async def test_pa_client_calls_and_payload_handling():
    client = PaClient(base_url="http://pa", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "pa"})
    _FakeAsyncClient.queue_json(200, {"resultsByPeriod": {"YTD": {"net_cumulative_return": 2.1}}})
    _FakeAsyncClient.queue_json(
        200,
        {
            "allocationBuckets": [{"bucketKey": "EQUITY"}],
            "topChanges": [],
            "riskProxy": {},
        },
    )

    status_one, payload_one = await client.get_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-1",
    )
    status_two, payload_two = await client.get_pas_input_twr(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        periods=["YTD"],
        consumer_system="BFF",
        correlation_id="corr-1",
    )
    status_three, payload_three = await client.get_workbench_analytics(
        payload={"portfolioId": "P1", "groupBy": "ASSET_CLASS"},
        correlation_id="corr-1",
    )

    assert status_one == 200
    assert payload_one["sourceService"] == "pa"
    assert status_two == 200
    assert payload_two["resultsByPeriod"]["YTD"]["net_cumulative_return"] == 2.1
    assert status_three == 200
    assert payload_three["allocationBuckets"][0]["bucketKey"] == "EQUITY"
    assert _FakeAsyncClient.calls[0]["url"] == "http://pa/integration/capabilities"
    assert _FakeAsyncClient.calls[1]["url"] == "http://pa/performance/twr/pas-input"
    assert _FakeAsyncClient.calls[2]["url"] == "http://pa/analytics/workbench"


@pytest.mark.asyncio
async def test_pa_client_non_json_and_non_dict_payload_handling():
    client = PaClient(base_url="http://pa", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(503, "pa unavailable")
    _FakeAsyncClient.queue_json(200, ["analytics"])

    status_one, payload_one = await client.get_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-1",
    )
    status_two, payload_two = await client.get_workbench_analytics(
        payload={"portfolioId": "P1"},
        correlation_id="corr-1",
    )

    assert status_one == 503
    assert payload_one["detail"] == "pa unavailable"
    assert status_two == 200
    assert payload_two["detail"] == ["analytics"]


@pytest.mark.asyncio
async def test_pas_client_endpoints_and_non_json_response_handling():
    client = PasClient(base_url="http://pas", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"items": [{"portfolio_id": "P1"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"instrument_id": "AAPL"}]})
    _FakeAsyncClient.queue_json(200, {"items": [{"value": "USD"}]})
    _FakeAsyncClient.queue_json(201, {"session": {"session_id": "S1", "version": 1}})
    _FakeAsyncClient.queue_json(200, {"version": 2})
    _FakeAsyncClient.queue_json(200, {"positions": []})
    _FakeAsyncClient.queue_text(503, "service unavailable")

    assert (await client.get_portfolio_lookups(correlation_id="corr-2"))[0] == 200
    assert (await client.get_instrument_lookups(limit=25, correlation_id="corr-2"))[0] == 200
    assert (await client.get_currency_lookups(correlation_id="corr-2"))[0] == 200
    assert (
        await client.create_simulation_session(
            portfolio_id="P1",
            created_by="advisor",
            ttl_hours=4,
            correlation_id="corr-2",
        )
    )[0] == 201
    assert (
        await client.add_simulation_changes(
            session_id="S1",
            changes=[{"kind": "trade"}],
            correlation_id="corr-2",
        )
    )[0] == 200
    projected_positions_status, _ = await client.get_projected_positions(
        session_id="S1",
        correlation_id="corr-2",
    )
    assert projected_positions_status == 200
    status_summary, payload_summary = await client.get_projected_summary(
        session_id="S1", correlation_id="corr-2"
    )
    assert status_summary == 503
    assert payload_summary["detail"] == "service unavailable"


@pytest.mark.asyncio
async def test_pas_client_core_endpoints():
    client = PasClient(base_url="http://pas", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "pas"})
    _FakeAsyncClient.queue_json(200, {"allowedSections": ["OVERVIEW"]})
    _FakeAsyncClient.queue_json(200, {"items": []})
    _FakeAsyncClient.queue_json(200, {"snapshot": {"overview": {}}})
    _FakeAsyncClient.queue_json(200, {"items": [{"instrument_id": "AAPL"}]})

    assert (
        await client.get_capabilities(
            consumer_system="BFF", tenant_id="default", correlation_id="corr-3"
        )
    )[0] == 200
    assert (
        await client.get_effective_policy(
            consumer_system="BFF", tenant_id="default", correlation_id="corr-3"
        )
    )[0] == 200
    assert (await client.list_portfolios(correlation_id="corr-3"))[0] == 200
    assert (
        await client.get_core_snapshot(
            portfolio_id="P1",
            as_of_date="2026-02-24",
            include_sections=["OVERVIEW"],
            consumer_system="BFF",
            correlation_id="corr-3",
        )
    )[0] == 200
    assert (await client.list_instruments(limit=10, correlation_id="corr-3"))[0] == 200


@pytest.mark.asyncio
async def test_pas_client_non_dict_payload_branch():
    client = PasClient(base_url="http://pas", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, ["not-dict"])
    status_code, payload = await client.list_portfolios(correlation_id="corr-3")
    assert status_code == 200
    assert payload["detail"] == ["not-dict"]


@pytest.mark.asyncio
async def test_pas_ingestion_client_upload_paths():
    client = PasIngestionClient(base_url="http://pas-ingest", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(202, {"status": "accepted"})
    _FakeAsyncClient.queue_json(200, {"columns": ["portfolio_id"]})
    _FakeAsyncClient.queue_json(201, {"importedRows": 10})

    status_ingest, _ = await client.ingest_portfolio_bundle(
        body={"portfolio": {"portfolio_id": "P1"}},
        correlation_id="corr-4",
    )
    status_preview, _ = await client.preview_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        sample_size=5,
        correlation_id="corr-4",
    )
    status_commit, _ = await client.commit_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        allow_partial=False,
        correlation_id="corr-4",
    )

    assert status_ingest == 202
    assert status_preview == 200
    assert status_commit == 201
    assert _FakeAsyncClient.calls[1]["url"] == "http://pas-ingest/ingest/uploads/preview"
    assert _FakeAsyncClient.calls[2]["url"] == "http://pas-ingest/ingest/uploads/commit"


@pytest.mark.asyncio
async def test_pas_ingestion_client_non_dict_and_text_payload_handling():
    client = PasIngestionClient(base_url="http://pas-ingest", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, [{"preview": "row"}])
    _FakeAsyncClient.queue_text(503, "ingestion unavailable")

    preview_status, preview_payload = await client.preview_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        sample_size=1,
        correlation_id="corr-4",
    )
    commit_status, commit_payload = await client.commit_upload(
        entity_type="transactions",
        filename="tx.csv",
        content=b"id,qty\n1,10",
        allow_partial=True,
        correlation_id="corr-4",
    )
    assert preview_status == 200
    assert preview_payload["detail"] == [{"preview": "row"}]
    assert commit_status == 503
    assert commit_payload["detail"] == "ingestion unavailable"
    assert _FakeAsyncClient.calls[1]["data"]["allowPartial"] == "true"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method_name", "kwargs", "expected_url"),
    [
        (
            "simulate_proposal",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/rebalance/proposals/simulate",
        ),
        (
            "create_proposal",
            {
                "body": {"portfolio_id": "P1"},
                "idempotency_key": "idem-2",
                "correlation_id": "corr-5",
            },
            "http://dpm/rebalance/proposals",
        ),
        (
            "list_proposals",
            {"params": {"portfolio_id": "P1", "status": None}, "correlation_id": "corr-5"},
            "http://dpm/rebalance/proposals",
        ),
        (
            "list_runs",
            {"params": {"portfolio_id": "P1", "status": None}, "correlation_id": "corr-5"},
            "http://dpm/rebalance/runs",
        ),
        (
            "get_proposal",
            {"proposal_id": "PR-1", "include_evidence": True, "correlation_id": "corr-5"},
            "http://dpm/rebalance/proposals/PR-1",
        ),
        (
            "get_proposal_version",
            {
                "proposal_id": "PR-1",
                "version_no": 2,
                "include_evidence": False,
                "correlation_id": "corr-5",
            },
            "http://dpm/rebalance/proposals/PR-1/versions/2",
        ),
        (
            "create_proposal_version",
            {
                "proposal_id": "PR-1",
                "body": {"changes": []},
                "idempotency_key": "idem-3",
                "correlation_id": "corr-5",
            },
            "http://dpm/rebalance/proposals/PR-1/versions",
        ),
        (
            "transition_proposal",
            {
                "proposal_id": "PR-1",
                "body": {"event": "submit"},
                "idempotency_key": "idem-transition-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/rebalance/proposals/PR-1/transitions",
        ),
        (
            "record_approval",
            {
                "proposal_id": "PR-1",
                "body": {"decision": "approve"},
                "idempotency_key": "idem-approval-1",
                "correlation_id": "corr-5",
            },
            "http://dpm/rebalance/proposals/PR-1/approvals",
        ),
        (
            "get_workflow_events",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://dpm/rebalance/proposals/PR-1/workflow-events",
        ),
        (
            "get_approvals",
            {"proposal_id": "PR-1", "correlation_id": "corr-5"},
            "http://dpm/rebalance/proposals/PR-1/approvals",
        ),
        (
            "get_capabilities",
            {"consumer_system": "BFF", "tenant_id": "default", "correlation_id": "corr-5"},
            "http://dpm/integration/capabilities",
        ),
    ],
)
async def test_dpm_client_all_routes(method_name, kwargs, expected_url):
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"ok": True})

    method = getattr(client, method_name)
    status_code, payload = await method(**kwargs)
    assert status_code == 200
    assert payload["ok"] is True
    assert _FakeAsyncClient.calls[0]["url"] == expected_url
    methods_with_idempotency = {
        "simulate_proposal",
        "create_proposal",
        "create_proposal_version",
        "transition_proposal",
        "record_approval",
    }
    if method_name in methods_with_idempotency:
        assert _FakeAsyncClient.calls[0]["headers"]["Idempotency-Key"] == kwargs["idempotency_key"]


@pytest.mark.asyncio
async def test_dpm_client_non_json_and_non_dict_payload_handling():
    client = DpmClient(base_url="http://dpm", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(502, "dpm unavailable")
    _FakeAsyncClient.queue_json(200, ["not-dict"])

    status_one, payload_one = await client.get_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-5",
    )
    status_two, payload_two = await client.list_runs(
        params={"portfolio_id": "P1"},
        correlation_id="corr-5",
    )
    assert status_one == 502
    assert payload_one["detail"] == "dpm unavailable"
    assert status_two == 200
    assert payload_two["detail"] == ["not-dict"]


@pytest.mark.asyncio
async def test_reporting_client_handles_non_dict_payload():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, [{"metric": "market_value_base"}])
    status_code, payload = await client.get_portfolio_snapshot(
        portfolio_id="P1",
        as_of_date="2026-02-24",
        correlation_id="corr-6",
    )
    assert status_code == 200
    assert payload["detail"] == [{"metric": "market_value_base"}]


@pytest.mark.asyncio
async def test_reporting_client_summary_and_review_routes():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_json(200, {"sourceService": "lotus-report"})
    _FakeAsyncClient.queue_json(200, {"scope": {"portfolio_id": "P1"}})
    _FakeAsyncClient.queue_json(200, {"portfolio_id": "P1", "overview": {}})

    capabilities_status, capabilities_payload = await client.get_capabilities(
        consumer_system="BFF",
        tenant_id="default",
        correlation_id="corr-7",
    )
    summary_status, summary_payload = await client.post_portfolio_summary(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24", "sections": ["WEALTH"]},
        correlation_id="corr-7",
    )
    review_status, review_payload = await client.post_portfolio_review(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24", "sections": ["OVERVIEW"]},
        correlation_id="corr-7",
    )

    assert capabilities_status == 200
    assert capabilities_payload["sourceService"] == "lotus-report"
    assert summary_status == 200
    assert summary_payload["scope"]["portfolio_id"] == "P1"
    assert review_status == 200
    assert review_payload["portfolio_id"] == "P1"
    assert _FakeAsyncClient.calls[0]["url"] == "http://ras/integration/capabilities"
    assert _FakeAsyncClient.calls[1]["url"] == "http://ras/reports/portfolios/P1/summary"
    assert _FakeAsyncClient.calls[2]["url"] == "http://ras/reports/portfolios/P1/review"


@pytest.mark.asyncio
async def test_reporting_client_summary_review_non_json_payloads():
    client = ReportingClient(base_url="http://ras", timeout_seconds=2.0)
    _FakeAsyncClient.queue_text(502, "summary failure")
    _FakeAsyncClient.queue_json(200, ["review-item"])

    summary_status, summary_payload = await client.post_portfolio_summary(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24"},
        correlation_id="corr-7",
    )
    review_status, review_payload = await client.post_portfolio_review(
        portfolio_id="P1",
        payload={"as_of_date": "2026-02-24"},
        correlation_id="corr-7",
    )
    assert summary_status == 502
    assert summary_payload["detail"] == "summary failure"
    assert review_status == 200
    assert review_payload["detail"] == ["review-item"]
