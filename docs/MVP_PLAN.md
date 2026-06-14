# FableLayer MVP Plan

## Phase 0 — Safe Core Skeleton

- `core/source_policy.py`: source ledger validation.
- `core/procedure_spec.md`: verification, investigation, review, drift prevention modules.
- `gates/verify_fablelayer.sh`: fail-closed QA gate.
- `gates/license_gate.sh`, `perf_claim_gate.sh`, `preflight_gate.sh`, `publish_gate.sh`, `selftest.sh`: Opus 개선본에서 선별 통합한 보조 HARD 게이트.

## Phase 1 — CLI

- `cli/fablelayer`: shell entrypoint.
- Commands: `init`, `verify`, `benchmark`, `status`.
- 모든 명령은 `--dry-run` 기본값으로 시작한다.

## Phase 2 — Runtime Adapters

- Claude Code skill bundle exporter.
- Ollama/LM Studio/SillyTavern config exporter.
- adapter output은 `_dist/`에 생성하고 사용자 승인 전 외부 배포하지 않는다.

## Phase 3 — Benchmark

- `bench/fixtures/`: 공개 예제 task.
- `bench/run_benchmark.py`: raw JSON 생성.
- `bench/RESULTS.md`: 결과 요약. 미실행 시 목표값과 실측값을 분리한다.

## Acceptance Checks

- `bash gates/verify_fablelayer.sh` exit 0.
- source ledger high risk 항목이 core에 복사되지 않음.
- benchmark 결과가 없으면 similarity 주장을 완료로 표시하지 않음.
