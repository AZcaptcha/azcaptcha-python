# Contributing

1. Read the contract in [AZcaptcha/sdk-spec](https://github.com/AZcaptcha/sdk-spec).
2. Fixtures under `tests/fixtures/` are copied from the spec repo; a fixture change
   is a spec change — open the issue there first.
3. Run the suite:

```bash
python -m pip install -e ".[test]"
python -m pytest
```

4. Keep changes scoped; add a test for every behaviour change.
5. Releases are cut from tags `vX.Y.Z` by CI (PyPI trusted publishing).
