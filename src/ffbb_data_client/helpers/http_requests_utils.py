from __future__ import annotations

import atexit
import json
import time
from typing import Any
from urllib.parse import urlencode

try:
    import orjson  # type: ignore

    _JSON_LOADS = orjson.loads
except ImportError:
    try:
        import ujson  # type: ignore

        _JSON_LOADS = ujson.loads
    except ImportError:
        _JSON_LOADS = json.loads

import httpx
from httpx import Client, Response

from ..utils.retry_utils import (
    RetryConfig,
    TimeoutConfig,
    make_http_request_with_retry,
    make_http_request_with_retry_async,
)
from ..utils.secure_logging import get_secure_logger

logger = get_secure_logger(__name__)

_DEFAULT_SYNC_CLIENT: httpx.Client | None = None
_DEFAULT_ASYNC_CLIENT: httpx.AsyncClient | None = None

# ⚡ Performance optimization: Connection limits to keep TLS sockets warm across calls
_POOL_LIMITS = httpx.Limits(max_keepalive_connections=50, max_connections=200)


def _build_timeout(timeout: int | float | TimeoutConfig | None) -> httpx.Timeout:
    if isinstance(timeout, TimeoutConfig):
        return httpx.Timeout(
            timeout.total_timeout,
            connect=timeout.connect_timeout,
            read=timeout.read_timeout,
            write=timeout.read_timeout,
            pool=timeout.connect_timeout,
        )
    value = 20.0 if timeout is None else float(timeout)
    return httpx.Timeout(value)


def _get_default_sync_client(timeout: int | float = 20) -> httpx.Client:
    global _DEFAULT_SYNC_CLIENT
    if _DEFAULT_SYNC_CLIENT is None or _DEFAULT_SYNC_CLIENT.is_closed:
        _DEFAULT_SYNC_CLIENT = httpx.Client(
            timeout=_build_timeout(timeout),
            limits=_POOL_LIMITS,
        )
    return _DEFAULT_SYNC_CLIENT


async def _get_default_async_client(timeout: int | float = 20) -> httpx.AsyncClient:
    global _DEFAULT_ASYNC_CLIENT
    if _DEFAULT_ASYNC_CLIENT is None or _DEFAULT_ASYNC_CLIENT.is_closed:
        _DEFAULT_ASYNC_CLIENT = httpx.AsyncClient(
            timeout=_build_timeout(timeout),
            limits=_POOL_LIMITS,
        )
    return _DEFAULT_ASYNC_CLIENT


def close_default_clients() -> None:
    """Close module-level fallback clients used when no session is provided."""
    global _DEFAULT_SYNC_CLIENT, _DEFAULT_ASYNC_CLIENT
    if _DEFAULT_SYNC_CLIENT is not None and not _DEFAULT_SYNC_CLIENT.is_closed:
        _DEFAULT_SYNC_CLIENT.close()
    _DEFAULT_SYNC_CLIENT = None
    _DEFAULT_ASYNC_CLIENT = None


atexit.register(close_default_clients)


def _handle_token_refresh(
    url: str, headers: dict[str, str], debug: bool = False
) -> bool:
    """
    Tente de rafraîchir les tokens de la FFBB via TokenManager.
    Met à jour l'en-tête 'Authorization' dans le dictionnaire headers.
    """
    if "Authorization" not in headers:
        return False
    try:
        if debug:
            logger.info(
                "Détection d'une erreur 401/403 de sécurité. Tentative de rafraîchissement automatique du token..."
            )

        from ..utils.token_manager import TokenManager

        tokens = TokenManager.get_tokens(use_cache=False)

        if "meilisearch" in url.lower():
            new_token = tokens.meilisearch_token
        else:
            new_token = tokens.api_token

        headers["Authorization"] = f"Bearer {new_token}"
        if debug:
            logger.info(
                "Le token a été rafraîchi et mis à jour dynamiquement dans les headers."
            )
        return True
    except Exception as e:
        logger.error(f"Échec du rafraîchissement automatique du token : {e}")
        return False


def to_json_from_response(response: Response) -> Any:
    """
    Converts the HTTP response to a JSON dictionary.

    Args:
        response (Response): The HTTP response.

    Returns:
        Any: Parsed JSON payload (dict, list, etc.).
    """
    data_str = response.text.strip()

    try:
        return _JSON_LOADS(data_str)
    except Exception:
        pass

    if data_str.endswith(","):
        data_str = data_str[:-1]

    data_str = data_str.replace("][", ",")
    data_str = data_str.replace("KO", "")

    if data_str.startswith('""'):
        data_str = data_str[2:]

    try:
        return _JSON_LOADS(data_str)
    except Exception as e:
        logger.warning(f"Error in to_json_from_response: {e}")
        try:
            return response.json()
        except Exception:
            raise e


