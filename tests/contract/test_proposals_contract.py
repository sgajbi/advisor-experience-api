from app.contracts.proposals import ProposalSimulateResponse


def test_proposals_contract_shape() -> None:
    payload = ProposalSimulateResponse(
        correlation_id="corr_1",
        contract_version="v1",
        data={"status": "READY", "proposal_run_id": "pr_1"},
    )
    assert payload.data["status"] == "READY"
