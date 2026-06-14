# FableLayer Project Context

## 하네스: FableLayer

**목표:** 공개-safe prompt/procedure/verification 레이어로 Claude Code, CLI, Local LLM에서 Fable-like discipline을 재현하는 툴킷을 설계·구현·검증한다.

**중요 안전 규칙:** 비공개·유출 시스템 프롬프트 원문을 저장·출력·번들하지 않는다. 참조 저장소는 source ledger와 license 확인 후 `copy|adapt|reference-only|blocked|unverified`로 분류한다.

**에이전트 팀:**

| 에이전트 | 역할 |
|---|---|
| fablelayer-conductor | RUN_MANIFEST, phase gate, 팀 조율, 최종 보고 |
| fablelayer-source-auditor | source ledger, license, provenance, 유출 원문 위험 분류 |
| fablelayer-legal-guardian | AGPL/재배포/비공개 prompt 비포함 정책 검토 |
| fablelayer-architect | PromptCore/ProcedureHarness/ValueOptimizer/Router 아키텍처 |
| fablelayer-implementation-planner | MVP CLI/core/adapter/benchmark 구현 계획 |
| fablelayer-benchmark-designer | blind benchmark와 비용/토큰 rubric 설계 |
| fablelayer-qa-auditor | 요구사항 완전성, 안전, 게이트 exit code 검증 |

**스킬:**

| 스킬 | 용도 | 사용 에이전트 |
|---|---|---|
| fablelayer-pipeline | 전체 오케스트레이션, 재실행, status, qa | conductor |
| fablelayer-source-ledger | 참조 자료 license/provenance 원장 | source-auditor, legal-guardian |
| fablelayer-benchmark | blind benchmark/RESULTS 설계 | benchmark-designer |
| fablelayer-qa-gates | fail-closed 구조/안전/완전성 검증 | qa-auditor |

**실행 규칙:**

- FableLayer PRD, MVP, benchmark, source ledger, local LLM adapter, Claude Code plugin 관련 작업은 `fablelayer-pipeline` 스킬과 에이전트 팀으로 처리한다.
- 단순 질문/확인은 직접 답변해도 되지만, 완료 주장 전 `bash gates/verify_fablelayer.sh /Users/voidlight/projects/fablelayer`를 실행한다.
- 모든 에이전트는 `model: "opus"`를 사용한다.
- 중간 산출물은 `_workspace/`, run 상태는 `_workspace/runs/<run_id>/RUN_MANIFEST.json`에 둔다.
- 외부 push, package publish, marketplace 등록, 공개 링크 생성은 사용자 명시 승인 전 금지한다.

**디렉토리 구조:**

```text
.claude/
├── agents/
│   ├── fablelayer-conductor.md
│   ├── fablelayer-source-auditor.md
│   ├── fablelayer-legal-guardian.md
│   ├── fablelayer-architect.md
│   ├── fablelayer-implementation-planner.md
│   ├── fablelayer-benchmark-designer.md
│   └── fablelayer-qa-auditor.md
└── skills/
    ├── fablelayer-pipeline/SKILL.md
    ├── fablelayer-source-ledger/SKILL.md
    ├── fablelayer-benchmark/SKILL.md
    └── fablelayer-qa-gates/SKILL.md
```

**변경 이력:**

| 날짜 | 변경 내용 | 대상 | 사유 |
|---|---|---|---|
| 2026-06-14 | 초기 FableLayer 하네스 구성 | 전체 | PRD 기반 신규 하네스 구축 |
| 2026-06-14 | Opus 4.8 최종 런타임 통합 | fablelayer/*.py/tests/gates/ROADMAP/CI | Opus 최종본의 152-test Python runtime, runtime_gate, RETRO, CI 스캐폴드를 통합본 루트에 병합 |
