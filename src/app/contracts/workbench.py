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
