from datetime import datetime

from pydantic import BaseModel, Field


class ReportingSnapshotResponse(BaseModel):
    correlation_id: str = Field(..., alias="correlationId")
    contract_version: str = Field(..., alias="contractVersion")
    source_service: str = Field(..., alias="sourceService")
    portfolio_id: str = Field(..., alias="portfolioId")
    as_of_date: str = Field(..., alias="asOfDate")
    generated_at: datetime = Field(..., alias="generatedAt")
    rows: list[dict]

    model_config = {"populate_by_name": True}


class ReportingSummaryResponse(BaseModel):
    correlation_id: str = Field(..., alias="correlationId")
    contract_version: str = Field(..., alias="contractVersion")
    source_service: str = Field(..., alias="sourceService")
    portfolio_id: str = Field(..., alias="portfolioId")
    as_of_date: str = Field(..., alias="asOfDate")
    data: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ReportingReviewResponse(BaseModel):
    correlation_id: str = Field(..., alias="correlationId")
    contract_version: str = Field(..., alias="contractVersion")
    source_service: str = Field(..., alias="sourceService")
    portfolio_id: str = Field(..., alias="portfolioId")
    as_of_date: str = Field(..., alias="asOfDate")
    data: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}
