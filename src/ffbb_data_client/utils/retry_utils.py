"""
Retry utilities for FFBB Data Client.

This module provides retry logic with exponential backoff for HTTP requests,
along with configurable timeout management.
"""

import asyncio
import atexit
import secrets
import time
from collections.abc import Callable
from typing import Any, cast
from urllib.parse import urlparse

import httpx
from httpx import Client, Response

from .secure_logging import get_secure_logger

logger = get_secure_logger(__name__)

_DEFAULT_CLIENT: httpx.Client | None = None
_DEFAULT_ASYNC_CLIENT: httpx.AsyncClient | None = None

# ⚡ Performance optimization: Connection limits to keep TLS sockets warm across calls
_POOL_LIMITS = httpx.Limits(max_keepalive_connections=50, max_connections=200)
_ALLOWED_SCHEMES = frozenset({"http", "https"})


def _validate_url(url: str) -> str:
    """Validate, sanitize and reconstruct URL to prevent SSRF (CWE-918)."""
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")
    parsed = urlparse(url.strip())
    if parsed.scheme not in _ALLOWED_SCHEMES or not parsed.netloc:
        raise ValueError(f"Invalid URL target: '{url}'")
    path = parsed.path or "/"
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{parsed.scheme}://{parsed.netloc}{path}{query}"


def _get_default_client() -> httpx.Client:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None or _DEFAULT_CLIENT.is_closed:
        _DEFAULT_CLIENT = httpx.Client(limits=_POOL_LIMITS)
    return _DEFAULT_CLIENT


async def _get_default_async_client() -> httpx.AsyncClient:
    global _DEFAULT_ASYNC_CLIENT
    if _DEFAULT_ASYNC_CLIENT is None or _DEFAULT_ASYNC_CLIENT.is_closed:
        _DEFAULT_ASYNC_CLIENT = httpx.AsyncClient(limits=_POOL_LIMITS)
    return _DEFAULT_ASYNC_CLIENT


def close_default_clients() -> None:
    """Close module-level fallback clients synchronously."""
    global _DEFAULT_CLIENT, _DEFAULT_ASYNC_CLIENT
    if _DEFAULT_CLIENT is not None and not _DEFAULT_CLIENT.is_closed:
        _DEFAULT_CLIENT.close()
    _DEFAULT_CLIENT = None
    _DEFAULT_ASYNC_CLIENT = None


async def aclose_default_clients() -> None:
    """Close module-level fallback clients asynchronously."""
    global _DEFAULT_CLIENT, _DEFAULT_ASYNC_CLIENT
    if _DEFAULT_ASYNC_CLIENT is not None and not _DEFAULT_ASYNC_CLIENT.is_closed:
        await _DEFAULT_ASYNC_CLIENT.aclose()
    if _DEFAULT_CLIENT is not None and not _DEFAULT_CLIENT.is_closed:
        _DEFAULT_CLIENT.close()
    _DEFAULT_CLIENT = None
    _DEFAULT_ASYNC_CLIENT = None


atexit.register(close_default_clients)


class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts.
        base_delay: Base delay in seconds between retries.
        max_delay: Maximum delay between retries.
        backoff_factor: Exponential backoff multiplier.
        jitter: Whether to add random jitter to delays.
        retry_on_status_codes: HTTP status codes to retry on.
        retry_on_exceptions: Exception types to retry on.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_status_codes: list[int] | None = None,
        retry_on_exceptions: tuple[type[Exception], ...] | None = None,
    ) -> None:
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts.
            base_delay: Base delay in seconds between retries.
            max_delay: Maximum delay between retries.
            backoff_factor: Exponential backoff multiplier.
            jitter: Whether to add random jitter to delays.
            retry_on_status_codes: HTTP status codes to retry on.
            retry_on_exceptions: Exception types to retry on.
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_on_status_codes = retry_on_status_codes or [429, 500, 502, 503, 504]
        self.retry_on_exceptions = retry_on_exceptions or (
            httpx.RequestError,
            ConnectionError,
            TimeoutError,
        )


class TimeoutConfig:
    """
    Configuration for timeout behavior.

    Attributes:
        connect_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.
        total_timeout: Total request timeout in seconds.
    """

    def __init__(
        self,
        connect_timeout: float = 10.0,
        read_timeout: float = 30.0,
        total_timeout: float | None = None,
    ) -> None:
        """
        Initialize timeout configuration.

        Args:
            connect_timeout: Connection timeout in seconds.
            read_timeout: Read timeout in seconds.
            total_timeout: Total request timeout in seconds (overrides connect+read if set).
        """
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.total_timeout = total_timeout or (connect_timeout + read_timeout)


