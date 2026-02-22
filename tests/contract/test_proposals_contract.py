from app.contracts.proposals import (
    ProposalEnvelopeResponse,
    ProposalSimulateResponse,
    ProposalSubmitRequest,
)


def test_proposals_contract_shape() -> None:
    payload = ProposalSimulateResponse(
        correlation_id="corr_1",
        contract_version="v1",
        data={"status": "READY", "proposal_run_id": "pr_1"},
    )
    assert payload.data["status"] == "READY"


def test_proposal_envelope_contract_shape() -> None:
    payload = ProposalEnvelopeResponse(
        correlation_id="corr_2",
        contract_version="v1",
        data={"items": [{"proposal_id": "pp_1", "current_state": "DRAFT"}]},
    )
    assert payload.data["items"][0]["proposal_id"] == "pp_1"


def test_proposal_submit_request_contract_shape() -> None:
    payload = ProposalSubmitRequest(actor_id="advisor_1")
    assert payload.review_type == "RISK"
    assert payload.expected_state == "DRAFT"
