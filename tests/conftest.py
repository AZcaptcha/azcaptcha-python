"""Shared test doubles — no network, fixtures only."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from azcaptcha.transport import Transport

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text())


class FakeTransport(Transport):
    """Replays canned JSON bodies and records every call."""

    def __init__(self, *responses: Dict[str, Any]) -> None:
        self.responses: List[Dict[str, Any]] = list(responses)
        self.calls: List[tuple] = []

    def _next(self, kind: str, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((kind, path, payload))
        if not self.responses:
            raise AssertionError(f"unexpected call: {kind} {path}")
        return self.responses.pop(0)

    def post_form(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._next("form", path, data)

    def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._next("json", path, payload)

    def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._next("get", path, params)


@pytest.fixture
def fixture():
    return load_fixture
