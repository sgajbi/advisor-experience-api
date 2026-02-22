from pydantic import BaseModel, Field


class PortfolioInfo(BaseModel):
    portfolio_id: str
    client_id: str | None = None
    base_currency: str = "USD"
    booking_center_code: str | None = None


class OverviewInfo(BaseModel):
    market_value_base: float
    cash_weight_pct: float
    position_count: int


class PerformanceSnapshot(BaseModel):
    period: str
    return_pct: float | None = None
    benchmark_return_pct: float | None = None


class RebalanceSnapshot(BaseModel):
    status: str
    last_rebalance_run_id: str | None = None
    last_run_at_utc: str | None = None


class PartialFailure(BaseModel):
    source_service: str
    error_code: str
    detail: str


class WorkbenchOverviewResponse(BaseModel):
    correlation_id: str
    contract_version: str = "v1"
    as_of_date: str = Field(description="Business as-of date in YYYY-MM-DD")
    portfolio: PortfolioInfo
    overview: OverviewInfo
    performance_snapshot: PerformanceSnapshot | None = None
    rebalance_snapshot: RebalanceSnapshot | None = None
    warnings: list[str] = Field(default_factory=list)
    partial_failures: list[PartialFailure] = Field(default_factory=list)
