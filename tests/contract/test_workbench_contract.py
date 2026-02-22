from app.contracts.workbench import WorkbenchOverviewResponse


def test_workbench_contract_minimal_shape():
    payload = WorkbenchOverviewResponse(
        correlation_id="corr_abc",
        contract_version="v1",
        as_of_date="2026-02-22",
        portfolio={
            "portfolio_id": "PF_1",
            "client_id": "C_1",
            "base_currency": "USD",
            "booking_center_code": "SG",
        },
        overview={"market_value_base": 1.0, "cash_weight_pct": 0.1, "position_count": 1},
        warnings=[],
        partial_failures=[],
    )
    assert payload.portfolio.portfolio_id == "PF_1"
