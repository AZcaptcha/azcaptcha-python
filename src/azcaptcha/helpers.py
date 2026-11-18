"""Parameter helpers shared by the sync and async clients."""
from __future__ import annotations

import base64
import os
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

DEFAULT_TIMEOUTS = {
    "base64": 120, "grid": 120,
    "userrecaptcha": 300, "recaptcha_v3": 300,
    "hcaptcha": 120, "hcaptcha_enterprise": 120,
    "turnstile": 180,
    "funcaptcha": 300, "geetest": 300, "geetest_v4": 300,
    "mtcaptcha": 300, "friendlycaptcha": 300, "altcha": 300,
    "cf_clearance": 300, "aws_waf": 300, "filecrypt": 300,
}

_SCHEMES = {"http": "HTTP", "https": "HTTP", "socks4": "SOCKS4", "socks5": "SOCKS5"}


def normalise_proxy(proxy: str) -> Dict[str, str]:
    """Any accepted proxy spelling -> {proxy, proxytype} fields for the API.

    Accepts ``scheme://user:pass@host:port``, ``host:port:user:pass`` and
    ``user:pass@host:port``. The scheme is never sent in ``proxy`` (upstream
    rejects NS_ERROR_UNKNOWN_PROXY_HOST).
    """
    raw = proxy.strip()
    proxytype = "HTTP"
    if "://" in raw:
        scheme, raw = raw.split("://", 1)
        proxytype = _SCHEMES.get(scheme.lower(), "HTTP")
    parts = raw.split(":")
    if len(parts) == 4 and parts[1].isdigit():
        host, port, user, password = parts
        raw = f"{user}:{password}@{host}:{port}"
    elif "@" not in raw and not urlparse("//" + raw).port:
        raise ValueError("proxy must include a port")
    return {"proxy": raw, "proxytype": proxytype}


def image_body(image: Union[bytes, str]) -> str:
    """Bytes/base64/file-path -> bare base64 (no data: prefix)."""
    if isinstance(image, (bytes, bytearray)):
        return base64.b64encode(bytes(image)).decode()
    value = image.strip()
    if value.startswith("data:") and "," in value:
        return value.split(",", 1)[1]
    if os.path.isfile(value):
        with open(value, "rb") as fh:
            return base64.b64encode(fh.read()).decode()
    return value


def clean(params: Dict[str, Any]) -> Dict[str, Any]:
    """Drop None values so the API sees only provided fields."""
    return {k: v for k, v in params.items() if v is not None}
