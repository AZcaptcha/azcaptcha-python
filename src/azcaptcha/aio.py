"""Async facade — each call runs the sync client in a worker thread."""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional

from .client import SOFT_ID, Azcaptcha
from .transport import Transport


class AsyncAzcaptcha:
    """Drop-in async wrapper: ``await client.solve_turnstile(...)``."""

    def __init__(self, api_key: str, host: str = "https://azcaptcha.com", *,
                 timeout: float = 30.0, transport: Optional[Transport] = None,
                 soft_id: int = SOFT_ID) -> None:
        self._sync = Azcaptcha(api_key, host, timeout=timeout,
                               transport=transport, soft_id=soft_id)

    async def _call(self, name: str, *args: Any, **kwargs: Any) -> Any:
        fn: Callable[..., Any] = getattr(self._sync, name)
        return await asyncio.to_thread(fn, *args, **kwargs)

    async def submit(self, method: str, **params: Any) -> str:
        return await self._call("submit", method, **params)

    async def result(self, task_id: str) -> str:
        return await self._call("result", task_id)

    async def wait_result(self, task_id: str, timeout: Optional[float] = None) -> str:
        return await self._call("wait_result", task_id, timeout=timeout)

    async def balance(self) -> float:
        return await self._call("balance")

    async def report_bad(self, task_id: str) -> bool:
        return await self._call("report_bad", task_id)

    async def create_task(self, task_type: str, **task: Any) -> int:
        return await self._call("create_task", task_type, **task)

    async def get_task_result(self, task_id: int) -> Dict[str, Any]:
        return await self._call("get_task_result", task_id)

    async def wait_task_result(self, task_id: int, timeout: float = 300) -> Dict[str, Any]:
        return await self._call("wait_task_result", task_id, timeout=timeout)

    async def solve(self, method: str, timeout: Optional[float] = None, **params: Any) -> str:
        return await self._call("solve", method, timeout=timeout, **params)

    async def solve_image(self, image: bytes | str, **params: Any) -> str:
        return await self._call("solve_image", image, **params)

    async def solve_recaptcha_v2(self, sitekey: str, pageurl: str, **params: Any) -> str:
        return await self._call("solve_recaptcha_v2", sitekey, pageurl, **params)

    async def solve_recaptcha_v3(self, sitekey: str, pageurl: str, action: str,
                                 min_score: float = 0.6, **params: Any) -> str:
        return await self._call("solve_recaptcha_v3", sitekey, pageurl, action,
                                min_score=min_score, **params)

    async def solve_hcaptcha(self, sitekey: str, pageurl: str, **params: Any) -> str:
        return await self._call("solve_hcaptcha", sitekey, pageurl, **params)

    async def solve_turnstile(self, sitekey: str, pageurl: str, **params: Any) -> str:
        return await self._call("solve_turnstile", sitekey, pageurl, **params)

    async def solve_funcaptcha(self, publickey: str, pageurl: str, **params: Any) -> str:
        return await self._call("solve_funcaptcha", publickey, pageurl, **params)

    async def solve_geetest(self, gt: str, challenge: str, pageurl: str, **params: Any) -> str:
        return await self._call("solve_geetest", gt, challenge, pageurl, **params)
