# Development Guide

## Principles

- Public-safe source handling only.
- Capability claims require benchmark evidence.
- Runtime behavior must be covered by stdlib tests.
- Gate verdicts come from exit codes, not narrative claims.

## Local workflow

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

## Versioning

FableLayer follows semantic versioning:

- PATCH: docs, tests, gate fixture updates that do not change CLI contracts.
- MINOR: new CLI subcommands, adapters, benchmark fixtures, or gates.
- MAJOR: breaking CLI/API/interface changes.

Update these files together when cutting a release:

- `pyproject.toml`
- `fablelayer/__init__.py`
- `CHANGELOG.md`
- `runs/<run_id>/RUN_MANIFEST.json`

## Release checklist

1. `python3 tests/run_tests.py`
2. `bash gates/selftest.sh`
3. `bash gates/verify_fablelayer.sh . --mode new`
4. Review `ATTRIBUTION.md` and source licenses.
5. Confirm no unapproved publish token is present.
6. Tag only after the working tree is clean.
