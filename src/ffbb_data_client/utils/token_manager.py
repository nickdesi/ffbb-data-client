"""Token management for FFBB API clients."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from httpx import ReadTimeout
from pydantic import ValidationError as PydanticValidationError

from ..config import (
    API_FFBB_BASE_URL,
    DEFAULT_USER_AGENT,
    ENDPOINT_CONFIGURATION,
    ENV_API_TOKEN,
    ENV_MEILISEARCH_TOKEN,
    FALLBACK_USER_AGENTS,
)
from ..exceptions import FFBBAuthenticationError, FFBBResponseValidationError
from ..models.configuration_models import GetConfigurationResponse
from ..utils.cache_manager import CacheConfig
from ..utils.retry_utils import (
    get_default_retry_config,
    get_default_timeout_config,
    make_http_request_with_retry,
)
from ..utils.secure_logging import get_secure_logger

logger = get_secure_logger(__name__)

T = TypeVar("T")


def _catch_result(callback: Callable[[], T], is_retrieving: bool = False) -> T | None:
    """Local retry wrapper to avoid importing the helpers package and creating cycles."""
    try:
        return callback()
    except json.decoder.JSONDecodeError as e:
        if e.msg == "Expecting value":
            return None
        raise e
    except ReadTimeout as e:
        if not is_retrieving:
            return _catch_result(callback, True)
        raise e
    except ConnectionError as e:
        if not is_retrieving:
            return _catch_result(callback, True)
        raise e


@dataclass
class FFBBTokens:
    """Container for FFBB API tokens."""

    api_token: str
    meilisearch_token: str


class TokenManager:
    """
    Manages FFBB API tokens.

    Resolution order:
    1. Environment variables
    2. Fetch from FFBB API configuration endpoint (public, HTTP cached)

    Example:
        tokens = TokenManager.get_tokens()
        client = FFBBDataClient.create(
            api_bearer_token=tokens.api_token,
            meilisearch_bearer_token=tokens.meilisearch_token
        )
    """

    @staticmethod
    def get_tokens(
        cache_config: CacheConfig | None = None,
        use_cache: bool | None = None,
    ) -> FFBBTokens:
        """
        Get FFBB tokens from environment or API.

        Args:
            cache_config: Optional cache configuration object for advanced settings.
            use_cache: Simple boolean to enable/disable caching (mutually exclusive with cache_config).

        Returns:
            FFBBTokens with api_token and meilisearch_token

        Raises:
            ValueError: If both cache_config and use_cache are provided.

        Note:
            If neither cache_config nor use_cache is provided, default caching is used.
        """
        if cache_config is not None and use_cache is not None:
            raise ValueError(
                "Cannot specify both 'cache_config' and 'use_cache' parameters"
            )

        # Convert simple use_cache boolean to CacheConfig if provided
        if use_cache is not None:
            cache_config = CacheConfig(enabled=use_cache)

        # Try environment variables first
        api_token = os.getenv(ENV_API_TOKEN)
        meilisearch_token = os.getenv(ENV_MEILISEARCH_TOKEN)

        if api_token and meilisearch_token:
            return FFBBTokens(api_token=api_token, meilisearch_token=meilisearch_token)

        # Fetch from API (HTTP layer handles caching)
        config = TokenManager._fetch_configuration(cache_config)
        return FFBBTokens(
            api_token=config.api_bearer_token,
            meilisearch_token=config.meilisearch_token,
        )

    @staticmethod
    def _fetch_configuration(
        _cache_config: CacheConfig | None = None,
    ) -> GetConfigurationResponse:
        """Fetch configuration without persisting its bearer tokens in HTTP cache."""
        from ..helpers.http_requests_utils import _is_bunnycdn_block

        config_url = f"{API_FFBB_BASE_URL}{ENDPOINT_CONFIGURATION}"
        candidate_user_agents = [DEFAULT_USER_AGENT] + [
            ua for ua in FALLBACK_USER_AGENTS if ua != DEFAULT_USER_AGENT
        ]

        last_error: Exception | None = None
        for ua in candidate_user_agents:
            headers = {"user-agent": ua}

            def _get_json() -> dict[str, Any]:
                response = make_http_request_with_retry(
                    "GET",
                    config_url,
                    headers,
                    cached_session=None,
                    retry_config=get_default_retry_config(),
                    timeout_config=get_default_timeout_config(),
                )
                if response.status_code == 403 and _is_bunnycdn_block(response):
                    raise FFBBAuthenticationError(
                        f"Blocked by BunnyCDN WAF on User-Agent: {ua}",
                        status_code=403,
                    )
                response.raise_for_status()

                try:
                    import orjson  # type: ignore

                    return cast(dict[str, Any], orjson.loads(response.text.strip()))
                except ImportError:
                    try:
                        import ujson  # type: ignore

                        return cast(dict[str, Any], ujson.loads(response.text.strip()))
                    except ImportError:
                        return cast(dict[str, Any], json.loads(response.text.strip()))

            try:
                data = _catch_result(_get_json)
                actual_data = (
                    data.get("data") if data and isinstance(data, dict) else data
                )
                if not actual_data:
                    raise RuntimeError("Failed to fetch configuration from FFBB API")

                return GetConfigurationResponse.from_dict(actual_data)
            except FFBBAuthenticationError as cdn_exc:
                logger.warning(
                    f"BunnyCDN WAF blocked configuration fetch with UA '{ua}'. "
                    f"Attempting next fallback User-Agent..."
                )
                last_error = cdn_exc
                continue
            except PydanticValidationError as exc:
                raise FFBBResponseValidationError(
                    "FFBB configuration response is missing valid bearer tokens"
                ) from exc
            except Exception:
                raise

        if last_error:
            raise RuntimeError(
                f"Failed to fetch configuration from FFBB API (all User-Agents blocked): {last_error}"
            ) from last_error
        raise RuntimeError("Failed to fetch configuration from FFBB API")
