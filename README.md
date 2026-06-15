<p align="center">
  <img src="assets/fablelayer-hero.svg" alt="FableLayer — procedure, verification, benchmark">
</p>

# FableLayer

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-AGPL--3.0-blue.svg" alt="License: AGPL-3.0"></a>
  <img src="https://img.shields.io/badge/version-0.1.1-green.svg" alt="Version 0.1.1">
  <img src="https://img.shields.io/badge/Claude%20Code-plugin-8A2BE2.svg" alt="Claude Code plugin">
  <img src="https://img.shields.io/badge/gates-fail--closed-d62728.svg" alt="Fail-closed gates">
  <img src="https://img.shields.io/badge/runtime%20deps-0-lightgrey.svg" alt="Zero runtime dependencies">
</p>

**FableLayer is a public-safe procedure, verification, and benchmark layer for LLM workflows.**

It does not claim to transfer a model's underlying capability. It packages the repeatable parts of strong agentic work: evidence discipline, systematic investigation, fail-closed gates, model routing, and honest benchmark records.

## Why it exists

Teams often try to improve model behavior by copying long prompts or making vague quality claims. FableLayer takes a stricter approach:

- no private or proprietary prompt text
- no unverified performance claims
- no external publishing without approval
- no “done” without evidence
- no benchmark number without raw data and limitations

## What you get

| Layer | What it does | Files |
|---|---|---|
| PromptCore | Deterministic public-safe operating profile | `fablelayer/promptcore.py`, `core/promptcore.md` |
| Evidence Gate | Blocks completion claims without evidence | `fablelayer/evidence_gate.py` |
| Router | Cost-aware Sonnet/Opus/local routing rules | `fablelayer/router.py` |
| Adapters | Exports Claude Code, Ollama, LM Studio, SillyTavern profiles | `fablelayer/adapters.py` |
| Benchmark | Deterministic fixture scoring and raw JSON output | `fablelayer/benchmark.py`, `bench/` |
| Gates | License, performance, runtime, render, publish, completeness checks | `gates/` |

## Quick start

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer

python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new

./cli/fablelayer --help
./cli/fablelayer init --target ./_dist/demo --apply
```

See [`docs/INSTALL.md`](./docs/INSTALL.md) for detailed installation options.

## CLI

```bash
./cli/fablelayer init                 # dry-run scaffold
./cli/fablelayer init --apply         # write local layer files
./cli/fablelayer upgrade sonnet       # preview routing decision
./cli/fablelayer benchmark            # run deterministic benchmark fixtures
./cli/fablelayer check --file output.md
./cli/fablelayer status
./cli/fablelayer resume
```

## Verification

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
python3 proof/verify_claims.py .
```

Current local evidence:

- 152 stdlib tests pass
- `LICENSE/PERF/BENCH/COMPLETE/RENDER/RUNTIME` gates pass
- publish without approval exits non-zero by design
- public claim checks verify version alignment, plugin references, and tracked-file hygiene

## Proof and reproducibility

FableLayer separates verified procedural claims from unsupported capability-transfer claims.

- [`proof/CLAIMS.md`](./proof/CLAIMS.md) defines what the project claims and does not claim.
- [`proof/REPRODUCIBILITY.md`](./proof/REPRODUCIBILITY.md) gives clean-checkout reproduction steps.
- [`proof/EXPERIMENT_DESIGN.md`](./proof/EXPERIMENT_DESIGN.md) describes model-only vs model-plus-FableLayer comparisons.
- [`proof/THREATS_TO_VALIDITY.md`](./proof/THREATS_TO_VALIDITY.md) records limits and failure modes.

The CI matrix runs tests, proof claims, and gates on Python 3.10–3.13.

## Public-safe source policy

FableLayer is an original implementation. It may reference public methodology sources in [`ATTRIBUTION.md`](./ATTRIBUTION.md), but it does not copy private, proprietary, or non-public prompt text. High-risk source classes are blocked/reference-only and are not required to use this project.

## Performance honesty

FableLayer's benchmark is designed to preserve raw data and limitations. Do not cite quality or cost claims without a `bench/` reference. See [`bench/RESULTS.md`](./bench/RESULTS.md).

## Documentation

- [`docs/INSTALL.md`](./docs/INSTALL.md)
- [`docs/DEVELOPMENT.md`](./docs/DEVELOPMENT.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`SECURITY.md`](./SECURITY.md)
- [`ROADMAP.md`](./ROADMAP.md)
- [`ATTRIBUTION.md`](./ATTRIBUTION.md)
- [`README.ko.md`](./README.ko.md)

## License

AGPL-3.0. See [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE).
