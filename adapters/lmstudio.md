# LM Studio Adapter — FableLayer

LM Studio는 GGUF 로컬 모델을 데스크톱에서 돌리는 런타임이다. FableLayer 어댑터는 LM Studio의 **System Prompt** 필드와 **Preset(JSON)** 에 전이 가능한 절차를 주입하는 방법을 정의한다. 주입 본문의 정본은 `core/promptcore.md`이며, 이 가이드는 그것을 LM Studio 포맷에 맞게 넣는 절차만 설명한다.

## 무엇을 주입하는가 (경계)

LM Studio에 주입하는 것은 **절차(procedure)**다. 검증 grounding, 완결성 evidence gate, 체계적 조사, early-stop 방지, 구조화된 출력 — 이 행동 규율을 system prompt로 모델에 건다. 주입해도 베이스 GGUF 모델의 **capability(추론 깊이·지식)는 늘지 않는다.** 어댑터는 모델을 강하게 만드는 도구가 아니라 가진 능력을 규율 있게 쓰게 하는 도구다. 성능 수치는 이 문서에서 단언하지 않으며, 측정값은 루트 `bench/RESULTS.md`(와 그 `## 한계`)를 참조한다.

## 적용 절차 (GUI)

1. LM Studio 좌측에서 베이스 모델을 로드한다(예: 7B~14B 계열 GGUF). 모델 선택은 capability를 결정하므로, 무거운 추론이 필요하면 더 큰 모델을 고른다 — 어댑터가 이를 보상하지 못한다.
2. 우측 패널의 **System Prompt** 필드를 연다.
3. `core/promptcore.md`의 본문을 그대로 붙여넣는다. 길이 제한에 걸리면 절차 헤더(검증 grounding / evidence gate / 체계적 조사 / early-stop 방지 / 출력구조)부터 우선 넣고, 생략 사실을 메모로 남긴다.
4. 샘플링은 절차 준수에 맞춰 보수적으로 둔다: Temperature 0.3, Top P 0.9, Repeat Penalty 1.1 권장. 이는 sampling 튜닝이지 capability 향상이 아니다.
5. 대화를 시작해 모델이 "근거 없이 완료를 선언하지 않는지", "조사 시 재현 → 가설 → 인과 순서를 따르는지" 직접 관찰한다. 따르지 않으면 더 큰 베이스 모델로 교체한다.

## 적용 절차 (Preset JSON)

LM Studio는 설정을 Preset JSON으로 저장·재사용한다. 아래는 system prompt를 `core/promptcore.md`로 채우는 preset 스켈레톤이다. `<<<INJECT core/promptcore.md>>>` 자리에 정본 본문을 넣는다(직접 붙여넣거나 아래 생성 스니펫으로 채운다).

```json
{
  "name": "fablelayer-procedure",
  "load_params": {
    "n_ctx": 8192
  },
  "inference_params": {
    "temperature": 0.3,
    "top_p": 0.9,
    "repeat_penalty": 1.1
  },
  "system_prompt": "<<<INJECT core/promptcore.md>>>"
}
```

## 생성 스니펫 (정본을 preset에 자동 주입)

`core/promptcore.md`를 JSON 문자열로 안전하게 인코딩해 preset 파일을 만드는 스니펫이다. macOS 기본 python3로 동작한다. 정본이 없으면 멈춘다(절차를 임의 합성하지 않는다).

```bash
# repo 루트에서 실행
CORE="core/promptcore.md"
OUT="out/lmstudio-fablelayer.preset.json"
[ -f "$CORE" ] || { echo "FAIL: $CORE 가 먼저 생성되어야 한다"; exit 2; }
mkdir -p "$(dirname "$OUT")"

python3 - "$CORE" "$OUT" <<'PY'
import json, sys
core_path, out_path = sys.argv[1], sys.argv[2]
with open(core_path, "r", encoding="utf-8") as f:
    system_prompt = f.read()
preset = {
    "name": "fablelayer-procedure",
    "load_params": {"n_ctx": 8192},
    "inference_params": {
        "temperature": 0.3,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
    },
    # Injected procedure only — capability is not transferred. See adapters/README.md.
    "system_prompt": system_prompt,
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(preset, f, ensure_ascii=False, indent=2)
print("WROTE", out_path)
PY
```

생성한 preset JSON은 유효성을 직접 확인한다.

```bash
python3 -m json.tool out/lmstudio-fablelayer.preset.json >/dev/null && echo "valid JSON rc=$?"
```

그 다음 LM Studio의 Preset 가져오기로 불러오거나, system prompt 필드에 `system_prompt` 값을 붙여넣는다.

## 한계

- LM Studio의 context window(`n_ctx`)와 베이스 모델 한계가 작으면 절차 전문을 다 담지 못할 수 있다. 그 경우 핵심 절차 헤더만 우선 주입한다.
- 양자화가 강한 작은 모델일수록 절차 준수가 불안정하다. 이는 어댑터 결함이 아니라 capability 비전이의 결과다.
- 이 가이드는 성능을 보장하지 않는다. 주입 전후 차이를 알고 싶으면 동일 베이스 모델로 직접 비교하고 방법론은 `bench/RESULTS.md`를 참조한다.
