from pydantic import BaseModel, Field


class WorkbenchPortfolioSummary(BaseModel):
    portfolio_id: str
    client_id: str | None = None
    base_currency: str
    booking_center_code: str | None = None


class WorkbenchOverviewSummary(BaseModel):
    market_value_base: float
    cash_weight_pct: float
    position_count: int


class WorkbenchPerformanceSnapshot(BaseModel):
    period: str
    return_pct: float | None = None
    benchmark_return_pct: float | None = None


class WorkbenchRebalanceSnapshot(BaseModel):
    status: str
    last_rebalance_run_id: str | None = None
    last_run_at_utc: str | None = None


class WorkbenchPartialFailure(BaseModel):
    source_service: str
    error_code: str
    detail: str


class WorkbenchOverviewResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    performance_snapshot: WorkbenchPerformanceSnapshot | None = None
    rebalance_snapshot: WorkbenchRebalanceSnapshot | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class WorkbenchPositionView(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    quantity: float


class WorkbenchProjectedPositionView(BaseModel):
    security_id: str
    instrument_name: str
    asset_class: str | None = None
    baseline_quantity: float
    proposed_quantity: float
    delta_quantity: float


class WorkbenchProjectedSummary(BaseModel):
    total_baseline_positions: int
    total_proposed_positions: int
    net_delta_quantity: float


class WorkbenchPortfolio360Response(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    as_of_date: str
    portfolio: WorkbenchPortfolioSummary
    overview: WorkbenchOverviewSummary
    current_positions: list[WorkbenchPositionView] = Field(default_factory=list)
    projected_positions: list[WorkbenchProjectedPositionView] = Field(default_factory=list)
    projected_summary: WorkbenchProjectedSummary | None = None
    active_session_id: str | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)


class WorkbenchSandboxSessionCreateRequest(BaseModel):
    created_by: str | None = None
    ttl_hours: int = Field(default=24, ge=1, le=168)


class WorkbenchSandboxChangeInput(BaseModel):
    security_id: str
    transaction_type: str
    quantity: float | None = None
    price: float | None = None
    amount: float | None = None
    currency: str | None = None
    effective_date: str | None = None
    metadata: dict[str, str | int | float | bool] | None = None


class WorkbenchSandboxApplyChangesRequest(BaseModel):
    changes: list[WorkbenchSandboxChangeInput] = Field(default_factory=list)
    evaluate_policy: bool = False


class WorkbenchPolicyFeedback(BaseModel):
    status: str
    detail: str | None = None
    raw: dict | None = None


class WorkbenchSandboxStateResponse(BaseModel):
    correlation_id: str
    contract_version: str = Field(default="v1")
    portfolio_id: str
    session_id: str
    session_version: int
    projected_positions: list[WorkbenchProjectedPositionView] = Field(default_factory=list)
    projected_summary: WorkbenchProjectedSummary
    policy_feedback: WorkbenchPolicyFeedback | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[WorkbenchPartialFailure] = Field(default_factory=list)
