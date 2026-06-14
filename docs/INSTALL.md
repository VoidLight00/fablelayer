# Installation Guide

FableLayer is a standard-library-only Python package plus shell gates.

## Requirements

- Python 3.10+
- Bash
- Git

No runtime Python dependencies are required.

## Clone

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer
```

## Run from source

```bash
python3 -m fablelayer.cli --help
./cli/fablelayer --help
```

## Optional editable install

```bash
python3 -m pip install -e .
fablelayer --help
```

## Verify the checkout

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

## Export local adapters

```bash
./cli/fablelayer init --target ./_dist/demo --apply
```

Generated files stay local. FableLayer does not push, deploy, or publish without an explicit approval gate.
