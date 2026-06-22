import pytest
import httpx
from pydantic import ValidationError

from app import main
from app.core.auth import AUTH_COOKIE_NAME, create_session_cookie_value
from app.core.config import Settings
from app.local_database import reset_connection


@main.app.get("/api/test-auth-protected")
async def auth_protected_route() -> dict[str, bool]:
    return {"ok": True}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def configured_temp_storage(monkeypatch, tmp_path):
    reset_connection()
    monkeypatch.setattr(main.settings, "data_dir", tmp_path)
    monkeypatch.setattr(main.settings, "duckdb_path", tmp_path / "auth-api.duckdb")
    monkeypatch.setattr(main.settings, "auth_enabled", False)
    monkeypatch.setattr(main.settings, "auth_username", None)
    monkeypatch.setattr(main.settings, "auth_password", None)
    monkeypatch.setattr(main.settings, "auth_session_secret", None)
    monkeypatch.setattr(main.settings, "auth_session_ttl_seconds", 86400)
    monkeypatch.setattr(main.settings, "auth_cookie_secure", False)
    yield
    reset_connection()


def test_auth_disabled_keeps_existing_api_routes_open() -> None:
    response = main.meta_filters()

    assert response.contact_types == ()
    assert response.regions == ()
    assert response.statuses == ()
    assert response.min_created_at is None
    assert response.max_created_at is None
    assert response.min_closed_at is None
    assert response.max_closed_at is None


def test_auth_enabled_with_missing_config_fails_closed() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(APP_AUTH_ENABLED=True)

    assert "APP_AUTH_USERNAME" in str(exc_info.value)
    assert "APP_AUTH_PASSWORD" in str(exc_info.value)
    assert "APP_AUTH_SESSION_SECRET" in str(exc_info.value)


@pytest.mark.anyio
async def test_protected_api_requires_session_when_auth_enabled() -> None:
    configure_auth()

    async with build_client() as client:
        response = await client.get("/api/meta/filters")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


@pytest.mark.anyio
async def test_auth_session_before_login_is_public_and_safe() -> None:
    configure_auth()

    async with build_client() as client:
        response = await client.get("/api/auth/session")

    assert response.status_code == 200
    assert response.json() == {
        "auth_enabled": True,
        "authenticated": False,
        "username": None,
    }


@pytest.mark.anyio
async def test_invalid_login_returns_generic_401_and_no_valid_session() -> None:
    configure_auth()

    async with build_client() as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "wrong-password"},
        )
        protected_response = await client.get("/api/meta/filters")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password."}
    assert AUTH_COOKIE_NAME not in response.cookies
    assert protected_response.status_code == 401


@pytest.mark.anyio
async def test_valid_login_sets_http_only_cookie_and_allows_protected_api() -> None:
    configure_auth()

    async with build_client() as client:
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "correct-password"},
        )
        protected_response = await client.get("/api/test-auth-protected")

    assert login_response.status_code == 200
    assert login_response.json() == {
        "auth_enabled": True,
        "authenticated": True,
        "username": "operator",
    }
    set_cookie = login_response.headers["set-cookie"]
    assert AUTH_COOKIE_NAME in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert protected_response.status_code == 200
    assert protected_response.json() == {"ok": True}


@pytest.mark.anyio
async def test_logout_clears_session_and_protected_api_requires_login_again() -> None:
    configure_auth()

    async with build_client() as client:
        await client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "correct-password"},
        )
        logout_response = await client.post("/api/auth/logout")
        protected_response = await client.get("/api/meta/filters")

    assert logout_response.status_code == 200
    assert logout_response.json() == {
        "auth_enabled": True,
        "authenticated": False,
        "username": None,
    }
    assert AUTH_COOKIE_NAME in logout_response.headers["set-cookie"]
    assert "Max-Age=0" in logout_response.headers["set-cookie"]
    assert protected_response.status_code == 401


@pytest.mark.anyio
async def test_expired_or_invalid_session_cookie_is_rejected() -> None:
    configure_auth()
    expired_cookie = create_session_cookie_value(main.settings, "operator", now=100)

    async with build_client() as client:
        client.cookies.set(AUTH_COOKIE_NAME, expired_cookie)
        response = await client.get("/api/meta/filters")

    assert response.status_code == 401


@pytest.mark.anyio
async def test_auth_json_responses_do_not_expose_password_or_secret() -> None:
    configure_auth()

    async with build_client() as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "operator", "password": "correct-password"},
        )
    response_text = response.text

    assert response.status_code == 200
    assert "correct-password" not in response_text
    assert "test-session-secret" not in response_text
    assert AUTH_COOKIE_NAME not in response_text


def build_client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=main.app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


def configure_auth() -> None:
    main.settings.auth_enabled = True
    main.settings.auth_username = "operator"
    main.settings.auth_password = "correct-password"
    main.settings.auth_session_secret = "test-session-secret"
    main.settings.auth_session_ttl_seconds = 3600
    main.settings.auth_cookie_secure = False
