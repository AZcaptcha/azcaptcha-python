"""Modern JSON API plus async facade."""
from __future__ import annotations

import asyncio

import pytest

from azcaptcha import AsyncAzcaptcha, Azcaptcha, ResultError

from conftest import FakeTransport, load_fixture


def test_create_task_fixture():
    fx = load_fixture("modern-create-task")
    transport = FakeTransport(fx["response"]["json"])
    task_id = Azcaptcha("test-key", transport=transport).create_task(
        "RecaptchaV2TaskProxyless",
        websiteURL="https://example.com/login",
        websiteKey="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
    )
    assert task_id == 1234567892
    kind, path, payload = transport.calls[0]
    assert (kind, path) == ("json", "/createTask")
    assert payload["clientKey"] == "test-key"
    assert payload["task"] == fx["request"]["json"]["task"]


def test_get_task_result_fixture():
    fx = load_fixture("modern-task-ready")
    transport = FakeTransport(fx["response"]["json"])
    body = Azcaptcha("test-key", transport=transport).get_task_result(1234567892)
    assert body["status"] == "ready"
    assert body["solution"]["gRecaptchaResponse"] == "03AGdBq26..."


def test_wait_task_result_polls_until_ready():
    transport = FakeTransport(
        {"errorId": 0, "status": "processing"},
        {"errorId": 0, "status": "ready", "solution": {"token": "abc"}},
    )
    sleeps = []
    client = Azcaptcha("test-key", transport=transport, sleep=sleeps.append)
    assert client.wait_task_result(1) == {"token": "abc"}
    assert sleeps == [1.0]


def test_modern_error_raises_typed_error():
    transport = FakeTransport({"errorId": 12, "errorCode": "ERROR_ZERO_BALANCE",
                               "errorDescription": "no funds"})
    with pytest.raises(Exception) as exc:
        Azcaptcha("test-key", transport=transport).create_task("RecaptchaV2TaskProxyless")
    assert exc.value.code == "ERROR_ZERO_BALANCE"


def test_wait_task_result_timeout():
    transport = FakeTransport({"errorId": 0, "status": "processing"})
    client = Azcaptcha("test-key", transport=transport, sleep=lambda _: None)
    with pytest.raises(ResultError):
        client.wait_task_result(1, timeout=0.001)


def test_async_facade_wraps_sync_client():
    fx = load_fixture("modern-task-ready")
    transport = FakeTransport(fx["response"]["json"])
    client = AsyncAzcaptcha("test-key", transport=transport)
    body = asyncio.run(client.get_task_result(1234567892))
    assert body["status"] == "ready"
