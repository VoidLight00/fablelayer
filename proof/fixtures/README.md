# Proof Fixtures

FableLayer's executable good/bad fixtures currently live under `gates/fixtures/`.

They are exercised by:

```bash
bash gates/selftest.sh
```

The selftest asserts both pass and fail behavior:

- `license_pass` passes and `license_fail` fails
- `perf_pass` passes and `perf_fail` fails
- `bench_pass` passes and `bench_fail` fails
- `complete_pass` passes and `complete_fail` fails
- `preflight_pass` passes and `preflight_fail` fails
- `render_pass` passes and `render_fail` fails
- `publish_fail` fails without approval
- `runtime_pass` passes and `runtime_fail` fails

This directory exists as the proof index. New proof fixtures may either be added here or under `gates/fixtures/` when they are tied to a gate.

When adding a fixture, include:

1. The defect being tested.
2. The expected exit code.
3. The gate or proof script that owns the fixture.
4. A note explaining why the fixture matters for public claims.

