"""Proxy and image parameter normalisation."""
from __future__ import annotations

import base64

import pytest

from azcaptcha.helpers import image_body, normalise_proxy


def test_proxy_host_port():
    assert normalise_proxy("1.2.3.4:8080") == {"proxy": "1.2.3.4:8080", "proxytype": "HTTP"}


def test_proxy_userinfo():
    out = normalise_proxy("user:pass@1.2.3.4:8080")
    assert out == {"proxy": "user:pass@1.2.3.4:8080", "proxytype": "HTTP"}


def test_proxy_host_port_user_pass_is_reordered():
    out = normalise_proxy("1.2.3.4:8080:user:pass")
    assert out["proxy"] == "user:pass@1.2.3.4:8080"


@pytest.mark.parametrize("scheme,expected", [
    ("http", "HTTP"), ("https", "HTTP"), ("socks4", "SOCKS4"), ("socks5", "SOCKS5"),
])
def test_proxy_scheme_never_sent(scheme, expected):
    out = normalise_proxy(f"{scheme}://user:pass@1.2.3.4:1080")
    assert out["proxy"] == "user:pass@1.2.3.4:1080"
    assert out["proxytype"] == expected


def test_proxy_without_port_rejected():
    with pytest.raises(ValueError):
        normalise_proxy("1.2.3.4")


def test_image_bytes():
    assert image_body(b"\x89PNG") == base64.b64encode(b"\x89PNG").decode()


def test_image_data_uri():
    assert image_body("data:image/png;base64,AAAA") == "AAAA"


def test_image_file(tmp_path):
    path = tmp_path / "captcha.png"
    path.write_bytes(b"\x89PNG")
    assert image_body(str(path)) == base64.b64encode(b"\x89PNG").decode()


def test_image_passthrough():
    assert image_body("iVBORw0KGgo=") == "iVBORw0KGgo="
