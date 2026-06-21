from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    name: str = "Bitrix Sales Analytics"
    env: str = "local"
    debug: bool = False
    timezone: str = "Europe/Minsk"
    allowed_origins: str = "http://localhost:3000"
    bitrix_webhook_url: str | None = Field(
        default=None,
        validation_alias="BITRIX_WEBHOOK_URL",
    )
    bitrix_contact_type_field: str | None = Field(
        default=None,
        validation_alias="BITRIX_CONTACT_TYPE_FIELD",
    )
    bitrix_page_size: int = Field(
        default=50,
        ge=1,
        le=50,
        validation_alias="BITRIX_PAGE_SIZE",
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
