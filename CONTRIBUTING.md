# Contributing

Thank you for improving FableLayer.

## Ground rules

- Do not submit private, proprietary, or leaked prompt text.
- Do not add performance claims without benchmark raw data and limitations.
- Keep runtime dependencies at zero unless a proposal justifies the trade-off.
- Add or update tests for behavior changes.

## Before opening a PR

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

## Source additions

Any new upstream source must update `ATTRIBUTION.md` and, if used by runtime code, the source policy tests.
