import time

import pytest
from httpx import Request, Response

from ffbb_data_client.utils.rate_limiter import DirectusRateLimiter
from ffbb_data_client.utils.retry_utils import RetryConfig, calculate_delay


@pytest.mark.asyncio
async def test_directus_rate_limiter_acquire_release():
    limiter = DirectusRateLimiter(rate=10.0, burst=5, max_concurrency=2)
    t0 = time.monotonic()
    await limiter.acquire()
    limiter.release()
    elapsed = time.monotonic() - t0
    assert elapsed < 0.2


@pytest.mark.asyncio
async def test_directus_rate_limiter_cooldown_on_429():
    limiter = DirectusRateLimiter(rate=10.0, burst=2, max_concurrency=2)
    limiter.report_rate_limit(retry_after=0.5)
    t0 = time.monotonic()
    await limiter.acquire()
    limiter.release()
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.45


def test_calculate_delay_with_429_retry_after():
    config = RetryConfig(base_delay=1.0)
    req = Request("GET", "https://api.ffbb.com/test")
    resp_429 = Response(429, headers={"Retry-After": "4.0"}, request=req)
    delay = calculate_delay(0, config, resp_429)
    assert 4.0 <= delay <= 4.6


def test_calculate_delay_with_429_default_floor():
    config = RetryConfig(base_delay=1.0)
    req = Request("GET", "https://api.ffbb.com/test")
    resp_429 = Response(429, request=req)
    delay = calculate_delay(0, config, resp_429)
    # Floor delay for 429 is at least 2.5s
    assert delay >= 2.5
