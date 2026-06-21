from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    name: str = "Bitrix Sales Analytics"
    env: str = "local"
    debug: bool = False
    timezone: str = "Europe/Minsk"
    allowed_origins: str = "http://localhost:3000"
    bitrix_webhook_url: str = Field(
        default="https://example.bitrix24.com/rest/USER_ID/WEBHOOK_TOKEN/",
        validation_alias="BITRIX_WEBHOOK_URL",
    )

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
