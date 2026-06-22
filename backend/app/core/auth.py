import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings


AUTH_COOKIE_NAME = "bitrix_sales_session"


@dataclass(frozen=True)
class AuthSession:
    username: str
    expires_at: int


def validate_credentials(settings: Settings, username: str, password: str) -> bool:
    if not settings.auth_enabled or settings.auth_username is None or settings.auth_password is None:
        return False

    return hmac.compare_digest(username, settings.auth_username) and hmac.compare_digest(
        password,
        settings.auth_password,
    )


def create_session_cookie_value(settings: Settings, username: str, now: int | None = None) -> str:
    if not settings.auth_session_secret:
        raise ValueError("Auth session secret is not configured.")

    issued_at = int(time.time() if now is None else now)
    payload = {
        "sub": username,
        "exp": issued_at + settings.auth_session_ttl_seconds,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_part = _base64url_encode(payload_bytes)
    signature = _sign(payload_part.encode("ascii"), settings.auth_session_secret)
    return f"{payload_part}.{signature}"


def validate_session_cookie(
    settings: Settings,
    cookie_value: str | None,
    now: int | None = None,
) -> AuthSession | None:
    if not settings.auth_enabled or not settings.auth_session_secret or not cookie_value:
        return None

    try:
        payload_part, signature = cookie_value.split(".", 1)
    except ValueError:
        return None

    expected_signature = _sign(payload_part.encode("ascii"), settings.auth_session_secret)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = json.loads(_base64url_decode(payload_part))
    except (json.JSONDecodeError, ValueError):
        return None

    session = _parse_session_payload(payload)
    if session is None:
        return None

    current_time = int(time.time() if now is None else now)
    if session.expires_at <= current_time:
        return None

    if settings.auth_username is None or not hmac.compare_digest(
        session.username,
        settings.auth_username,
    ):
        return None

    return session


def build_auth_status(settings: Settings, session: AuthSession | None) -> dict[str, object]:
    if not settings.auth_enabled:
        return {
            "auth_enabled": False,
            "authenticated": True,
            "username": None,
        }

    return {
        "auth_enabled": True,
        "authenticated": session is not None,
        "username": session.username if session is not None else None,
    }


def _parse_session_payload(payload: Any) -> AuthSession | None:
    if not isinstance(payload, dict):
        return None

    username = payload.get("sub")
    expires_at = payload.get("exp")
    if not isinstance(username, str) or not isinstance(expires_at, int):
        return None

    return AuthSession(username=username, expires_at=expires_at)


def _sign(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
