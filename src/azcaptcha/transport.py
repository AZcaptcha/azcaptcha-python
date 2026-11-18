"""HTTP transport — stdlib only, injectable for tests."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from .errors import NetworkError, ServiceError

USER_AGENT = "azcaptcha-python/1.0.0"


class Transport:
    """Minimal interface the client needs; tests provide a fake."""

    def post_form(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class HttpTransport(Transport):
    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, req: urllib.request.Request) -> Dict[str, Any]:
        req.add_header("User-Agent", USER_AGENT)
        req.add_header("Accept", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                raw = res.read().decode("utf-8", "replace")
                status = res.status
        except urllib.error.HTTPError as exc:  # 4xx/5xx still carry JSON bodies
            raw = exc.read().decode("utf-8", "replace")
            status = exc.code
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise NetworkError("ERROR_NETWORK", str(exc)) from exc

        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ServiceError("ERROR_BAD_RESPONSE", raw[:200]) from exc
        if not isinstance(body, dict):
            raise ServiceError("ERROR_BAD_RESPONSE", "unexpected payload")
        if status >= 500:
            raise ServiceError("ERROR_HTTP_5XX", f"HTTP {status}")
        return body

    def post_form(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = urllib.parse.urlencode({k: v for k, v in data.items() if v is not None})
        req = urllib.request.Request(
            self.base_url + path,
            data=payload.encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        return self._request(req)

    def post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return self._request(req)

    def get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        req = urllib.request.Request(self.base_url + path + "?" + query, method="GET")
        return self._request(req)
