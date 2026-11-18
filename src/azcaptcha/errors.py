"""Typed errors mirroring spec/errors.json (spec-v1.0.0).

Every API error code maps to one class here; ``retryable`` mirrors the
taxonomy so callers (and the built-in polling loop) never hardcode codes.
"""
from __future__ import annotations

from typing import Dict, Tuple, Type


class CaptchaError(Exception):
    """Base error. ``code`` is the raw API code when one is available."""

    code = "ERROR_UNKNOWN"
    retryable = False

    def __init__(self, code: str | None = None, message: str | None = None) -> None:
        self.code = code or self.code
        self.message = message or self.code
        super().__init__(self.message)


class AuthError(CaptchaError):
    """Key missing, wrong or account suspended."""


class BalanceError(CaptchaError):
    """Zero balance."""


class RequestError(CaptchaError):
    """Bad parameters, unknown task, invalid sitekey/pageurl."""


class LimitError(CaptchaError):
    """Daily limit exceeded (terminal) or too many threads (retryable)."""


class ProcessingError(CaptchaError):
    """CAPCHA_NOT_READY — the task is still in the queue; poll again."""

    retryable = True


class CapacityError(CaptchaError):
    """No solver slot available — retry with backoff."""

    retryable = True


class ServiceError(CaptchaError):
    """Maintenance / upstream service problem."""


class ResultError(CaptchaError):
    """Task failed: unsolvable, timeout, expired, TTL."""


class ProxyError(CaptchaError):
    """Customer proxy rejected."""


class PingbackError(CaptchaError):
    """Pingback URL not verified."""


class ModuleError(CaptchaError):
    """Native module not trained / access denied."""


class NetworkError(CaptchaError):
    """Transport-level failure — retryable."""

    retryable = True


class UnknownError(CaptchaError):
    """Code not in the taxonomy (forward compatibility)."""


_TABLE: Dict[str, Tuple[Type[CaptchaError], bool]] = {
    "CAPCHA_NOT_READY": (ProcessingError, True),
    "ERROR_KEY_DOES_NOT_EXIST": (AuthError, False),
    "ERROR_ACCOUNT_SUSPENDED": (AuthError, False),
    "ERROR_ZERO_BALANCE": (BalanceError, False),
    "ERROR_BAD_PARAMETERS": (RequestError, False),
    "ERROR_WRONG_ID_FORMAT": (RequestError, False),
    "ERROR_NO_SUCH_CAPCHA_ID": (RequestError, False),
    "ERROR_TASK_NOT_FOUND": (RequestError, False),
    "ERROR_TASK_NOT_SUPPORTED": (RequestError, False),
    "ERROR_WRONG_GOOGLEKEY": (RequestError, False),
    "ERROR_RECAPTCHA_INVALID_SITEKEY": (RequestError, False),
    "ERROR_WRONG_PAGEURL": (RequestError, False),
    "ERROR_IMAGE_NOT_FOUND": (RequestError, False),
    "ERROR_IMAGE_TYPE_NOT_SUPPORTED": (RequestError, False),
    "ERROR_ZERO_CAPTCHA_FILESIZE": (RequestError, False),
    "ERROR_TOO_BIG_CAPTCHA_FILESIZE": (RequestError, False),
    "ERROR_DAILY_LIMIT_EXCEEDED": (LimitError, False),
    "ERROR_TOO_MANY_THREADS": (LimitError, True),
    "ERROR_NO_SLOT_AVAILABLE": (CapacityError, True),
    "ERROR_MAINTENANCE": (ServiceError, False),
    "ERROR_TIMEOUT": (ResultError, False),
    "ERROR_TTL": (ResultError, False),
    "ERROR_TOKEN_EXPIRED": (ResultError, False),
    "ERROR_CAPTCHA_UNSOLVABLE": (ResultError, False),
    "ERROR_PROXY_REQUIRED": (ProxyError, False),
    "ERROR_PROXY_NOT_AUTHORIZED": (ProxyError, False),
    "ERROR_PROXY_BANNED": (ProxyError, False),
    "ERROR_PINGBACK_NOT_VERIFIED": (PingbackError, False),
    "ERROR_MODULE_ACCESS_DENIED": (ModuleError, False),
    "ERROR_MODULE_NOT_TRAINED": (ModuleError, False),
}


def error_for(code: str, message: str | None = None) -> CaptchaError:
    """Instantiate the typed error for an API code."""
    cls, retryable = _TABLE.get(code, (UnknownError, False))
    err = cls(code, message)
    err.retryable = retryable
    return err
