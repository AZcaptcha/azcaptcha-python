"""AZcaptcha sync client — legacy (in.php/res.php) + modern (createTask) APIs.

Contract: https://github.com/AZcaptcha/sdk-spec (spec-v1.0.0).
"""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, Mapping, Optional

from .errors import CapacityError, LimitError, ProcessingError, ResultError, error_for
from .helpers import DEFAULT_TIMEOUTS, clean, image_body, normalise_proxy
from .transport import HttpTransport, Transport

SOFT_ID = 0  # assigned AZcaptcha soft id; omitted while 0
POLL_INTERVAL = 5.0
FIRST_DELAY = 1.0
NO_SLOT_BACKOFF = 10.0
NOT_READY = "CAPCHA_NOT_READY"


class Azcaptcha:
    """Synchronous client. Safe to share across threads."""

    def __init__(self, api_key: str, host: str = "https://azcaptcha.com", *,
                 timeout: float = 30.0, transport: Optional[Transport] = None,
                 soft_id: int = SOFT_ID, sleep: Callable[[float], None] = time.sleep) -> None:
        if not api_key:
            raise error_for("ERROR_KEY_DOES_NOT_EXIST", "api_key is required")
        self.api_key = api_key
        self.soft_id = soft_id
        self._sleep = sleep
        self._http = transport or HttpTransport(host, timeout)

    # ── legacy API ────────────────────────────────────────────────────
    def submit(self, method: str, **params: Any) -> str:
        form: Dict[str, Any] = {"key": self.api_key, "method": method, "json": "1"}
        if self.soft_id:
            form["soft_id"] = self.soft_id
        if params.get("proxy"):
            form.update(normalise_proxy(str(params.pop("proxy"))))
        if params.get("proxytype"):
            form["proxytype"] = str(params.pop("proxytype")).upper()
        form.update(clean(params))
        return self._unwrap(self._http.post_form("/in.php", form), "submit")

    def result(self, task_id: str) -> str:
        body = self._http.get("/res.php", {"key": self.api_key, "action": "get",
                                           "id": str(task_id), "json": "1"})
        if str(body.get("request") or "") == NOT_READY:
            raise ProcessingError(NOT_READY)
        return self._unwrap(body, "result")

    def wait_result(self, task_id: str, timeout: Optional[float] = None,
                    poll_interval: float = POLL_INTERVAL) -> str:
        """Poll until ready, backing off harder while slots are exhausted.

        Raises the typed error for any non-retryable code, and ResultError
        (``ERROR_TIMEOUT``) once the deadline passes.
        """
        limit = float(timeout or 300)
        deadline = time.monotonic() + limit
        delay = FIRST_DELAY
        backoff = NO_SLOT_BACKOFF
        while True:
            try:
                return self.result(task_id)
            except ProcessingError:
                pause, delay = delay, poll_interval
            except CapacityError:
                pause, backoff = backoff, min(backoff * 1.5, 60.0)
            except LimitError as exc:
                if not exc.retryable:
                    raise
                pause, backoff = backoff, min(backoff * 1.5, 60.0)
            if time.monotonic() + pause >= deadline:
                raise ResultError("ERROR_TIMEOUT", f"task {task_id} not ready in {limit:g}s")
            self._sleep(pause)

    def balance(self) -> float:
        body = self._http.get("/res.php", {"key": self.api_key, "action": "getbalance", "json": "1"})
        return float(self._unwrap(body, "balance"))

    def report_bad(self, task_id: str) -> bool:
        body = self._http.get("/res.php", {"key": self.api_key, "action": "reportbad",
                                           "id": str(task_id), "json": "1"})
        return self._unwrap(body, "reportbad").upper().startswith("OK")

    # ── modern API ────────────────────────────────────────────────────
    def create_task(self, task_type: str, **task: Any) -> int:
        payload: Dict[str, Any] = {"clientKey": self.api_key, "task": {"type": task_type, **clean(task)}}
        if self.soft_id:
            payload["softId"] = self.soft_id
        body = self._http.post_json("/createTask", payload)
        self._raise_modern(body)
        return int(body.get("taskId", 0))

    def get_task_result(self, task_id: int) -> Dict[str, Any]:
        body = self._http.post_json("/getTaskResult", {"clientKey": self.api_key, "taskId": task_id})
        self._raise_modern(body)
        return body

    def wait_task_result(self, task_id: int, timeout: float = 300,
                         poll_interval: float = POLL_INTERVAL) -> Dict[str, Any]:
        deadline = time.monotonic() + float(timeout)
        delay = FIRST_DELAY
        while True:
            body = self.get_task_result(task_id)
            if body.get("status") == "ready":
                return body.get("solution") or {}
            if time.monotonic() + delay >= deadline:
                raise ResultError("ERROR_TIMEOUT", f"modern task {task_id} not ready")
            self._sleep(delay)
            delay = poll_interval

    # ── helpers ───────────────────────────────────────────────────────
    def solve(self, method: str, timeout: Optional[float] = None, **params: Any) -> str:
        task_id = self.submit(method, **params)
        return self.wait_result(task_id, timeout=timeout or DEFAULT_TIMEOUTS.get(method, 300))

    def solve_image(self, image: bytes | str, **params: Any) -> str:
        return self.solve("base64", body=image_body(image), **params)

    def solve_recaptcha_v2(self, sitekey: str, pageurl: str, *, invisible: bool = False,
                           enterprise: bool = False, **params: Any) -> str:
        return self.solve("userrecaptcha", googlekey=sitekey, pageurl=pageurl,
                          invisible=1 if invisible else None,
                          enterprise=1 if enterprise else None, **params)

    def solve_recaptcha_v3(self, sitekey: str, pageurl: str, action: str,
                           min_score: float = 0.6, **params: Any) -> str:
        return self.solve("userrecaptcha", googlekey=sitekey, pageurl=pageurl, version="v3",
                          action=action, min_score=min_score, **params)

    def solve_hcaptcha(self, sitekey: str, pageurl: str, **params: Any) -> str:
        return self.solve("hcaptcha", sitekey=sitekey, pageurl=pageurl, **params)

    def solve_turnstile(self, sitekey: str, pageurl: str, **params: Any) -> str:
        return self.solve("turnstile", sitekey=sitekey, pageurl=pageurl, **params)

    def solve_funcaptcha(self, publickey: str, pageurl: str, **params: Any) -> str:
        return self.solve("funcaptcha", publickey=publickey, pageurl=pageurl, **params)

    def solve_geetest(self, gt: str, challenge: str, pageurl: str, **params: Any) -> str:
        return self.solve("geetest", gt=gt, challenge=challenge, pageurl=pageurl, **params)

    # ── internals ─────────────────────────────────────────────────────
    def _unwrap(self, body: Mapping[str, Any], action: str) -> str:
        request = body.get("request")
        if str(request or "").startswith("ERROR_"):
            raise error_for(str(request))
        if int(body.get("status", 0)) != 1:
            raise error_for(str(request or f"ERROR_{action.upper()}_FAILED"))
        return str(request if request is not None else "")

    @staticmethod
    def _raise_modern(body: Mapping[str, Any]) -> None:
        if int(body.get("errorId", 0)):
            raise error_for(str(body.get("errorCode") or "ERROR_UNKNOWN"),
                            str(body.get("errorDescription") or ""))
