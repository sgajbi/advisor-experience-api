from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Advisor Experience API"
    contract_version: str = "v1"
    decisioning_service_base_url: str = Field(default="http://localhost:8000")
    portfolio_data_platform_base_url: str = Field(default="http://localhost:8201")
    portfolio_data_ingestion_base_url: str = Field(default="http://localhost:8200")
    performance_analytics_base_url: str = Field(default="http://localhost:8002")
    risk_analytics_base_url: str = Field(default="http://localhost:8130")
    reporting_aggregation_base_url: str = Field(default="http://localhost:8300")
    management_service_base_url: str = Field(default="http://localhost:8140")
    risk_split_enabled: bool = Field(default=True)
    manage_split_enabled: bool = Field(default=True)
    upstream_timeout_seconds: float = Field(default=3.0)
    upstream_max_retries: int = Field(default=2)
    upstream_retry_backoff_seconds: float = Field(default=0.2)


settings = Settings()
