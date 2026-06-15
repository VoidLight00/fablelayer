# Reproducibility

This document describes how to reproduce the public release checks from a clean checkout.

## Requirements

- Git
- Bash
- Python 3.10 or newer

FableLayer has no runtime Python dependencies.

## Clean checkout

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer
```

## Baseline verification

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
python3 proof/verify_claims.py .
```

Expected result:

```text
all commands exit 0
```

## Optional editable install

```bash
python3 -m pip install -e .
fablelayer --help
```

## Benchmark reproduction

```bash
./cli/fablelayer benchmark
```

Benchmark interpretation must reference:

- raw output
- fixture list
- limitations
- date and environment

Do not cite benchmark numbers without the raw data and limitation note.

## Public-release hygiene reproduction

```bash
python3 proof/verify_claims.py .
```

This check verifies:

- version alignment
- plugin reference existence
- `_workspace/` not tracked
- root `CLAUDE.md` not tracked
- tracked files do not contain local absolute-path artifacts
- GitHub governance files exist

## CI reproduction

GitHub Actions runs the same checks on Python 3.10, 3.11, 3.12, and 3.13.

Local reproduction of the matrix can be done with pyenv, uv, or separate Python installations. The project itself does not require runtime dependencies, so a plain `python3` is enough for the default path.

## Expected non-reproducible items

The following are intentionally not required for reproduction:

- private development notes
- local `_workspace/` outputs
- local editor state
- external publish credentials
- hidden prompts or proprietary sources

