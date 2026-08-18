from __future__ import annotations

import copy
import hashlib
import json
import threading
import time
from collections.abc import Sequence
from typing import Any

import httpx
from httpx import Client

from ..config import (
    DEFAULT_USER_AGENT,
    MEILISEARCH_BASE_URL,
    MEILISEARCH_ENDPOINT_MULTI_SEARCH,
)
from ..helpers.http_requests_helper import catch_result
from ..helpers.http_requests_utils import (
    http_post_json,
    http_post_json_async,
)
from ..models.multi_search_query import MultiSearchQuery
from ..models.multi_search_results_class import MultiSearchResults
from ..utils.cache_manager import CacheManager
from ..utils.retry_utils import (
    RetryConfig,
    TimeoutConfig,
    get_default_retry_config,
    get_default_timeout_config,
)
from ..utils.secure_logging import get_secure_logger

_APP_CACHE: dict[str, tuple[float, Any]] = {}
_APP_CACHE_LOCK = threading.Lock()
_APP_CACHE_TTL: int = 300  # secondes, modifiable


def _make_cache_key(queries: Sequence[MultiSearchQuery] | None) -> str:
    payload = [q.to_dict() for q in queries] if queries else []
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Any | None:
    with _APP_CACHE_LOCK:
        entry = _APP_CACHE.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _APP_CACHE_TTL:
        with _APP_CACHE_LOCK:
            _APP_CACHE.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    with _APP_CACHE_LOCK:
        _APP_CACHE[key] = (time.monotonic(), value)


def _cache_result_object(key: str, result: MultiSearchResults) -> None:
    _cache_set(key, copy.deepcopy(result))


def clear_meili_app_cache() -> None:
    """Vide le cache applicatif (utile pour les tests)."""
    with _APP_CACHE_LOCK:
        _APP_CACHE.clear()


logger = get_secure_logger(__name__)


class MeilisearchClient:
    url: str = ""
    debug: bool = False
    cached_session: Client | None = None
    async_cached_session: httpx.AsyncClient | None = None
    retry_config: RetryConfig | None = None
    timeout_config: TimeoutConfig | None = None

    def __init__(
        self,
        bearer_token: str,
        url: str = MEILISEARCH_BASE_URL,
        debug: bool = False,
        cached_session: Client | None = None,
        *,
        async_cached_session: httpx.AsyncClient | None = None,
        retry_config: RetryConfig | None = None,
        timeout_config: TimeoutConfig | None = None,
    ):
        """
        Initializes an instance of the MeilisearchClient class.

        Args:
            bearer_token (str): The bearer token used for authentication.
            url (str, optional): The base URL.
                Defaults to "https://meilisearch-prod.ffbb.app/".
            debug (bool, optional): Whether to enable debug mode. Defaults to False.
            cached_session (Client, optional): The cached session to use.
            retry_config (RetryConfig, optional): Retry configuration. Defaults to None.
            timeout_config (TimeoutConfig, optional): Timeout configuration.
                Defaults to None.
        """
        if not bearer_token or not bearer_token.strip():
            raise ValueError("bearer_token cannot be None, empty, or whitespace-only")

        # Store token securely (private attribute)
        self._bearer_token = bearer_token
        self.url = url
        self.debug = debug
        self.cached_session = (
            cached_session if cached_session else CacheManager().session
        )
        self.async_cached_session = (
            async_cached_session
            if async_cached_session
            else CacheManager().async_session
        )
        self.headers = {
            "Authorization": f"Bearer {self._bearer_token}",
            "Content-Type": "application/json",
            "user-agent": DEFAULT_USER_AGENT,
        }

        # Configure retry and timeout settings
        self.retry_config = retry_config or get_default_retry_config()
        self.timeout_config = timeout_config or get_default_timeout_config()

        # Initialize secure logger
        self.logger = get_secure_logger(f"{self.__class__.__name__}")

        # Log initialization without leaking token
        if self.debug:
            self.logger.info(
                "MeilisearchClient initialized with authentication token configured"
            )
            self.logger.info(
                f"Retry config: {self.retry_config.max_attempts} attempts, "
                f"timeout: {self.timeout_config.total_timeout}s"
            )
        else:
            self.logger.info("MeilisearchClient initialized successfully")

    @property
    def bearer_token(self) -> str:
        """Get the bearer token."""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth.removeprefix("Bearer ")
        return self._bearer_token

    def multi_search(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: Client | None = None,
    ) -> MultiSearchResults | None:
        key = _make_cache_key(queries)
        cached = _cache_get(key)
        if cached is not None:
            cached_copy: MultiSearchResults = copy.deepcopy(cached)
            return cached_copy

        url = f"{self.url}{MEILISEARCH_ENDPOINT_MULTI_SEARCH}"
        params = {"queries": [query.to_dict() for query in queries] if queries else []}
        raw_data = catch_result(
            lambda: http_post_json(
                url,
                self.headers,
                params,
                debug=self.debug,
                cached_session=cached_session or self.cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
        )
        result: MultiSearchResults | None = (
            MultiSearchResults.from_dict(raw_data) if raw_data else None
        )
        if result is not None:
            _cache_result_object(key, result)
        return result

    async def multi_search_async(
        self,
        queries: Sequence[MultiSearchQuery] | None = None,
        cached_session: httpx.AsyncClient | None = None,
    ) -> MultiSearchResults | None:
        key = _make_cache_key(queries)
        cached = _cache_get(key)
        if cached is not None:
            cached_copy: MultiSearchResults = copy.deepcopy(cached)
            return cached_copy

        url = f"{self.url}{MEILISEARCH_ENDPOINT_MULTI_SEARCH}"
        params = {"queries": [query.to_dict() for query in queries] if queries else []}
        try:
            raw_data = await http_post_json_async(
                url,
                self.headers,
                params,
                debug=self.debug,
                cached_session=cached_session or self.async_cached_session,
                retry_config=self.retry_config,
                timeout_config=self.timeout_config,
            )
            result: MultiSearchResults | None = (
                MultiSearchResults.from_dict(raw_data) if raw_data else None
            )
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            self.logger.warning("multi_search_async request failed: %s", e)
            result = None
        except Exception as e:
            self.logger.error("multi_search_async unexpected error: %s", e)
            result = None

        if result is not None:
            _cache_result_object(key, result)
        return result