# Default configurations
DEFAULT_RETRY_CONFIG = RetryConfig()
DEFAULT_TIMEOUT_CONFIG = TimeoutConfig()


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for the given retry attempt.

    Args:
        attempt: Current attempt number (0-based).
        config: Retry configuration.

    Returns:
        Delay in seconds.
    """
    delay = config.base_delay * (config.backoff_factor**attempt)
    delay = min(delay, config.max_delay)

    if config.jitter:
        # Add random jitter (±25% of delay)
        jitter_range = delay * 0.25
        delay += secrets.SystemRandom().uniform(-jitter_range, jitter_range)
        delay = max(0.1, delay)  # Minimum 100ms delay

    return delay


def should_retry(
    attempt: int,
    response: Response | None,
    exception: Exception | None,
    config: RetryConfig,
) -> bool:
    """
    Determine if a request should be retried.

    Args:
        attempt: Current attempt number (0-based).
        response: HTTP response (if any).
        exception: Exception that occurred (if any).
        config: Retry configuration.

    Returns:
        True if request should be retried.
    """
    # Retry on exceptions
    if exception and isinstance(exception, config.retry_on_exceptions):
        return True

    # Retry on specific status codes
    if (
        response
        and hasattr(response, "status_code")
        and response.status_code in config.retry_on_status_codes
    ):
        return True

    return False


def execute_with_retry(
    func: Callable[..., Response],
    *args: Any,
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
    timeout_config: TimeoutConfig = DEFAULT_TIMEOUT_CONFIG,
    **kwargs: Any,
) -> Response:
    """
    Execute a function with retry logic.

    Args:
        func: Function to execute (should return a Response object).
        *args: Positional arguments for the function.
        config: Retry configuration.
        timeout_config: Timeout configuration.
        **kwargs: Keyword arguments for the function.

    Returns:
        The HTTP response.

    Raises:
        Exception: The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None

    # Update timeout in kwargs if not already set
    if "timeout" not in kwargs:
        kwargs["timeout"] = timeout_config.total_timeout

    for attempt in range(config.max_attempts + 1):
        try:
            response = func(*args, **kwargs)

            # Check if we should retry based on response
            if should_retry(attempt, response, None, config):
                if attempt < config.max_attempts:
                    delay = calculate_delay(attempt, config)
                    time.sleep(delay)
                    continue

            return response

        except (
            httpx.RequestError,
            ConnectionError,
            TimeoutError,
            OSError,
        ) as e:
            last_exception = e

            # Check if we should retry based on exception
            if should_retry(attempt, None, e, config):
                if attempt < config.max_attempts:
                    delay = calculate_delay(attempt, config)
                    time.sleep(delay)
                    continue
            # Don't retry this type of exception
            raise

    # All retries exhausted
    if last_exception:
        raise last_exception

    # This should never happen, but just in case
    raise RuntimeError("Retry logic failed unexpectedly")


def make_http_request_with_retry(
    method: str,
    url: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    cached_session: Client | None = None,
    retry_config: RetryConfig = DEFAULT_RETRY_CONFIG,
    timeout_config: TimeoutConfig = DEFAULT_TIMEOUT_CONFIG,
    debug: bool = False,
) -> Response:
    """
    Make an HTTP request with retry logic.

    Args:
        method: HTTP method ('GET', 'POST', etc.).
        url: Request URL.
        headers: Request headers.
        data: Request data (for POST requests).
        cached_session: Cached session to use.
        retry_config: Retry configuration.
        timeout_config: Timeout configuration.
        debug: Whether to enable debug logging.

    Returns:
        HTTP response.
    """

    url = _validate_url(url)

    def _make_request(**_kwargs: Any) -> Response:
        if debug:
            logger.debug(f"Making {method} request to {url}")

        if cached_session:
            if method.upper() == "GET":
                return cached_session.get(
                    url, headers=headers, timeout=timeout_config.total_timeout
                )
            elif method.upper() == "POST":
                return cached_session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=timeout_config.total_timeout,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        else:
            session = _get_default_client()
            if method.upper() == "GET":
                return session.get(
                    url, headers=headers, timeout=timeout_config.total_timeout
                )
            elif method.upper() == "POST":
                return session.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=timeout_config.total_timeout,
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

    return execute_with_retry(
        _make_request, config=retry_config, timeout_config=timeout_config
    )


