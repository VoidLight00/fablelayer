---
name: fablelayer-qa-gates
description: "FableLayer 산출물 검증, 게이트 실행, 유출 프롬프트 금칙 검사, 요구사항 완전성 검사, source ledger와 architecture 교차 검증 요청이면 반드시 사용한다."
---

# FableLayer QA Gates

## 목적

완료 주장 전에 실측 증거를 만든다. 핵심 판정은 `gates/verify_fablelayer.sh` exit code다.

## 검사 항목

1. 필수 파일 존재: REQUIREMENTS, FAILURE_LOG, CLAUDE, agents, skills, gate.
2. source ledger 안전성: `allowed_use`, `risk`, `license` 필드.
3. 유출/비밀 위험: token, authorization header, 긴 private prompt 원문 패턴.
4. 요구사항 완전성: FL1~FL10 대응 산출물.
5. 하네스 구조: RUN_MANIFEST, resume/status, failure log, 승인 게이트.

## 보고 형식

```json
{
  "passed": true,
  "gate_exit": 0,
  "evidence": ["명령과 출력 요약"],
  "findings": []
}
```

## 실패 처리

exit 2/3/4는 fail-closed다. 해당 owner에게 수정 요청 후 전체 게이트를 다시 실행한다.
