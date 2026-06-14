# ATTRIBUTION

FableLayer는 아래 오픈소스/공개 자료의 **아이디어와 절차**에서 영감을 받았다. 코드를 직접 복사하지 않고, 검증된 방법론을 재구현하거나 `inspired-by` 방식으로 참조한다. 각 소스의 라이선스 상태는 2026-06-14 정찰 기준이며, **확정 라이선스 검증은 통합 직전 `fablelayer-legal-guardian` 에이전트가 LICENSE 파일 원문으로 재확인**한다.

## 코드/방법론 소스

| 소스 | 용도 | 라이선스 상태(2026-06-14) | 통합 방식 |
|------|------|--------------------------|-----------|
| [fivetaku/fablize](https://github.com/fivetaku/fablize) | ProcedureHarness (verification grounding, multi-story gate, investigation, early-stop) | README에 MIT 배지 (GitHub 자동감지 실패 — LICENSE 원문 재확인 필요) | 방법론 재구현 (inspired-by) |
| [itsinseong/value-for-fable](https://github.com/itsinseong/value-for-fable) | ValueOptimizer (VFF v2 output-style, COST 라우팅) | LICENSE+NOTICE 파일 존재 (원문 재확인 필요) | 방법론 재구현 + 벤치 방법론 차용 |
| [robzilla1738/supergoal](https://github.com/robzilla1738/supergoal) | 자율 빌드 루프, adaptive phase, self-healing | LICENSE 존재 (원문 재확인 필요) | 패턴 참조 |
| [ucsandman/context-handoff-bundle](https://github.com/ucsandman/context-handoff-bundle) | 세션 핸드오프, drift detection | README에 MIT 배지 | 패턴 참조 |
| [sgup/ai](https://github.com/sgup/ai) | Fable5.md operating profiles | 라이선스 불명확 | 구조 참조만 (코드 미포함) |
| [xonovex/platform](https://github.com/xonovex/platform) | model provider routing 패턴 | 라이선스 불명확 | 개념 참조만 |
| [CheswickDEV/claude-fable-5-prompt-optimizer](https://github.com/CheswickDEV/claude-fable-5-prompt-optimizer) | prompt optimizer 룰셋 (43 source-backed rules) | 라이선스 불명확 | 개념 참조만 |
| [Anil-matcha/awesome-claude-fable-5](https://github.com/Anil-matcha/awesome-claude-fable-5) | 큐레이션 목록 | 라이선스 불명확 | 링크 참조만 |

## Leaked-prompt 소스 — 전문 포함 금지

| 소스 | 상태 | 정책 |
|------|------|------|
| [elder-plinius/CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S) | leaked system prompts, 라이선스 모호 | **전문 미포함.** 공개적으로 관찰된 *패턴*만 `inspired-by`로 요약. 사용자가 원하면 직접 적용. |
| [asgeirtj/system_prompts_leaks](https://github.com/asgeirtj/system_prompts_leaks) | leaked system prompts, 라이선스 모호 | 동일 — 전문 미포함, 패턴 요약만 |

근거: Anthropic 등 원저작자의 시스템 프롬프트 저작권/약관이 불명확하므로, 재배포 리스크를 피해 PRD §9의 "inspired-by + 사용자 직접 적용" 방침을 따른다(`license_gate.sh`가 전문/카피 지시를 HARD 차단).

## 공식 문서 참조

- Anthropic 공식 "Prompting Claude Fable 5" 문서 (인용 시 출처 명기, 전문 미복제)
- Simon Willison, "Fable is relentlessly proactive" 분석 (인용)
