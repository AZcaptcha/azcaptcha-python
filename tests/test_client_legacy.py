"""Legacy API behaviour, replayed against spec fixtures."""
from __future__ import annotations

import pytest

from azcaptcha import (
    AuthError, Azcaptcha, BalanceError, CapacityError, ProcessingError, ResultError,
)
from azcaptcha.client import NOT_READY

from conftest import FakeTransport, load_fixture


def client(transport, **kwargs):
    return Azcaptcha("test-key", transport=transport, **kwargs)


def test_submit_image_fixture():
    fx = load_fixture("submit-image")
    transport = FakeTransport(fx["response"]["json"], {"status": 1, "request": "wxyz"})
    assert client(transport).solve_image(b"\x89PNG") == "wxyz"
    kind, path, form = transport.calls[0]
    assert (kind, path) == ("form", "/in.php")
    assert form["method"] == "base64"
    assert form["key"] == "test-key"
    assert form["json"] == "1"
    assert form["body"] == "iVBORw=="  # b"\x89PNG" base64


def test_submit_recaptcha_v2_fixture():
    fx = load_fixture("submit-recaptcha-v2")
    transport = FakeTransport(fx["response"]["json"])
    task_id = client(transport).submit(
        "userrecaptcha",
        googlekey="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
        pageurl="https://example.com/login",
    )
    assert task_id == "1234567891"
    form = transport.calls[0][2]
    assert form["method"] == "userrecaptcha"
    assert form["googlekey"] == "6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
    assert form["pageurl"] == "https://example.com/login"
    assert "soft_id" not in form  # zero soft id is omitted


def test_soft_id_sent_when_configured():
    transport = FakeTransport({"status": 1, "request": "1"})
    client(transport, soft_id=4242).submit("base64", body="AA==")
    assert transport.calls[0][2]["soft_id"] == 4242


def test_proxy_fields_normalised():
    transport = FakeTransport({"status": 1, "request": "1"})
    client(transport).submit("turnstile", sitekey="0x4AAA", pageurl="https://e.com",
                             proxy="socks5://u:p@1.2.3.4:1080")
    form = transport.calls[0][2]
    assert form["proxy"] == "u:p@1.2.3.4:1080"
    assert form["proxytype"] == "SOCKS5"


def test_zero_balance_fixture_raises_typed_error():
    fx = load_fixture("error-zero-balance")
    transport = FakeTransport(fx["response"]["json"])
    with pytest.raises(BalanceError) as exc:
        client(transport).submit("userrecaptcha", googlekey="k", pageurl="https://e.com")
    assert exc.value.code == "ERROR_ZERO_BALANCE"
    assert exc.value.retryable is False


def test_no_slot_fixture_is_retryable_capacity_error():
    fx = load_fixture("error-no-slot")
    transport = FakeTransport(fx["response"]["json"])
    with pytest.raises(CapacityError) as exc:
        client(transport).submit("turnstile", sitekey="k", pageurl="https://e.com")
    assert exc.value.code == "ERROR_NO_SLOT_AVAILABLE"
    assert exc.value.retryable is True


def test_poll_ready_fixture():
    fx = load_fixture("poll-ready-recaptcha")
    transport = FakeTransport(fx["response"]["json"])
    assert client(transport).result("1234567891") == "03AGdBq26..."


def test_poll_processing_fixture_raises_not_ready():
    fx = load_fixture("poll-processing")
    transport = FakeTransport(fx["response"]["json"])
    with pytest.raises(ProcessingError) as exc:
        client(transport).result("1234567891")
    assert exc.value.code == NOT_READY
    assert exc.value.retryable is True


def test_wait_result_polls_with_contract_delays():
    transport = FakeTransport(
        load_fixture("poll-processing")["response"]["json"],
        load_fixture("poll-ready-recaptcha")["response"]["json"],
    )
    sleeps = []
    value = client(transport, sleep=sleeps.append).wait_result("1234567891")
    assert value == "03AGdBq26..."
    assert sleeps == [1.0]  # initial delay, then 5s interval


def test_wait_result_backs_off_on_no_slot():
    transport = FakeTransport(
        {"status": 0, "request": "ERROR_NO_SLOT_AVAILABLE"},
        {"status": 1, "request": "token"},
    )
    sleeps = []
    assert client(transport, sleep=sleeps.append).wait_result("1") == "token"
    assert sleeps == [10.0]


def test_wait_result_raises_non_retryable_immediately():
    transport = FakeTransport({"status": 0, "request": "ERROR_CAPTCHA_UNSOLVABLE"})
    with pytest.raises(ResultError):
        client(transport).wait_result("1")


def test_wait_result_timeout():
    transport = FakeTransport({"status": 0, "request": NOT_READY})
    with pytest.raises(ResultError) as exc:
        client(transport, sleep=lambda _: None).wait_result("1", timeout=0.001)
    assert exc.value.code == "ERROR_TIMEOUT"


def test_balance():
    transport = FakeTransport({"status": 1, "request": 12.5})
    assert client(transport).balance() == 12.5


def test_report_bad():
    transport = FakeTransport({"status": 1, "request": "OK_REPORT_RECORDED"})
    assert client(transport).report_bad("123") is True


def test_missing_key_rejected():
    with pytest.raises(AuthError):
        Azcaptcha("")
