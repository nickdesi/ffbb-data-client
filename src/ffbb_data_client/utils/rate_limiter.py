"""Rate limiting and traffic shaping for FFBB Directus API (api.ffbb.com).

Protects against HTTP 429 Too Many Requests and BunnyCDN edge rate-limiting by:
1. Limiting outbound request concurrency (max 2 concurrent in-flight requests).
2. Enforcing a token-bucket rate limit (default 3.0 req/s, burst 3).
3. Backoff cooldown when HTTP 429 is received upstream.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import threading
import time
from typing import Any

from .secure_logging import get_secure_logger

logger = get_secure_logger(__name__)


class DirectusRateLimiter:
    """Thread-safe and asyncio-safe rate limiter for Directus calls."""

    def __init__(
        self,
        rate: float = 3.0,
        burst: int = 3,
        max_concurrency: int = 2,
        min_jitter: float = 0.0,
        max_jitter: float = 0.0,
    ) -> None:
        self.rate = float(os.getenv("FFBB_MAX_RPS", str(rate)))
        self.burst = int(os.getenv("FFBB_MAX_BURST", str(burst)))
        self.max_concurrency = int(
            os.getenv("FFBB_MAX_CONCURRENCY", str(max_concurrency))
        )
        self.min_jitter = float(os.getenv("FFBB_MIN_JITTER", str(min_jitter)))
        self.max_jitter = float(os.getenv("FFBB_MAX_JITTER", str(max_jitter)))

        self._tokens = float(self.burst)
        self._last_refill = time.monotonic()
        self._cooldown_until: float = 0.0

        self._thread_lock = threading.Lock()
        self._async_lock: asyncio.Lock | None = None
        self._semaphore: asyncio.Semaphore | None = None
        self._sync_semaphore = threading.Semaphore(self.max_concurrency)

    def _sample_jitter(self) -> float:
        if self.max_jitter > 0 and self.max_jitter >= self.min_jitter:
            return secrets.SystemRandom().uniform(self.min_jitter, self.max_jitter)
        return 0.0

    def _get_async_primitives(self) -> tuple[asyncio.Lock, asyncio.Semaphore]:
        """Lazy initialization of asyncio primitives inside the running event loop."""
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self.max_concurrency)
        return self._async_lock, self._semaphore

    def _refill(self, now: float) -> None:
        if now < self._last_refill:
            self._tokens = float(self.burst)
            self._last_refill = now
            self._cooldown_until = 0.0
            return
        elapsed = now - self._last_refill
        self._tokens = min(float(self.burst), self._tokens + elapsed * self.rate)
        self._last_refill = now

    def report_rate_limit(self, retry_after: float | None = None) -> None:
        """Triggered upon encountering HTTP 429: enforce immediate cooldown."""
        cooldown = max(3.5, retry_after or 3.5)
        with self._thread_lock:
            self._cooldown_until = time.monotonic() + cooldown
            self._tokens = 0.0
            logger.warning(
                "DirectusRateLimiter: Cooldown actif de %.1fs suite à HTTP 429.",
                cooldown,
            )

    async def acquire(self) -> None:
        """Acquire a slot to dispatch an async request to Directus."""
        async_lock, sem = self._get_async_primitives()
        await sem.acquire()

        while True:
            now = time.monotonic()

            async with async_lock:
                with self._thread_lock:
                    if now < self._cooldown_until:
                        wait_time = self._cooldown_until - now
                    else:
                        self._refill(now)
                        if self._tokens >= 1.0:
                            self._tokens -= 1.0
                            jitter_delay = self._sample_jitter()
                            if jitter_delay > 0:
                                self._cooldown_until = max(
                                    self._cooldown_until, now + jitter_delay
                                )
                            return
                        wait_time = (1.0 - self._tokens) / self.rate

            if wait_time > 0:
                await asyncio.sleep(wait_time)

    def release(self) -> None:
        """Release the concurrency slot."""
        if self._semaphore is not None:
            self._semaphore.release()

    async def __aenter__(self) -> DirectusRateLimiter:
        await self.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.release()

    def acquire_sync(self) -> None:
        """Acquire a slot synchronously for sync threads."""
        self._sync_semaphore.acquire()
        while True:
            now = time.monotonic()
            with self._thread_lock:
                if now < self._cooldown_until:
                    wait_time = self._cooldown_until - now
                else:
                    self._refill(now)
                    if self._tokens >= 1.0:
                        self._tokens -= 1.0
                        jitter_delay = self._sample_jitter()
                        if jitter_delay > 0:
                            self._cooldown_until = max(
                                self._cooldown_until, now + jitter_delay
                            )
                        return
                    wait_time = (1.0 - self._tokens) / self.rate
            if wait_time > 0:
                time.sleep(wait_time)

    def release_sync(self) -> None:
        self._sync_semaphore.release()

    def __enter__(self) -> DirectusRateLimiter:
        self.acquire_sync()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release_sync()


_RATE_LIMITER_INSTANCE: DirectusRateLimiter | None = None
_RATE_LIMITER_LOCK = threading.Lock()


def get_directus_rate_limiter() -> DirectusRateLimiter:
    global _RATE_LIMITER_INSTANCE
    if _RATE_LIMITER_INSTANCE is None:
        with _RATE_LIMITER_LOCK:
            if _RATE_LIMITER_INSTANCE is None:
                _RATE_LIMITER_INSTANCE = DirectusRateLimiter()
    return _RATE_LIMITER_INSTANCE
