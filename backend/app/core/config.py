from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
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
    auth_enabled: bool = Field(
        default=False,
        validation_alias="APP_AUTH_ENABLED",
    )
    auth_username: str | None = Field(
        default=None,
        validation_alias="APP_AUTH_USERNAME",
    )
    auth_password: str | None = Field(
        default=None,
        validation_alias="APP_AUTH_PASSWORD",
    )
    auth_session_secret: str | None = Field(
        default=None,
        validation_alias="APP_AUTH_SESSION_SECRET",
    )
    auth_session_ttl_seconds: int = Field(
        default=86400,
        gt=0,
        validation_alias="APP_AUTH_SESSION_TTL_SECONDS",
    )
    auth_cookie_secure: bool = Field(
        default=False,
        validation_alias="APP_AUTH_COOKIE_SECURE",
    )

    @field_validator("duckdb_path", mode="before")
    @classmethod
    def empty_duckdb_path_uses_default(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @field_validator("auth_username", "auth_password", "auth_session_secret", mode="before")
    @classmethod
    def empty_auth_value_uses_none(cls, value: object) -> object:
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def require_auth_settings_when_enabled(self) -> "Settings":
        if not self.auth_enabled:
            return self

        missing = [
            name
            for name, value in (
                ("APP_AUTH_USERNAME", self.auth_username),
                ("APP_AUTH_PASSWORD", self.auth_password),
                ("APP_AUTH_SESSION_SECRET", self.auth_session_secret),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                "Auth is enabled but required auth settings are missing: "
                + ", ".join(missing)
            )

        return self

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
