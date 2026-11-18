"""AZcaptcha — official Python SDK for the AZcaptcha captcha-solving API.

Compatible with the 2Captcha method surface (`solve`, `result`, `balance`,
`report_bad`) and the modern JSON API (`create_task`, `get_task_result`).

Spec: https://github.com/AZcaptcha/sdk-spec (spec-v1.0.0).
"""
from .aio import AsyncAzcaptcha
from .client import Azcaptcha
from .helpers import DEFAULT_TIMEOUTS, image_body, normalise_proxy
from .errors import (
    AuthError,
    BalanceError,
    CapacityError,
    CaptchaError,
    LimitError,
    ModuleError,
    NetworkError,
    PingbackError,
    ProcessingError,
    ProxyError,
    RequestError,
    ResultError,
    ServiceError,
    UnknownError,
    error_for,
)
from .transport import HttpTransport, Transport

__version__ = "1.0.0"
__all__ = [
    "Azcaptcha", "AsyncAzcaptcha", "normalise_proxy", "image_body", "DEFAULT_TIMEOUTS",
    "Transport", "HttpTransport",
    "CaptchaError", "AuthError", "BalanceError", "RequestError", "LimitError", "ProcessingError",
    "CapacityError", "ServiceError", "ResultError", "ProxyError", "PingbackError",
    "ModuleError", "NetworkError", "UnknownError", "error_for",
    "__version__",
]