def http_get(
    url: str,
    headers: dict[str, str],
    debug: bool = False,
    cached_session: Client | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Response:
    """
    Performs an HTTP GET request with retry logic.

    Args:
        url (str): The URL of the request.
        headers (Dict[str, str]): The headers of the request.
        debug (bool): Whether to enable debug mode or not. Default is False.
        cached_session (CachedSession): Cached session to use. Default is None.
        timeout (int): The timeout value in seconds. Default is 20.
        retry_config (RetryConfig): Retry configuration. Default is None.
        timeout_config (TimeoutConfig): Timeout configuration. Default is None.

    Returns:
        Response: The HTTP response.
    """
    start_time: float = 0.0
    if debug:
        logger.debug(f"Making GET request to {url}")
        start_time = time.time()

    # Use retry logic if configured
    if retry_config and timeout_config:
        response = make_http_request_with_retry(
            "GET",
            url,
            headers,
            cached_session=cached_session,
            retry_config=retry_config,
            timeout_config=timeout_config,
            debug=debug,
        )
    else:
        # Fallback to reusable client to keep connections warm across calls.
        if cached_session:
            response = cached_session.get(
                url, headers=headers, timeout=_build_timeout(timeout_config or timeout)
            )
        else:
            response = _get_default_sync_client(timeout).get(
                url, headers=headers, timeout=_build_timeout(timeout_config or timeout)
            )

    if response.status_code in (401, 403) and "Authorization" in headers:
        if _handle_token_refresh(url, headers, debug):
            if retry_config and timeout_config:
                response = make_http_request_with_retry(
                    "GET",
                    url,
                    headers,
                    cached_session=cached_session,
                    retry_config=retry_config,
                    timeout_config=timeout_config,
                    debug=debug,
                )
            else:
                if cached_session:
                    response = cached_session.get(
                        url,
                        headers=headers,
                        timeout=_build_timeout(timeout_config or timeout),
                    )
                else:
                    response = _get_default_sync_client(timeout).get(
                        url,
                        headers=headers,
                        timeout=_build_timeout(timeout_config or timeout),
                    )

    if debug:
        end_time = time.time()
        logger.debug(f"GET request to {url} took {end_time - start_time} seconds.")
        logger.debug(f"GET response: {response.text}")

    return response


def http_post(
    url: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    debug: bool = False,
    cached_session: Client | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Response:
    """
    Performs an HTTP POST request with retry logic.

    Args:
        url (str): The URL of the request.
        headers (Dict[str, str]): The headers of the request.
        data (Dict[str, Any]): The data of the request.
        debug (bool): Whether to enable debug mode or not. Default is False.
        cached_session (CachedSession): Cached session to use. Default is None.
        timeout (int): The timeout value in seconds. Default is 20.
        retry_config (RetryConfig): Retry configuration. Default is None.
        timeout_config (TimeoutConfig): Timeout configuration. Default is None.

    Returns:
        Response: The HTTP response.
    """
    start_time: float = 0.0
    data_str: str = ""
    if debug:
        data_str = ", ".join([f"{k}:{v}" for k, v in data.items()]) if data else ""
        logger.debug(f"Making POST request to {url} {data_str}")
        start_time = time.time()

    # Use retry logic if configured
    if retry_config and timeout_config:
        response = make_http_request_with_retry(
            "POST",
            url,
            headers,
            data=data,
            cached_session=cached_session,
            retry_config=retry_config,
            timeout_config=timeout_config,
            debug=debug,
        )
    else:
        # Fallback to reusable client to keep connections warm across calls.
        if cached_session:
            response = cached_session.post(
                url,
                headers=headers,
                json=data,
                timeout=_build_timeout(timeout_config or timeout),
            )
        else:
            response = _get_default_sync_client(timeout).post(
                url,
                headers=headers,
                json=data,
                timeout=_build_timeout(timeout_config or timeout),
            )

    if response.status_code in (401, 403) and "Authorization" in headers:
        if _handle_token_refresh(url, headers, debug):
            if retry_config and timeout_config:
                response = make_http_request_with_retry(
                    "POST",
                    url,
                    headers,
                    data=data,
                    cached_session=cached_session,
                    retry_config=retry_config,
                    timeout_config=timeout_config,
                    debug=debug,
                )
            else:
                if cached_session:
                    response = cached_session.post(
                        url,
                        headers=headers,
                        json=data,
                        timeout=_build_timeout(timeout_config or timeout),
                    )
                else:
                    response = _get_default_sync_client(timeout).post(
                        url,
                        headers=headers,
                        json=data,
                        timeout=_build_timeout(timeout_config or timeout),
                    )

    if debug:
        end_time = time.time()
        logger.debug(
            f"POST request to {url} {data_str} took {end_time - start_time} seconds."
        )
        logger.debug(f"POST response: {response.text}")

    return response


def http_get_json(
    url: str,
    headers: dict[str, str],
    debug: bool = False,
    cached_session: Client | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Any:
    """
    Performs an HTTP GET request and returns the result in JSON format.

    Args:
        url (str): The URL of the request.
        headers (Dict[str, str]): The headers of the request.
        debug (bool): Whether to enable debug mode or not. Default is False.
        cached_session (CachedSession): Cached session to use. Default is None.
        timeout (int): The timeout value in seconds. Default is 20.
        retry_config (RetryConfig): Retry configuration. Default is None.
        timeout_config (TimeoutConfig): Timeout configuration. Default is None.

    Returns:
        Dict[str, Any]: The result of the request in JSON format.
    """
    response = http_get(
        url,
        headers,
        debug=debug,
        cached_session=cached_session,
        timeout=timeout,
        retry_config=retry_config,
        timeout_config=timeout_config,
    )
    response.raise_for_status()
    return to_json_from_response(response)


def http_post_json(
    url: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    debug: bool = False,
    cached_session: Client | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Any:
    """
    Performs an HTTP POST request and returns the result in JSON format.

    Args:
        url (str): The URL of the request.
        headers (Dict[str, str]): The headers of the request.
        data (Dict[str, Any]): The data of the request.
        debug (bool): Whether to enable debug mode or not. Default is False.
        cached_session (CachedSession): Cached session to use. Default is None.
        timeout (int): The timeout value in seconds. Default is 20.
        retry_config (RetryConfig): Retry configuration. Default is None.
        timeout_config (TimeoutConfig): Timeout configuration. Default is None.

    Returns:
        Dict[str, Any]: The result of the request in JSON format.
    """
    filtered_data = {k: v for k, v in data.items() if v is not None} if data else None

    response = http_post(
        url,
        headers,
        filtered_data,
        debug=debug,
        cached_session=cached_session,
        timeout=timeout,
        retry_config=retry_config,
        timeout_config=timeout_config,
    )
    response.raise_for_status()
    return to_json_from_response(response)


async def http_get_async(
    url: str,
    headers: dict[str, str],
    debug: bool = False,
    cached_session: httpx.AsyncClient | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Response:
    """
    Performs an HTTP GET request asynchroniously.
    """
    start_time: float = 0.0
    if debug:
        logger.debug(f"Making async GET request to {url}")
        start_time = time.time()

    # Use retry logic if configured
    if retry_config and timeout_config:
        response = await make_http_request_with_retry_async(
            "GET",
            url,
            headers,
            cached_session=cached_session,
            retry_config=retry_config,
            timeout_config=timeout_config,
            debug=debug,
        )
    else:
        # Fallback to reusable async client to keep connections warm across calls.
        if cached_session:
            response = await cached_session.get(
                url, headers=headers, timeout=_build_timeout(timeout_config or timeout)
            )
        else:
            response = await (await _get_default_async_client(timeout)).get(
                url, headers=headers, timeout=_build_timeout(timeout_config or timeout)
            )

    if response.status_code in (401, 403) and "Authorization" in headers:
        if _handle_token_refresh(url, headers, debug):
            if retry_config and timeout_config:
                response = await make_http_request_with_retry_async(
                    "GET",
                    url,
                    headers,
                    cached_session=cached_session,
                    retry_config=retry_config,
                    timeout_config=timeout_config,
                    debug=debug,
                )
            else:
                if cached_session:
                    response = await cached_session.get(
                        url,
                        headers=headers,
                        timeout=_build_timeout(timeout_config or timeout),
                    )
                else:
                    response = await (await _get_default_async_client(timeout)).get(
                        url,
                        headers=headers,
                        timeout=_build_timeout(timeout_config or timeout),
                    )

    if debug:
        end_time = time.time()
        logger.debug(
            f"Async GET request to {url} took {end_time - start_time} seconds."
        )
        logger.debug(f"Async GET response: {response.text}")

    return response


async def http_get_json_async(
    url: str,
    headers: dict[str, str],
    debug: bool = False,
    cached_session: httpx.AsyncClient | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Any:
    """
    Performs an HTTP GET request and returns the result in JSON format asynchroniously.
    """
    response = await http_get_async(
        url,
        headers,
        debug=debug,
        cached_session=cached_session,
        timeout=timeout,
        retry_config=retry_config,
        timeout_config=timeout_config,
    )
    response.raise_for_status()
    return to_json_from_response(response)


async def http_post_async(
    url: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    debug: bool = False,
    cached_session: httpx.AsyncClient | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Response:
    """
    Performs an HTTP POST request asynchroniously.
    """
    start_time: float = 0.0
    data_str: str = ""
    if debug:
        data_str = ", ".join([f"{k}:{v}" for k, v in data.items()]) if data else ""
        logger.debug(f"Making async POST request to {url} {data_str}")
        start_time = time.time()

    filtered_data = {k: v for k, v in data.items() if v is not None} if data else None

    # Use retry logic if configured
    if retry_config and timeout_config:
        response = await make_http_request_with_retry_async(
            "POST",
            url,
            headers,
            data=filtered_data,
            cached_session=cached_session,
            retry_config=retry_config,
            timeout_config=timeout_config,
            debug=debug,
        )
    else:
        # Fallback to reusable async client to keep connections warm across calls.
        if cached_session:
            response = await cached_session.post(
                url,
                headers=headers,
                json=filtered_data,
                timeout=_build_timeout(timeout_config or timeout),
            )
        else:
            response = await (await _get_default_async_client(timeout)).post(
                url,
                headers=headers,
                json=filtered_data,
                timeout=_build_timeout(timeout_config or timeout),
            )

    if response.status_code in (401, 403) and "Authorization" in headers:
        if _handle_token_refresh(url, headers, debug):
            if retry_config and timeout_config:
                response = await make_http_request_with_retry_async(
                    "POST",
                    url,
                    headers,
                    data=filtered_data,
                    cached_session=cached_session,
                    retry_config=retry_config,
                    timeout_config=timeout_config,
                    debug=debug,
                )
            else:
                if cached_session:
                    response = await cached_session.post(
                        url,
                        headers=headers,
                        json=filtered_data,
                        timeout=_build_timeout(timeout_config or timeout),
                    )
                else:
                    response = await (await _get_default_async_client(timeout)).post(
                        url,
                        headers=headers,
                        json=filtered_data,
                        timeout=_build_timeout(timeout_config or timeout),
                    )

    if debug:
        end_time = time.time()
        logger.debug(
            f"Async POST request to {url} {data_str} took {end_time - start_time} seconds."
        )
        logger.debug(f"Async POST response: {response.text}")

    return response


async def http_post_json_async(
    url: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    debug: bool = False,
    cached_session: httpx.AsyncClient | None = None,
    timeout: int = 20,
    retry_config: RetryConfig | None = None,
    timeout_config: TimeoutConfig | None = None,
) -> Any:
    """
    Performs an HTTP POST request and returns the result in JSON format asynchroniously.
    """
    response = await http_post_async(
        url,
        headers,
        data,
        debug=debug,
        cached_session=cached_session,
        timeout=timeout,
        retry_config=retry_config,
        timeout_config=timeout_config,
    )
    response.raise_for_status()
    return to_json_from_response(response)


def encode_params(params: dict[str, Any]) -> str:
    """
    Encodes the request parameters into a query string.
    Handles array parameters correctly (fields[], etc.)

    Args:
        params (Dict[str, Any]): The request parameters.

    Returns:
        str: The encoded query string.
    """
    # ⚡ Bolt optimization: using urlencode with doseq=True is ~3x faster than manual loop concatenation
    # It correctly handles array parameters (e.g., fields[]) natively in C/optimized Python.
    return urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)


def url_with_params(url: str, params: dict[str, Any]) -> str:
    """
    Adds the request parameters to the URL.

    Args:
        url (str): The URL of the request.
        params (Dict[str, Any]): The request parameters.

    Returns:
        str: The URL with the request parameters.
    """
    if encoded_params := encode_params(params):
        return f"{url}?{encoded_params}"
    else:
        return url