async def execute_with_retry_async(
    func: Callable[..., Any],
    *args: Any,
    config: RetryConfig = DEFAULT_RETRY_CONFIG,
    timeout_config: TimeoutConfig = DEFAULT_TIMEOUT_CONFIG,
    **kwargs: Any,
) -> Any:
    """
    Execute an async function with retry logic.

    Args:
        func: Async function to execute.
        *args: Positional arguments for the function.
        config: Retry configuration.
        timeout_config: Timeout configuration.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function.

    Raises:
        Exception: The last exception if all retries are exhausted.
    """
    last_exception: Exception | None = None

    # Update timeout in kwargs if not already set
    if "timeout" not in kwargs:
        kwargs["timeout"] = timeout_config.total_timeout

    for attempt in range(config.max_attempts + 1):
        try:
            response = await func(*args, **kwargs)

            # Check if we should retry based on response
            if should_retry(
                attempt,
                response if isinstance(response, Response) else None,
                None,
                config,
            ):
                if attempt < config.max_attempts:
                    delay = calculate_delay(attempt, config)
                    await asyncio.sleep(delay)
                    continue

            return response

        except (
            httpx.RequestError,
            ConnectionError,
            TimeoutError,
            OSError,
        ) as e:
            last_exception = e

            # Check if we should retry based on exception
            if should_retry(attempt, None, e, config):
                if attempt < config.max_attempts:
                    delay = calculate_delay(attempt, config)
                    await asyncio.sleep(delay)
                    continue
            # Don't retry this type of exception
            raise

    # All retries exhausted
    if last_exception:
        raise last_exception

    # This should never happen, but just in case
    raise RuntimeError("Retry logic failed unexpectedly")


async def make_http_request_with_retry_async(
    method: str,
    url: str,
    headers: dict[str, str],
    data: dict[str, Any] | None = None,
    cached_session: httpx.AsyncClient | None = None,
    retry_config: RetryConfig = DEFAULT_RETRY_CONFIG,
    timeout_config: TimeoutConfig = DEFAULT_TIMEOUT_CONFIG,
    debug: bool = False,
) -> Response:
    """
    Make an async HTTP request with retry logic.

    Args:
        method: HTTP method ('GET', 'POST', etc.).
        url: Request URL.
        headers: Request headers.
        data: Request data (for POST requests).
        cached_session: Async cached session to use.
        retry_config: Retry configuration.
        timeout_config: Timeout configuration.
        debug: Whether to enable debug logging.

    Returns:
        HTTP response.
    """

    url = _validate_url(url)

    async def _make_request(**_kwargs: Any) -> Response:
        if debug:
            logger.debug(f"Making async {method} request to {url}")

        session: httpx.AsyncClient
        if cached_session:
            session = cached_session
        else:
            session = await _get_default_async_client()

        if method.upper() == "GET":
            return await session.get(
                url, headers=headers, timeout=timeout_config.total_timeout
            )
        elif method.upper() == "POST":
            return await session.post(
                url,
                headers=headers,
                json=data,
                timeout=timeout_config.total_timeout,
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    return cast(
        Response,
        await execute_with_retry_async(
            _make_request, config=retry_config, timeout_config=timeout_config
        ),
    )


# Convenience functions for backward compatibility
def get_default_retry_config() -> RetryConfig:
    """Get default retry configuration."""
    return DEFAULT_RETRY_CONFIG


def get_default_timeout_config() -> TimeoutConfig:
    """Get default timeout configuration."""
    return DEFAULT_TIMEOUT_CONFIG


def create_custom_retry_config(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> RetryConfig:
    """
    Create a custom retry configuration.

    Args:
        max_attempts: Maximum number of retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.

    Returns:
        Custom retry configuration.
    """
    return RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
    )


def create_custom_timeout_config(
    connect_timeout: float = 10.0,
    read_timeout: float = 30.0,
) -> TimeoutConfig:
    """
    Create a custom timeout configuration.

    Args:
        connect_timeout: Connection timeout in seconds.
        read_timeout: Read timeout in seconds.

    Returns:
        Custom timeout configuration.
    """
    return TimeoutConfig(
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
    )
