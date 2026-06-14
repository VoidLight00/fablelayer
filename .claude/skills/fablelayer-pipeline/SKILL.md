---
name: fablelayer-pipeline
description: "FableLayer PRD, FableLayer MVP, Claude 모델을 Fable 5급 절차 레이어로 업그레이드하는 툴킷, source ledger, benchmark, local LLM adapter, Claude Code plugin, 재실행, 수정, 보완, status, qa 요청이면 반드시 사용한다. 에이전트 팀으로 FableLayer 하네스를 실행한다."
---

# FableLayer Pipeline

FableLayer 작업을 에이전트 팀으로 실행하는 오케스트레이터 스킬이다. 목적은 PRD를 안전하고 검증 가능한 공개 프로젝트 구조로 바꾸는 것이다.

## Phase 0: 컨텍스트 확인

1. `REQUIREMENTS.md`를 읽는다.
2. `_workspace/runs/`와 최근 `RUN_MANIFEST.json`을 확인한다.
3. 실행 모드를 판정한다.
   - 새 PRD/큰 입력: 새 run
   - “수정/보완/다시”: 기존 산출물 기반 부분 재실행
   - “status”: 읽기 전용 상태 보고
   - “qa”: 게이트만 재실행

## Phase 1: 팀 구성

기본 팀:

| 에이전트 | 역할 |
|---|---|
| fablelayer-conductor | RUN_MANIFEST, phase gate, 최종 보고 |
| fablelayer-source-auditor | source ledger, license, provenance |
| fablelayer-legal-guardian | AGPL/재배포/유출 원문 차단 |
| fablelayer-architect | core/plugin/cli/adapter/benchmark 아키텍처 |
| fablelayer-implementation-planner | MVP task breakdown |
| fablelayer-benchmark-designer | blind benchmark rubric |
| fablelayer-qa-auditor | 요구사항 완전성, 게이트 exit code |

모든 Agent 호출에는 `model: "opus"`를 명시한다.

## Phase 2: Source Ledger

`fablelayer-source-auditor`와 `fablelayer-legal-guardian`이 다음을 만든다.

- `_workspace/source_ledger.json`
- `_workspace/legal_review.md`

유출/비공개 prompt 원문은 `blocked` 또는 `reference-only`로 기록한다. 원문 복사 금지.

## Phase 3: Architecture

`fablelayer-architect`가 다음을 만든다.

- `docs/ARCHITECTURE.md`
- `docs/CONFIG_SCHEMA.md` (필요 시)
- `_workspace/decisions.md`

필수로 다룰 축:

1. PromptCore
2. ProcedureHarness
3. ValueOptimizer
4. SkillPack & Router
5. Claude Code Plugin
6. CLI Tool
7. Local LLM Adapter
8. Benchmark Suite

## Phase 4: MVP Plan

`fablelayer-implementation-planner`가 다음을 만든다.

- `docs/MVP_PLAN.md`
- `_workspace/task_breakdown.json`

## Phase 5: Benchmark Design

`fablelayer-benchmark-designer`가 다음을 만든다.

- `bench/README.md`
- `bench/RESULTS.md`
- `_workspace/benchmark_schema.json`

## Phase 6: QA Gate

`fablelayer-qa-auditor`가 `gates/verify_fablelayer.sh`를 실행한다. exit code가 0이 아니면 완료 보고 금지.

게이트 분류:

| Exit | 의미 |
|---|---|
| 0 | PASS |
| 2 | 구조/필수 산출물 누락 |
| 3 | 안전/유출 원문/비밀값 위험 |
| 4 | 완전성 요구사항 누락 |

## RUN_MANIFEST.json

각 run은 `_workspace/runs/<run_id>/RUN_MANIFEST.json`에 기록한다.

```json
{
  "run_id": "20260614-120000-plan",
  "mode": "plan",
  "input_summary": "FableLayer PRD v1.0",
  "phases": [{"name":"source-ledger","status":"done","owner":"fablelayer-source-auditor"}],
  "artifacts": ["docs/ARCHITECTURE.md"],
  "gates": {"verify_fablelayer_exit":0},
  "created_at": "2026-06-14T12:00:00+0900",
  "updated_at": "2026-06-14T12:10:00+0900"
}
```

## 에러 처리

- source risk high/blocked: 아키텍처에서 복사 의존 제거 후 재검증한다.
- gate exit 2/3/4: owner 에이전트로 되돌려 최대 3회 수정한다.
- 외부 네트워크 실패: ledger 항목을 `unverified`로 두고 완료 보고에 미검증으로 표시한다.

## 테스트 시나리오

### 정상 흐름

입력: FableLayer PRD 전체. 기대: source ledger, architecture, MVP plan, benchmark skeleton, gate PASS.

### 에러 흐름

입력에 유출 prompt 원문이 포함됨. 기대: gate exit 3, 원문 산출물 저장 금지, legal review에 blocked 기록.
