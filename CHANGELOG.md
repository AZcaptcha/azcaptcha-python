# Changelog

## 1.0.0 — 2026-11-18

- Initial release against `spec-v1.0.0`.
- Sync `Azcaptcha` and async `AsyncAzcaptcha` clients.
- Legacy API (`in.php`/`res.php`) and modern API (`createTask`/`getTaskResult`).
- Typed errors for all 30 taxonomy codes; contract polling with `NO_SLOT` backoff.
- Helpers: image captcha, reCAPTCHA v2/v3, hCaptcha, Turnstile, FunCaptcha, GeeTest.
- Proxy normalisation for all accepted spellings.
