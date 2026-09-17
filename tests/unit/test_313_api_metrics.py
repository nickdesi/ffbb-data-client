"""Unit tests for Prometheus /metrics endpoint on FastAPI API."""

import httpx
import pytest

from ffbb_data_client.api import app


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_valid_prometheus_format():
    """Verify that /metrics endpoint returns 200 with standard Prometheus exposition format."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Trigger an endpoint to record metrics
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200

        # Now query /metrics
        metrics_resp = await client.get("/metrics")
        assert metrics_resp.status_code == 200
        assert "text/plain" in metrics_resp.headers.get("content-type", "")

        text = metrics_resp.text
        assert "ffbb_api_uptime_seconds" in text
        assert "ffbb_api_http_requests_total" in text
        assert "ffbb_api_http_latency_seconds_bucket" in text
        assert "ffbb_api_http_latency_seconds_sum" in text
        assert "ffbb_api_http_latency_seconds_count" in text
        assert "ffbb_api_http_inflight_requests" in text
        assert "ffbb_api_cache_entries" in text
        assert 'path="/health"' in text
        assert 'status="200"' in text
