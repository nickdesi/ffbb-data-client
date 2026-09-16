"""Unit tests for CORS configuration on FastAPI API."""

import httpx
import pytest

from ffbb_data_client.api import app


@pytest.mark.asyncio
async def test_cors_preflight_options():
    """Verify that OPTIONS preflight request allows requests from any origin."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = {
            "Origin": "https://domotique.desimone.fr",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        resp = await client.options("/health", headers=headers)
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "*"


@pytest.mark.asyncio
async def test_cors_get_origin_header():
    """Verify that GET request returns proper CORS header for any origin."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/health", headers={"Origin": "https://domotique.desimone.fr"}
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == "*"
