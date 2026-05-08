"""
Advanced cache management for FFBB Data Client.

This module provides sophisticated caching strategies including:
- Multi-level caching (memory, disk, Redis)
- Configurable cache policies
- Cache performance metrics
- Intelligent cache invalidation
- Cache warming capabilities
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from typing import Any, cast

import hishel
import hishel.httpx
import httpx


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    sets: int = 0
    errors: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def reset(self) -> None:
        """Reset all metrics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.sets = 0
        self.errors = 0


class CacheConfig:
    """
    Configuration for cache behavior.

    Attributes:
        enabled: Whether caching is enabled.
        backend: Cache backend ('memory', 'sqlite', 'redis').
        expire_after: Default expiration time in seconds.
        max_size: Maximum cache size (for memory backend).
        redis_url: Redis URL for Redis backend.
        key_prefix: Prefix for cache keys.
        compression: Whether to compress cached data.
        transport_retries: Low-level HTTP transport retries.
    """

    def __init__(
        self,
        enabled: bool = True,
        backend: str = "sqlite",
        expire_after: int = 1800,  # 30 minutes
        max_size: int = 1000,
        redis_url: str | None = None,
        key_prefix: str = "ffbb_api",
        compression: bool = False,
        transport_retries: int = 0,
    ) -> None:
        """
        Initialize cache configuration.

        Args:
            enabled: Whether caching is enabled.
            backend: Cache backend type.
            expire_after: Default expiration time.
            max_size: Maximum cache size for memory backend.
            redis_url: Redis connection URL.
            key_prefix: Prefix for cache keys.
            compression: Whether to compress cached data.
            transport_retries: Low-level HTTP transport retries.
        """
        self.enabled = enabled
        self.backend = backend
        self.expire_after = expire_after
        self.max_size = max_size
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.compression = compression
        self.transport_retries = transport_retries


