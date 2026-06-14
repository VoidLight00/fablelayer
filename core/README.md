# core/ — PromptCore (Layer 1)

## 무엇인가

`core/` 는 FableLayer 의 Layer 1, PromptCore 다. FableLayer 4개 레이어 중 가장 아래에 있는 공통 규율 정본이다. 상위 레이어(ProcedureHarness·ValueOptimizer·SkillPack/Router)는 모두 여기서 패턴을 가져간다.

PromptCore 는 **전이 가능한 운영 규율**만 담는다 — 검증 grounding, 완결성 evidence gate, 체계적 조사, early-stop 방지, 출력구조 규약, 가성비 운영 자세, drift 방지. 이 규율들은 procedure 이며, 프롬프트 레이어로 다른 모델에 주입할 수 있다.

PromptCore 는 **capability(능력)는 담지 않는다.** 한 모델의 추론 깊이·지식을 다른 모델로 옮기는 것은 정찰 실측상 불가능하기 때문이다. 그래서 PromptCore 는 "모델을 Fable 로 바꾸는" 도구가 아니라, 전이되는 절차만 정리하고 capability 가 필요한 자리에는 escalate 경계를 만드는 레이어다.

## 왜 이렇게 만드는가

1. **capability 비전이의 정직한 반영.** PRD 의 "모델을 Fable 로 바꾼다"는 전제는 정찰 실측으로 보정됐다(REQUIREMENTS §정체성). PromptCore 는 그 보정을 §0 에 명시하고, 효과의 정량 주장(유사도·점수·절감률)을 본문에서 단언하지 않고 전부 `bench/` 실측으로 위임한다(FL9, perf_claim_gate HARD).
2. **inspired-by 병합으로 라이선스 리스크 회피.** PromptCore 는 `sgup/ai` Fable5.md 와 `value-for-fable` 8섹션을 *전문 복제 없이* 패턴·구조만 추상화해 병합한다. leaked prompt 의 전문이나 그것을 복제하라는 지시는 어떤 산출물에도 넣지 않는다(FL7, license_gate HARD). 출처 추적은 `[inspired-by:]` 태그와 `patterns.md` ledger 로 유지한다.
3. **품질 부채 차단.** value-for-fable v2 교훈에 따라, 품질을 깎는 산출물 압축 강제 규칙은 PromptCore 에 넣지 않는다(FL3). PromptCore 의 "압축"은 컨텍스트 운영의 상태 스냅샷에 한정한다.

## 파일

| 파일 | 내용 |
|------|------|
| `promptcore.md` | PromptCore 정본(V2). 9개 섹션. Fable5.md + value-for-fable 8섹션 inspired-by 병합본 |
| `versions/v2.md` | V2 버전 이력. 변경 요지·채택/배제 근거·출처 병합 매핑·검증 상태 |
| `patterns.md` | leaked prompt 에서 추출한 추상 패턴 ledger + `[inspired-by:]` 출처 태그 (별도 작성) |
| `README.md` | 이 파일 |

## 버전 관리

버전은 디렉토리/파일 분리로 한다. 새 버전은 `versions/v<N>.md` 를 추가하고 `promptcore.md` 상단 표기를 갱신하되, 이전 버전 파일은 보존한다. 변경된 섹션만 수정하고 나머지는 그대로 둔다.

## 게이트 정합

- `gates/license_gate.sh` (FL7, HARD): 이 디렉토리 산출물에 leaked 전문·카피 지시가 없어야 통과. 작성 후 종료코드로 자가 점검한다.
- `gates/perf_claim_gate.sh` (FL9, HARD): PromptCore 는 정량 성능 주장을 하지 않으므로 이 게이트의 대상 문서(README.md / docs)에 미검증 수치를 만들지 않는다.

법적 라이선스 표기 정본은 루트 `ATTRIBUTION.md` 다.
