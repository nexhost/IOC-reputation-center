from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="IOC Reputation Center", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    secret_key: str = Field(default="change-this-local-secret", alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./ioc_reputation.db", alias="DATABASE_URL")

    threatfox_api_url: str = Field(
        default="https://threatfox-api.abuse.ch/api/v1/",
        alias="THREATFOX_API_URL",
    )
    urlhaus_api_url: str = Field(
        default="https://urlhaus-api.abuse.ch/v1/",
        alias="URLHAUS_API_URL",
    )
    abuseipdb_api_key: str | None = Field(default=None, alias="ABUSEIPDB_API_KEY")
    virustotal_api_key: str | None = Field(default=None, alias="VIRUSTOTAL_API_KEY")
    otx_api_key: str | None = Field(default=None, alias="OTX_API_KEY")
    hibp_api_key: str | None = Field(default=None, alias="HIBP_API_KEY")
    request_timeout: int = Field(default=12, alias="REQUEST_TIMEOUT")

    reports_dir: Path = Path("reports")
    exports_dir: Path = Path("exports")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
