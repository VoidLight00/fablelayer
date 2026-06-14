# FableLayer Architecture

상태: 하네스 초기 설계
작성일: 2026-06-14

## 설계 원칙

FableLayer는 “Fable 5의 비공개 시스템 프롬프트를 복제하는 프로젝트”가 아니다. 공개 가능한 절차 discipline을 제품화한다. 따라서 core는 prompt 원문 저장소가 아니라 검증·조사·리뷰·드리프트 방지 절차를 실행하는 레이어다.

## 모듈

### 1. PromptCore

- 공개/허가된 style fragment만 ingest한다.
- 모든 fragment는 source ledger의 `allowed_use`를 통과해야 한다.
- 출력은 target runtime별 config bundle이다.

### 2. ProcedureHarness

- verification grounding: 주장마다 근거 파일/명령/출처를 요구한다.
- investigation protocol: 바로 구현하지 않고 scope → evidence → decision 순서로 진행한다.
- multi-pass review: 생성자와 검증자를 분리한다.
- early-stop hook: 검증 불가능하거나 법적 위험이 있으면 중단한다.

### 3. ValueOptimizer

- token_delta, cost_estimate, latency_estimate를 benchmark 결과에 남긴다.
- economy mode는 절차 일부를 끄는 것이 아니라 review depth와 context retrieval 범위를 줄인다.

### 4. SkillPack & Router

- Claude Code skill, CLI profile, Local LLM system prompt bundle을 같은 spec에서 생성한다.
- Smart Router는 기본 모델과 escalation rule을 명시하지만, 사용자 승인 없는 외부 비용 증가를 자동 실행하지 않는다.

## 배포 경로

### Claude Code Plugin

- `.claude/skills/fablelayer-pipeline` 형태로 설치된다.
- CLAUDE.md에 트리거와 안전 규칙을 등록한다.

### CLI Tool

- `fablelayer init`
- `fablelayer upgrade sonnet`
- `fablelayer benchmark`
- `fablelayer verify`

### Local LLM Adapter

- Ollama, LM Studio, SillyTavern용 config를 생성한다.
- 모델별 context length와 tool-use 한계를 config에 기록한다.

## 데이터 흐름

```text
source ledger → allowed fragments/procedures → core spec → runtime adapter → benchmark → qa gate
```

## 승인 게이트

외부 push, package publish, marketplace 등록, 공개 링크 생성은 `release_approval: explicit-user-approval` 상태에서만 진행한다.
