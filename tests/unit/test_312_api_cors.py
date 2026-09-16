"""Unit tests for CORS configuration on FastAPI API."""

from starlette.testclient import TestClient

from ffbb_data_client.api import app


def test_cors_preflight_options():
    """Verify that OPTIONS preflight request allows requests from any origin."""
    client = TestClient(app)
    headers = {
        "Origin": "https://domotique.desimone.fr",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type",
    }
    resp = client.options("/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"


def test_cors_get_origin_header():
    """Verify that GET request returns proper CORS header for any origin."""
    client = TestClient(app)
    resp = client.get("/health", headers={"Origin": "https://domotique.desimone.fr"})
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "*"
