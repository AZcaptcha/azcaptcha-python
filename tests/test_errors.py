"""Taxonomy contract: every code in spec/errors.json is mapped and typed."""
from __future__ import annotations

import json
from pathlib import Path

from azcaptcha.errors import (
    AuthError, BalanceError, CapacityError, CaptchaError, LimitError, ModuleError,
    PingbackError, ProxyError, RequestError, ResultError, ServiceError,
    UnknownError, error_for,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _taxonomy():
    return json.loads((FIXTURES / "errors.json").read_text())


def test_every_spec_code_maps_to_typed_error():
    data = _taxonomy()
    codes = list(data["errors"]) + list(data["envelope_codes"])
    for code in codes:
        err = error_for(code)
        assert not isinstance(err, UnknownError), code
        assert err.code == code


def test_retryable_flags_match_spec():
    data = _taxonomy()
    for code, meta in data["errors"].items():
        assert error_for(code).retryable is meta["retryable"], code
    for code, meta in data["envelope_codes"].items():
        assert error_for(code).retryable is meta["retryable"], code


def test_unknown_code_is_forward_compatible():
    err = error_for("ERROR_FROM_THE_FUTURE")
    assert isinstance(err, UnknownError)
    assert err.retryable is False


def test_category_classes():
    assert isinstance(error_for("ERROR_KEY_DOES_NOT_EXIST"), AuthError)
    assert isinstance(error_for("ERROR_ZERO_BALANCE"), BalanceError)
    assert isinstance(error_for("ERROR_BAD_PARAMETERS"), RequestError)
    assert isinstance(error_for("ERROR_TOO_MANY_THREADS"), LimitError)
    assert isinstance(error_for("ERROR_NO_SLOT_AVAILABLE"), CapacityError)
    assert isinstance(error_for("ERROR_MAINTENANCE"), ServiceError)
    assert isinstance(error_for("ERROR_CAPTCHA_UNSOLVABLE"), ResultError)
    assert isinstance(error_for("ERROR_PROXY_BANNED"), ProxyError)
    assert isinstance(error_for("ERROR_PINGBACK_NOT_VERIFIED"), PingbackError)
    assert isinstance(error_for("ERROR_MODULE_NOT_TRAINED"), ModuleError)
    assert issubclass(CaptchaError, Exception)
