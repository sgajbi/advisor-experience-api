import pytest
from fastapi import HTTPException

from app.services.proposal_service import ProposalService


class _FakeDpmClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def transition_proposal(self, proposal_id: str, body: dict, correlation_id: str):
        self.calls.append(
            (
                "transition_proposal",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"current_state": "RISK_REVIEW"}

    async def record_approval(self, proposal_id: str, body: dict, correlation_id: str):
        self.calls.append(
            (
                "record_approval",
                {
                    "proposal_id": proposal_id,
                    "body": body,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"current_state": "AWAITING_CLIENT_CONSENT"}

    async def get_workflow_events(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_workflow_events",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"events": [{"event_type": "CREATED"}]}

    async def get_approvals(self, proposal_id: str, correlation_id: str):
        self.calls.append(
            (
                "get_approvals",
                {
                    "proposal_id": proposal_id,
                    "correlation_id": correlation_id,
                },
            )
        )
        return 200, {"approvals": [{"approval_type": "RISK"}]}


class _FakeDpmErrorClient(_FakeDpmClient):
    async def record_approval(self, proposal_id: str, body: dict, correlation_id: str):
        _ = proposal_id, body, correlation_id
        return 409, {"detail": "STATE_CONFLICT"}


@pytest.mark.asyncio
async def test_submit_proposal_maps_risk_transition() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    result = await service.submit_proposal(
        proposal_id="pp_1",
        actor_id="advisor_1",
        expected_state="DRAFT",
        review_type="RISK",
        reason={"comment": "submit"},
        related_version_no=1,
        correlation_id="corr_1",
    )

    assert result.data["current_state"] == "RISK_REVIEW"
    _, payload = client.calls[0]
    assert payload["body"]["event_type"] == "SUBMITTED_FOR_RISK_REVIEW"


@pytest.mark.asyncio
async def test_approve_compliance_maps_approval_payload() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    await service.approve_compliance(
        proposal_id="pp_1",
        actor_id="compliance_1",
        expected_state="COMPLIANCE_REVIEW",
        details={"comment": "ok"},
        related_version_no=2,
        correlation_id="corr_2",
    )

    _, payload = client.calls[0]
    assert payload["body"]["approval_type"] == "COMPLIANCE"
    assert payload["body"]["approved"] is True


@pytest.mark.asyncio
async def test_get_workflow_events_and_approvals_wrap_envelope() -> None:
    client = _FakeDpmClient()
    service = ProposalService(dpm_client=client)

    events = await service.get_workflow_events(proposal_id="pp_1", correlation_id="corr_3")
    approvals = await service.get_approvals(proposal_id="pp_1", correlation_id="corr_3")

    assert events.data["events"][0]["event_type"] == "CREATED"
    assert approvals.data["approvals"][0]["approval_type"] == "RISK"


@pytest.mark.asyncio
async def test_approval_upstream_error_passthrough() -> None:
    service = ProposalService(dpm_client=_FakeDpmErrorClient())

    try:
        await service.approve_risk(
            proposal_id="pp_1",
            actor_id="risk_1",
            expected_state="RISK_REVIEW",
            details={},
            related_version_no=None,
            correlation_id="corr_4",
        )
    except HTTPException as exc:
        assert exc.status_code == 409
        assert "STATE_CONFLICT" in str(exc.detail)
        return

    raise AssertionError("Expected HTTPException")
