---
name: fablelayer-source-ledger
description: "FableLayer 참고 저장소, Anthropic 공식 문서, Simon Willison 분석, Fable 관련 오픈소스의 source ledger와 license/provenance 감사를 수행한다. 유출 prompt 원문은 복사하지 않고 reference-only 또는 blocked로 기록한다."
---

# FableLayer Source Ledger

## 목적

참조 자료를 공개 프로젝트에 안전하게 반영하기 위한 원장 작성 스킬이다.

## 절차

1. URL, 이름, 설명, 확인일을 기록한다.
2. LICENSE와 저작권 고지를 확인한다.
3. 허용 사용 범위를 `copy`, `adapt`, `reference-only`, `blocked`, `unverified` 중 하나로 분류한다.
4. 유출·비공개 시스템 프롬프트 원문은 내용 복사 없이 `reference-only` 또는 `blocked`로 둔다.
5. 산출물에는 원문 일부를 붙이지 말고 원칙 수준 요약만 적는다.

## 출력 스키마

```json
{
  "generated_at": "YYYY-MM-DD",
  "items": [
    {
      "name": "string",
      "url": "string",
      "license": "string|null",
      "allowed_use": "copy|adapt|reference-only|blocked|unverified",
      "risk": "low|medium|high|blocked",
      "notes": "string"
    }
  ]
}
```

## 금지

- private prompt 원문 저장
- license 불명확 자료의 코드 복사
- 출처 없는 “커뮤니티 자료”를 core에 포함