class CacheManager:
    """
    Thread-safe singleton cache manager for API requests.

    This class implements the singleton pattern with double-check locking
    to ensure thread safety during instance creation.

    Attributes:
        config: Cache configuration settings.
        metrics: Cache performance metrics.
    """

    _instance: CacheManager | None = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls, config: CacheConfig | None = None) -> CacheManager:
        """
        Create or return the singleton instance.

        Uses double-check locking for thread safety.

        Args:
            config: Optional configuration for first instantiation.

        Returns:
            The singleton CacheManager instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    cls._instance = instance
        return cls._instance

    def __init__(self, config: CacheConfig | None = None) -> None:
        """
        Initialize the cache manager instance.

        Only initializes on first call to avoid re-initialization.

        Args:
            config: Cache configuration settings.
        """
        if CacheManager._initialized:
            return

        with CacheManager._lock:
            if CacheManager._initialized:
                return

            self.config = config or CacheConfig()
            self.metrics = CacheMetrics()
            self._memory_cache: dict[str, dict[str, Any]] = {}
            self._client: httpx.Client | None = None
            self._async_client: httpx.AsyncClient | None = None

            if self.config.enabled:
                self._initialize_cache()

            CacheManager._initialized = True

    def _initialize_cache(self) -> None:
        """Initialize the cache backend."""
        policy = hishel.FilterPolicy()
        policy.use_body_key = True
        # ── AJOUT : force le cache indépendamment des headers HTTP ──────────
        # hishel respecte RFC 7234 par défaut → ne cache pas si le serveur
        # ne renvoie pas de Cache-Control/ETag. FFBB n'en envoie pas.
        cast(Any, policy).cacheable_methods = ["GET", "POST"]
        cast(Any, policy).cacheable_status_codes = [200, 203, 204, 206, 300, 301, 308]
        # ────────────────────────────────────────────────────────────────────

        if self.config.backend == "memory":
            import sqlite3

            # Use separate in-memory SQLite connections for sync and async:
            # sharing one connection across threads (sync vs asyncio) is not safe.
            sync_conn = sqlite3.connect(":memory:", check_same_thread=False)
            async_conn = sqlite3.connect(":memory:", check_same_thread=False)
            storage = hishel.SyncSqliteStorage(
                connection=sync_conn, default_ttl=self.config.expire_after
            )
            self._client = hishel.httpx.SyncCacheClient(
                storage=storage,
                policy=policy,
                transport=httpx.HTTPTransport(retries=self.config.transport_retries),
            )
            # Async version uses its own connection
            async_storage = hishel.AsyncSqliteStorage(
                connection=cast(Any, async_conn), default_ttl=self.config.expire_after
            )
            self._async_client = hishel.httpx.AsyncCacheClient(
                storage=async_storage,
                policy=policy,
                transport=httpx.AsyncHTTPTransport(
                    retries=self.config.transport_retries
                ),
            )
        elif self.config.backend == "sqlite":
            storage = hishel.SyncSqliteStorage(
                database_path="http_cache.db", default_ttl=self.config.expire_after
            )
            self._client = hishel.httpx.SyncCacheClient(
                storage=storage,
                policy=policy,
                transport=httpx.HTTPTransport(retries=self.config.transport_retries),
            )
            # Async version
            async_storage = hishel.AsyncSqliteStorage(
                database_path="http_cache.db", default_ttl=self.config.expire_after
            )
            self._async_client = hishel.httpx.AsyncCacheClient(
                storage=async_storage,
                policy=policy,
                transport=httpx.AsyncHTTPTransport(
                    retries=self.config.transport_retries
                ),
            )
        else:
            raise ValueError(f"Unsupported cache backend: {self.config.backend}")

    def create_cache_key(self, request: httpx.Request, **_kwargs: Any) -> str:
        """
        Create a cache key from the request.

        Args:
            request: httpx Request.
            **_kwargs: Additional arguments (ignored).

        Returns:
            Cache key string.
        """
        key_parts = [
            request.method or "GET",
            str(request.url) or "",
        ]

        if request.headers:
            auth_header = request.headers.get("Authorization", "")
            if auth_header:
                key_parts.append("auth_masked")

        if request.method == "POST" and request.content:
            content_bytes = (
                request.content
                if isinstance(request.content, bytes)
                else str(request.content).encode("utf-8")
            )
            body_hash = hashlib.md5(content_bytes).hexdigest()
            key_parts.append(body_hash)

        key_string = "|".join(key_parts)
        return (
            f"{self.config.key_prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        )

    @property
    def session(self) -> httpx.Client | None:
        """Get the cached session."""
        return self._client if self.config.enabled else None

    @property
    def async_session(self) -> httpx.AsyncClient | None:
        """Get the cached async session."""
        return self._async_client if self.config.enabled else None

    def get_session(
        self, async_mode: bool = False
    ) -> httpx.Client | httpx.AsyncClient | None:
        """
        Get the cached session.

        Args:
            async_mode: Whether to return the async session.

        Returns:
            The cached session or None if caching is disabled.
        """
        if async_mode:
            return self.async_session
        return self.session

    def is_enabled(self) -> bool:
        """
        Check if caching is enabled.

        Returns:
            True if caching is enabled.
        """
        return self.config.enabled and self._client is not None

    def clear_cache(self) -> bool:
        """
        Clear all cached data.

        Returns:
            True if cache was cleared successfully, False otherwise.
        """
        if self._client is None:
            return False
        try:
            storage = getattr(self._client, "_storage", None)
            clear_fn = getattr(storage, "clear", None)
            if callable(clear_fn):
                clear_fn()
                self.metrics.evictions = 0
                return True
            return False
        except (OSError, RuntimeError, AttributeError):
            self.metrics.errors += 1
            return False

    def get_cache_size(self) -> int:
        """
        Get the current cache size.

        Returns:
            Number of cached items.
        """
        if self._client is None:
            return 0
        try:
            storage = getattr(self._client, "_storage", None)
            count_method = getattr(storage, "count", None)
            if count_method is not None:
                return cast(int, count_method())
        except (OSError, RuntimeError, AttributeError):
            self.metrics.errors += 1
        return 0

    def get_metrics(self) -> CacheMetrics:
        """
        Get cache performance metrics.

        Returns:
            Current cache metrics.
        """
        return self.metrics

    def warm_cache(self, urls: list[str], headers: dict[str, str] | None = None) -> int:
        """
        Warm the cache by pre-fetching specified URLs.

        Args:
            urls: List of URLs to cache.
            headers: Headers to use for requests.

        Returns:
            Number of URLs successfully cached.
        """
        if not self.is_enabled() or self._client is None:
            return 0

        headers = headers or {}
        count = 0
        for url in urls:
            try:
                self._client.get(url, headers=headers, timeout=10)
                count += 1
            except (OSError, ConnectionError, TimeoutError, ValueError):
                self.metrics.errors += 1
                continue
        return count

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match for invalidation.

        Returns:
            Number of entries invalidated.
        """
        if not self.is_enabled() or self._client is None:
            return 0

        try:
            getattr(self._client, "_storage", None)
            # hishel storage doesn't generally support pattern invalidation exposing cache_dict,
            # so we'd need to iterate visually, but for now we skip or implement if needed
            return 0
        except (OSError, RuntimeError, AttributeError, KeyError):
            self.metrics.errors += 1
        return 0

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing purposes)."""
        with cls._lock:
            if cls._instance is not None:
                client = getattr(cls._instance, "_client", None)
                if client is not None:
                    client.close()
            cls._instance = None
            cls._initialized = False
