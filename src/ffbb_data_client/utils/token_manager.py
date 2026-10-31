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
    DEFAULT_FALLBACK_API_TOKEN,
    DEFAULT_FALLBACK_MEILISEARCH_TOKEN,
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

    _discovered_healthy_origin: str | None = None

    @classmethod
    def clear_discovered_origin(cls) -> None:
        """Clear any previously discovered healthy origin."""
        cls._discovered_healthy_origin = None

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

        # Autonomous fast fallback on known official Directus & Meilisearch bearer tokens
        # if configuration endpoint is challenged or fails
        try:
            config = TokenManager._fetch_configuration(cache_config)
            return FFBBTokens(
                api_token=config.api_bearer_token,
                meilisearch_token=config.meilisearch_token,
            )
        except Exception as exc:
            logger.warning(
                "Fetching /items/configuration failed (%s), using resilient default tokens.", exc
            )
            return FFBBTokens(
                api_token=DEFAULT_FALLBACK_API_TOKEN,
                meilisearch_token=DEFAULT_FALLBACK_MEILISEARCH_TOKEN,
            )

    @staticmethod
    def _fetch_configuration(
        _cache_config: CacheConfig | None = None,
    ) -> GetConfigurationResponse:
        """Fetch configuration without persisting its bearer tokens in HTTP cache."""
        from .retry_utils import _is_bunnycdn_block, reset_host_waf_block

        candidate_hosts: list[str] = []
        if TokenManager._discovered_healthy_origin:
            candidate_hosts.append(TokenManager._discovered_healthy_origin)
        for h in [
            API_FFBB_BASE_URL,
            "https://api.ffbb.com/",
            "https://api.ffbb.app/",
            "https://bo.ffbb.com/",
            "https://bo.ffbb.app/",
        ]:
            if h not in candidate_hosts:
                candidate_hosts.append(h)
        urls_to_try: list[str] = []
        for h in candidate_hosts:
            u = f"{h.rstrip('/')}/{ENDPOINT_CONFIGURATION}"
            if u not in urls_to_try:
                urls_to_try.append(u)

        candidate_user_agents = FALLBACK_USER_AGENTS

        last_error: Exception | None = None
        for config_url in urls_to_try:
            for ua in candidate_user_agents:
                headers = {"user-agent": ua}
                reset_host_waf_block(config_url)

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

                            return cast(
                                dict[str, Any], ujson.loads(response.text.strip())
                            )
                        except ImportError:
                            return cast(
                                dict[str, Any], json.loads(response.text.strip())
                            )

                try:
                    data = _catch_result(_get_json)
                    actual_data = (
                        data.get("data") if data and isinstance(data, dict) else data
                    )
                    if not actual_data:
                        continue

                    host_part = config_url.split(f"/{ENDPOINT_CONFIGURATION}")[0]
                    TokenManager._discovered_healthy_origin = (
                        host_part.rstrip("/") + "/"
                    )
                    return GetConfigurationResponse.from_dict(actual_data)
                except FFBBAuthenticationError as cdn_exc:
                    logger.warning(
                        f"BunnyCDN WAF blocked configuration fetch on {config_url} with UA '{ua}'. "
                        f"Attempting next fallback..."
                    )
                    last_error = cdn_exc
                    continue
                except PydanticValidationError as exc:
                    raise FFBBResponseValidationError(
                        "FFBB configuration response is missing valid bearer tokens"
                    ) from exc
                except Exception as exc:
                    last_error = exc
                    continue

        # Ultimate autonomous fallback: probe official ffbb.com Next.js bundles for live origins
        try:
            from .web_probe import probe_ffbb_web_origins

            probe_res = probe_ffbb_web_origins()
            discovered_candidates = [
                cand
                for cand in probe_res.get("healthy_directus_urls", [])
                if cand not in candidate_hosts
            ]
            if discovered_candidates:
                logger.info(
                    "Attempting autonomous fallback via %d live origins discovered from Next.js web bundle: %s",
                    len(discovered_candidates),
                    discovered_candidates,
                )
                for cand_host in discovered_candidates:
                    discovered_config_url = (
                        f"{cand_host.rstrip('/')}/{ENDPOINT_CONFIGURATION}"
                    )
                    for ua in candidate_user_agents:
                        headers = {"user-agent": ua}
                        reset_host_waf_block(discovered_config_url)
                        try:
                            resp = make_http_request_with_retry(
                                "GET",
                                discovered_config_url,
                                headers,
                                cached_session=None,
                                retry_config=get_default_retry_config(),
                                timeout_config=get_default_timeout_config(),
                            )
                            if resp.status_code == 200:
                                import json as _json

                                try:
                                    import orjson as _oj

                                    d = _oj.loads(resp.text.strip())
                                except ImportError:
                                    d = _json.loads(resp.text.strip())
                                act_data = d.get("data") if isinstance(d, dict) else d
                                if act_data:
                                    TokenManager._discovered_healthy_origin = (
                                        cand_host.rstrip("/") + "/"
                                    )
                                    return GetConfigurationResponse.from_dict(act_data)
                        except Exception as rec_exc:
                            last_error = rec_exc
                            continue
        except Exception as probe_err:
            logger.debug("Next.js web bundle fallback probe failed: %s", probe_err)

        if last_error:
            # Si tous les endpoints / User-Agents ont été bloqués par le WAF BunnyCDN
            if isinstance(last_error, FFBBAuthenticationError) and "BunnyCDN" in str(
                last_error
            ):
                logger.warning(
                    "All FFBB configuration endpoints are blocked by BunnyCDN WAF (%s). "
                    "Engaging resilient fallback bearer tokens.",
                    last_error,
                )
                return GetConfigurationResponse(
                    id=1,
                    key_dh=DEFAULT_FALLBACK_API_TOKEN,
                    key_ms=DEFAULT_FALLBACK_MEILISEARCH_TOKEN,
                )
            raise RuntimeError(
                f"Failed to fetch configuration from FFBB API (all endpoints/User-Agents blocked): {last_error}"
            ) from last_error
        raise RuntimeError("Failed to fetch configuration from FFBB API")
