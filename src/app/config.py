from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Advisor Experience API"
    contract_version: str = "v1"
    decisioning_service_base_url: str = Field(default="http://localhost:8000")
    upstream_timeout_seconds: float = Field(default=3.0)


settings = Settings()
