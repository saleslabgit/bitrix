from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
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
    data_dir: Path = Field(
        default=Path("data"),
        validation_alias="APP_DATA_DIR",
    )
    duckdb_path: Path | None = Field(
        default=None,
        validation_alias="APP_DUCKDB_PATH",
    )

    @field_validator("duckdb_path", mode="before")
    @classmethod
    def empty_duckdb_path_uses_default(cls, value: object) -> object:
        if value == "":
            return None
        return value

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
