from app.main import app, health


def test_health_route_is_registered() -> None:
    routes = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/health"
        and "GET" in getattr(route, "methods", set())
    ]

    assert len(routes) == 1
    assert getattr(routes[0], "endpoint", None) is health


def test_health_returns_ok_payload() -> None:
    assert health() == {"status": "ok", "environment": "local"}
