"""Public exception hierarchy for FFBB Data Client."""

from __future__ import annotations


class FFBBError(Exception):
    """Base exception for all SDK-specific failures."""


class FFBBHTTPError(FFBBError):
    """HTTP response error returned by an FFBB service."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class FFBBNotFoundError(FFBBHTTPError):
    """Requested FFBB resource does not exist."""


class FFBBAuthenticationError(FFBBHTTPError):
    """FFBB credentials are missing, expired, or rejected."""


class FFBBRateLimitError(FFBBHTTPError):
    """FFBB service rate limit was exceeded."""


class FFBBServerError(FFBBHTTPError):
    """FFBB service returned a server-side error."""


class FFBBTransportError(FFBBError):
    """Request could not reach the FFBB service."""


class FFBBResponseValidationError(FFBBError):
    """FFBB response did not match the expected schema."""