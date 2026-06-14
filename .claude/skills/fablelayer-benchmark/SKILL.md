---
name: fablelayer-benchmark
description: "FableLayer blind benchmark, Fable similarity, 비용 절감, Sonnet/Opus/local LLM 비교, RESULTS.md 자동 생성, rubric 설계 요청이면 반드시 사용한다."
---

# FableLayer Benchmark

## 목적

FableLayer의 품질 주장을 재현 가능한 benchmark로 환원한다. “Fable 같다”는 인상평이 아니라 blind pairwise rubric, raw JSON, 비용 추정으로 남긴다.

## 벤치 축

1. Coding task: 작은 기능 구현 + 테스트 통과.
2. Agentic task: 다단계 조사/수정/검증 루프.
3. Long planning task: 요구사항 분해와 drift prevention.

## 결과 형식

- `bench/README.md`: 실행 방법, fixture 설명.
- `bench/RESULTS.md`: 사람이 읽는 요약. 미실행이면 미실행이라고 표시한다.
- `_workspace/benchmark_schema.json`: raw run schema.

## 판정 원칙

- 모델명은 평가자에게 숨긴다.
- 비용은 입력/출력 token과 단가 가정으로 계산한다.
- 85% similarity 같은 수치는 실제 run이 없으면 목표값으로만 표시한다.
