<!-- Thank you for improving FableLayer. Keep changes public-safe and evidence-backed. -->

## What changed

<!-- One or two sentences describing the change. -->

## Why

<!-- The problem this solves or the behavior it changes. -->

## Evidence (required before merge)

Paste the exit codes / output. Claims of "done" without evidence are rejected by policy.

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

- [ ] Tests pass
- [ ] `gates/selftest.sh` exits 0
- [ ] `gates/verify_fablelayer.sh . --mode new` exits 0

## Policy checklist

- [ ] No private, proprietary, or leaked prompt text
- [ ] No performance claim without `bench/` raw data and a limitations section
- [ ] No new runtime dependency (or a proposal justifies the trade-off)
- [ ] Tests added/updated for behavior changes
- [ ] `ATTRIBUTION.md` updated if any upstream source was added
- [ ] No absolute local paths or secrets introduced
