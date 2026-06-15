# FableLayer Claims

This document defines what FableLayer claims, what it does not claim, and how each claim is verified.

## Claim boundary

FableLayer is a procedure, verification, and benchmark layer for LLM workflows. It does not claim to transfer a model's underlying capability.

In short:

- It can improve procedural discipline.
- It can make completion claims more evidence-bound.
- It can make public-release hygiene easier to audit.
- It can preserve benchmark raw data and limitations.
- It cannot turn one model into another model.
- It cannot guarantee better reasoning on every task.
- It cannot justify performance claims without benchmark evidence.

## Verified release claims

### C1. The checkout is installable without runtime Python dependencies.

Verification:

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

CI verifies this on Python 3.10, 3.11, 3.12, and 3.13.

### C2. Public metadata is version-aligned.

Files that must agree:

- `VERSION`
- `pyproject.toml`
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `CHANGELOG.md`

Verification:

```bash
python3 proof/verify_claims.py .
```

### C3. Plugin references point to files or directories that exist.

The plugin metadata must not reference missing skills, agents, or layer directories.

Verification:

```bash
python3 proof/verify_claims.py .
```

### C4. Internal build artifacts are not tracked.

The public repository must not track `_workspace/` outputs.

Verification:

```bash
python3 proof/verify_claims.py .
git ls-files '_workspace/**'
```

The second command should print nothing.

### C5. The root internal `CLAUDE.md` is not tracked.

Local developer instructions may exist in a working tree, but they are not part of the public release surface.

Verification:

```bash
python3 proof/verify_claims.py .
git ls-files CLAUDE.md
```

The second command should print nothing.

### C6. Tracked files do not contain local absolute-path artifacts.

The current tracked tree must not contain local path artifacts from the development machine.

Verification:

```bash
python3 proof/verify_claims.py .
```

## Benchmark claims

Benchmark claims must cite:

- fixture set
- command used
- raw JSON result
- measured result
- limitation section

The benchmark may support claims about procedure adherence. It must not be used to claim general model capability transfer.

## Non-claims

FableLayer does not claim:

- that Sonnet becomes Opus
- that a local model becomes a frontier model
- that hidden or proprietary prompts are copied
- that benchmark results generalize outside their fixtures
- that external publishing is allowed without approval

## How to add a new claim

Every new public claim must add:

1. A plain-language statement.
2. A verification command.
3. A failure mode.
4. A limitation note.
5. A CI or fixture-backed check when practical.

