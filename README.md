# FableLayer

**Fable is a discipline, not a capability transplant. We open-source the discipline — and the benchmark that proves its limits.**

FableLayer is a procedure, verification, and output-structure layer for Opus, Sonnet, and local LLMs. It does **not** turn a model into Fable 5.

## What FableLayer is — and is not

The distinction below is load-bearing. The rest of this README, and the project's honesty gate, depend on it.

- **Capability is not transferable.** A model's reasoning ceiling — how deep it can chain inference, how well it generalizes — is a property of the model's weights. No prompt, harness, or output style imports another model's capability into Opus or Sonnet. The reconnaissance behind this project (a 19-run A/B plus 26 sessions by the upstream author of the procedure source) reached the same conclusion: model capability does not transfer through a harness.
- **Procedure is transferable.** What *does* transfer is behavior — the steps a strong operator takes. FableLayer ports only the procedures that were empirically observed to transfer:
  - **Verification grounding** — finish only after running and observing the artifact, not after asserting it works.
  - **Multi-story completion with an evidence gate** — refuse to report "done" without grounded evidence.
  - **Systematic investigation** — reproduce, compete hypotheses, build the causal chain, instead of patching the first guess.
  - **Early-stop prevention** — a hook that resists quitting before the work is actually complete.
  - **Structured output** — the ValueOptimizer output style, applied without the lossy compression rules.

The framing, in one line: FableLayer **does not raise the ceiling; it helps the model reach its own ceiling.**

## The four layers

| Layer | Name | Responsibility |
|-------|------|----------------|
| 1 | **PromptCore** | Inspired-by structure extraction from prompt sources (no verbatim leaked prompt text), merged with the Fable 5 core notes and the ValueOptimizer sections, version-managed (V2/V3…). |
| 2 | **ProcedureHarness** | The four transferable procedures above, as files and hooks. Includes an optional 2-pass review. |
| 3 | **ValueOptimizer** | Output-style application, a cost-aware model router (task-type → model), drift prevention, and an always-on passive mode. Deliberately **omits compression rules** (see below). |
| 4 | **SkillPack & Router** | A unified interface over autonomous-build, session-handoff, and optimizer skills, plus a Smart Model Router (Sonnet by default; automatic switch to Opus for complex work, with documented routing criteria). |

### Why no compression rules

The upstream ValueOptimizer source (`value-for-fable`) shipped compression rules in its first version. On neutral re-verification, those rules read as a quality liability rather than a gain — the original benchmark could not be reproduced because the raw data was lost, and removing the compression rules was the real improvement. FableLayer therefore does **not** carry them. ValueOptimizer here applies output structure, not output shrinkage.

## Deployment forms

FableLayer ships in three forms from one source tree:

1. **Claude Code plugin** — a `.claude-plugin/marketplace.json` plus a `plugin.json`, both valid JSON, installable into Claude Code.
2. **CLI** — `fablelayer init`, `fablelayer upgrade <model>`, and `fablelayer benchmark` subcommands.
3. **Local LLM adapter** — a config generator for Ollama, LM Studio, and SillyTavern.

## Installation

```bash
# Clone
git clone <repo-url> fablelayer
cd fablelayer

# Inspect the CLI
./cli/fablelayer --help

# Scaffold into a project (local artifacts only; no external push)
./cli/fablelayer init

# Upgrade a target model with the FableLayer procedure layer
./cli/fablelayer upgrade sonnet
```

By default every operation writes **local artifacts only**. Creating a GitHub repository, pushing, registering on a marketplace, or merging a PR happens **only behind an explicit approval gate** — never as a side effect of a normal run.

## Honest performance

Performance numbers live in `bench/` and nowhere else. This README makes no unverified performance claim, by policy and by gate.

- The benchmark suite (`bench/RESULTS.md`) ships with raw data, a reproduction script, a neutral scoring rubric, at least two independent judging methods, and a mandatory **Limitations** section.
- The honesty gate (`gates/perf_claim_gate.sh`) blocks any quantitative performance assertion in docs that lacks a `[bench/...]` reference. If you want a number, read the benchmark and cite it.
- Summary of what the neutral re-verification found, stated as procedure rather than capability: structured Sonnet output was roughly comparable to Opus within measurement noise on the tested tasks, at a fraction of the output cost, while genuinely deep reasoning still favored Opus. The original upstream benchmark was **not** reproducible (raw data lost). Read `bench/RESULTS.md` and its Limitations section before citing any of this.

## Run manifest

Every run records a `runs/<run_id>/RUN_MANIFEST.json` capturing the mode, inputs, phases, and gate results. Phases use a fixed enum (`0-context`, `1-spec`, `2-build`, `3-gates`, `4-bench`, `5-report`). `status` and `resume` operate against this manifest.

## Scope

FableLayer's MVP is the four layers, the three deployment forms, and the benchmark suite. A web dashboard, a community marketplace, and LoRA training are **out of MVP scope** and are deferred by phase in `ROADMAP.md`. Nothing deferred is reported as implemented.

## License and attribution

FableLayer is licensed under **AGPL-3.0** (`LICENSE`, with `NOTICE`).

Every upstream source is recorded in [`ATTRIBUTION.md`](./ATTRIBUTION.md) with its honest license status (MIT vs. unclear, distinguished explicitly). Leaked-prompt sources are referenced as structure inspiration only — **no verbatim leaked prompt text is included**, and the license gate (`gates/license_gate.sh`) enforces this with a hard exit.

## Documentation

- [`README.ko.md`](./README.ko.md) — Korean README.
- [`ATTRIBUTION.md`](./ATTRIBUTION.md) — sources and license status.
- [`ROADMAP.md`](./ROADMAP.md) — phased scope, including deferred features.
- `bench/RESULTS.md` — benchmark results, raw data, reproduction, and limitations.
