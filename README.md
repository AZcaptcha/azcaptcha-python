# AZcaptcha Python SDK

Official Python client for [AZcaptcha](https://azcaptcha.com) — image captchas,
reCAPTCHA v2/v3, hCaptcha, Cloudflare Turnstile, FunCaptcha, GeeTest and more.

- Sync (`Azcaptcha`) and async (`AsyncAzcaptcha`) clients.
- 2Captcha-compatible method surface, so existing scripts migrate by changing
  the key and host.
- Typed exceptions for every API error code
  ([spec-v1.0.0](https://github.com/AZcaptcha/sdk-spec)).
- Polling with the contract delays and per-type deadlines built in.
- Zero runtime dependencies (stdlib `urllib`), Python 3.9+.

## Install

```bash
pip install azcaptcha
```

## Quickstart

```python
from azcaptcha import Azcaptcha

client = Azcaptcha("YOUR_API_KEY")

# reCAPTCHA v2
token = client.solve_recaptcha_v2(
    sitekey="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
    pageurl="https://example.com/login",
)
print(token)

# Image captcha (bytes, base64 string, data: URI or file path)
answer = client.solve_image("captcha.png")

# hCaptcha / Turnstile
token = client.solve_hcaptcha("SITEKEY", "https://example.com/")
token = client.solve_turnstile("0x4AAAAAAA...", "https://example.com/")
```

### Low-level (2Captcha style)

```python
task_id = client.submit("userrecaptcha", googlekey="SITEKEY", pageurl="https://example.com/")
token = client.wait_result(task_id, timeout=300)  # polls 1s then every 5s
```

### Modern JSON API

```python
task_id = client.create_task(
    "RecaptchaV2TaskProxyless",
    websiteURL="https://example.com/login",
    websiteKey="SITEKEY",
)
solution = client.wait_task_result(task_id)
print(solution["gRecaptchaResponse"])
```

### Async

```python
import asyncio
from azcaptcha import AsyncAzcaptcha

async def main():
    client = AsyncAzcaptcha("YOUR_API_KEY")
    tokens = await asyncio.gather(
        client.solve_turnstile("0x4AAA...", "https://a.example/"),
        client.solve_hcaptcha("SITEKEY", "https://b.example/"),
    )

asyncio.run(main())
```

## Proxies

Pass any accepted spelling as `proxy=`; the SDK normalises it and never sends the
scheme upstream (`NS_ERROR_UNKNOWN_PROXY_HOST` risk):

```python
client.solve_recaptcha_v2(sitekey, pageurl,
                          proxy="socks5://user:pass@1.2.3.4:1080")
client.solve_recaptcha_v2(sitekey, pageurl,
                          proxy="1.2.3.4:1080:user:pass")
```

`proxytype` defaults from the scheme (`http`/`https` → `HTTP`, `socks4`,
`socks5`); override with `proxytype="SOCKS5"`.

## Errors

Every API code maps to a typed exception; `retryable` mirrors the shared
taxonomy:

```python
from azcaptcha import BalanceError, CapacityError, ResultError

try:
    token = client.solve_turnstile(sitekey, pageurl)
except BalanceError:
    ...
except CapacityError:      # ERROR_NO_SLOT_AVAILABLE — retry with backoff
    ...
except ResultError:        # unsolvable / timeout / expired
    ...
```

`wait_result` retries only codes marked `retryable` (slot pressure, thread
limit) and backs off 10s ×1.5 up to 60s. Non-retryable codes raise immediately.

## Timeouts

Defaults follow server settings: image 120s, hCaptcha 120s, Turnstile 180s,
reCAPTCHA and others 300s. Override per call: `solve(..., timeout=600)` or
`solve_turnstile(..., timeout=90)`.

## Reporting bad solutions

```python
client.report_bad(task_id)
```

## Soft id

`soft_id` defaults to `0` (omitted). Once AZcaptcha assigns one it ships in the
next release and is sent automatically for upstream attribution.

## Links

- API contract: <https://github.com/AZcaptcha/sdk-spec>
- Docs: <https://azcaptcha.com/docs>
- Python guide: <https://azcaptcha.com/lang/python>
- Changelog: [CHANGELOG.md](CHANGELOG.md)

## License

MIT — see [LICENSE](LICENSE).
