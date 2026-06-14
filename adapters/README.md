# FableLayer Local LLM Adapters

이 디렉토리는 FableLayer의 **전이 가능한 절차·출력구조 레이어**(PromptCore / ProcedureHarness / ValueOptimizer)를 로컬 LLM 런타임이 소비할 수 있는 system prompt·config 형태로 변환하는 생성기를 담는다. 단일 진실(SSoT)은 루트 `REQUIREMENTS.md`의 FL5(배포 3형태)이며, 주입되는 절차 본문의 정본은 `core/promptcore.md`다.

지원 런타임 3종:

| 런타임 | 생성기 | 산출물 형태 |
|--------|--------|------------|
| Ollama | `adapters/ollama.sh` | Modelfile (SYSTEM 블록에 PromptCore 주입) |
| LM Studio | `adapters/lmstudio.md` | system prompt 텍스트 + preset 적용 가이드 |
| SillyTavern | `adapters/sillytavern.md` | context/instruct preset 적용 가이드 |

## 핵심 전제: capability는 전이되지 않는다 (정직성)

FableLayer의 정찰 실측 결론은 **모델 capability(추론력 자체)는 어떤 레이어로도 다른 모델에 전이되지 않는다**는 것이다. 따라서 이 어댑터들이 로컬 LLM에 하는 일은 정확히 한 가지로 한정된다.

- **전이되는 것(procedure):** 검증 grounding(산출물을 실행·관찰한 뒤 완료 선언), 완결성 evidence gate(근거 없는 "완료" 거부), 체계적 조사(재현 → 가설 경쟁 → 인과 사슬), early-stop 방지, 구조화된 출력 형식. 이것들은 *행동 규율*이므로 system prompt로 주입하면 작은 로컬 모델에서도 일정 부분 따라온다.
- **전이되지 않는 것(capability):** 모델이 본래 갖지 못한 추론 깊이·지식·코드 합성 능력. 어댑터를 거쳐도 7B 로컬 모델이 대형 모델의 추론력을 얻지는 못한다.

그러므로 **Local LLM 어댑터는 "모델을 강하게 만드는 도구"가 아니라 "이미 가진 능력을 규율 있게 쓰게 하는 도구"다.** 이 경계를 산출물·문서에서 흐리지 않는다. 성능 수치(유사도·점수·절감률)는 이 디렉토리 어떤 문서에서도 단언하지 않으며, 측정값이 필요하면 루트 `bench/RESULTS.md`와 그 `## 한계` 섹션을 참조한다.

## 공통 동작 원칙

생성기 3종은 공통적으로 다음을 지킨다.

1. **정본 참조:** 주입할 절차 본문은 `core/promptcore.md`에서 읽는다. 생성기는 절차를 발명하지 않고, 정본을 런타임 포맷으로 변환만 한다. `core/promptcore.md`가 없으면 생성기는 에러로 멈추고 경로를 보고한다(절차를 임의 합성하지 않는다).
2. **fallback-zero 호환:** 생성하는 system prompt 텍스트는 루트 게이트 `gates/verify_fablelayer.sh`가 호출하는 `fable_lint`에 통과 가능한 형태로 쓴다. 즉 추론 과정을 응답 본문에 그대로 옮기라는 지시나 컨텍스트 잔량 카운트다운 노출 같은 패턴을 넣지 않으며, 산출물 자신의 안전 동작을 메타적으로 묘사하는 표현도 피한다(그런 묘사 자체가 refusal을 유발할 수 있다).
3. **로컬 우선·비공개 기본:** 어댑터는 전부 로컬 파일만 생성한다. 외부 레지스트리 등록·push·업로드는 하지 않는다(FL15 승인 경계).

## 사용 흐름

```bash
# 1) 정본 절차가 준비되어 있어야 한다
test -f core/promptcore.md || echo "core/promptcore.md 가 먼저 생성되어야 한다"

# 2) Ollama Modelfile 생성 (베이스 모델은 인자로 지정)
bash adapters/ollama.sh llama3.1 ./out/Modelfile.fablelayer

# 3) LM Studio / SillyTavern 는 가이드 문서를 따라 system prompt 를 붙여넣는다
#    adapters/lmstudio.md / adapters/sillytavern.md 참조
```

## 한계

- 어댑터는 절차만 주입한다. 베이스 로컬 모델이 작거나 양자화 손실이 크면 절차 준수 자체가 불완전해질 수 있다. 이는 어댑터의 결함이 아니라 capability 비전이의 직접 귀결이다.
- 런타임별 system prompt 길이 제한·토큰 예산이 작으면 절차 전문을 다 넣지 못할 수 있다. 이 경우 `core/promptcore.md`의 핵심 절차 헤더만 우선 주입하고 나머지는 생략하는 것을 권장한다(생략 사실을 config 주석에 남긴다).
- 본 어댑터는 성능을 보장하지 않는다. 절차 주입 전후 차이를 알고 싶으면 동일 베이스 모델로 직접 비교 측정하고, 방법론은 `bench/RESULTS.md`를 참조한다.
