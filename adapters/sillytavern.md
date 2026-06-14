# SillyTavern Adapter — FableLayer

SillyTavern은 로컬·원격 LLM 백엔드(Ollama, LM Studio, KoboldCpp, text-generation-webui 등)에 붙는 프런트엔드다. 설정을 **Context Template**과 **Instruct Template** preset(JSON)으로 관리한다. FableLayer 어댑터는 전이 가능한 절차(`core/promptcore.md`)를 이 두 preset에 주입하는 방법을 정의한다. 이 가이드는 주입 절차만 다루며, 절차 본문 자체는 발명하지 않고 정본을 변환만 한다.

## 무엇을 주입하는가 (경계)

SillyTavern에 주입하는 것은 **절차(procedure)**다. 검증 grounding, 완결성 evidence gate, 체계적 조사, early-stop 방지, 구조화된 출력 — 이 행동 규율을 system / story-string에 건다. 베이스 백엔드 모델의 **capability(추론력)는 전이되지 않는다.** 어댑터는 모델이 가진 능력을 규율 있게 쓰게 할 뿐 능력 자체를 늘리지 않는다. 성능 수치는 단언하지 않으며, 측정값은 루트 `bench/RESULTS.md`(와 그 `## 한계`)를 참조한다.

## 주입 지점

SillyTavern에서 절차를 거는 위치는 두 곳이다.

| 위치 | 역할 | FableLayer 주입 |
|------|------|----------------|
| Context Template (`story_string`) | 매 프롬프트의 상단 컨텍스트 골격 | 절차 본문을 system 블록으로 포함 |
| Instruct Template (`system_prompt`) | instruct 모델의 system 지시 | 절차 본문을 system 지시로 주입 |

원격 챗 컴플리션 백엔드를 쓰면 Instruct Template의 `system_prompt`만으로 충분하고, 로컬 텍스트 컴플리션 백엔드를 쓰면 Context Template의 `story_string`에도 절차를 넣는 편이 안정적이다.

## 적용 절차

1. SillyTavern에서 사용할 백엔드(Ollama / LM Studio / KoboldCpp 등)를 연결한다. 모델 선택이 capability를 결정한다 — 어댑터가 보상하지 못한다.
2. **A) Settings** → **Context Template** 또는 **Instruct** 패널을 연다.
3. 아래 생성 스니펫으로 preset JSON을 만들고 **Import**로 불러온다(또는 system 필드에 정본 본문을 직접 붙여넣는다).
4. 샘플링은 절차 준수를 위해 보수적으로: Temperature 0.3~0.5, Top P 0.9 권장.
5. 대화를 시작해 모델이 근거 없는 완료 선언을 피하고 조사 시 재현 → 가설 → 인과 순서를 따르는지 직접 관찰한다.

## 생성 스니펫 (정본 → SillyTavern preset)

`core/promptcore.md`를 읽어 Instruct Template preset과 Context Template preset 두 개를 만든다. macOS 기본 python3로 동작한다. 정본이 없으면 멈춘다.

```bash
# repo 루트에서 실행
CORE="core/promptcore.md"
OUT_DIR="out/sillytavern"
[ -f "$CORE" ] || { echo "FAIL: $CORE 가 먼저 생성되어야 한다"; exit 2; }
mkdir -p "$OUT_DIR"

python3 - "$CORE" "$OUT_DIR" <<'PY'
import json, sys, os
core_path, out_dir = sys.argv[1], sys.argv[2]
with open(core_path, "r", encoding="utf-8") as f:
    procedure = f.read()

# Instruct Template preset — procedure goes into system_prompt.
instruct = {
    "name": "FableLayer-Procedure",
    "system_prompt": procedure,  # procedure only; capability not transferred
    "input_sequence": "<|user|>",
    "output_sequence": "<|assistant|>",
    "system_sequence": "<|system|>",
    "wrap": True,
    "macro": True,
}

# Context Template preset — procedure embedded in the story string as a system block.
context = {
    "name": "FableLayer-Procedure",
    "story_string": "<|system|>\n" + procedure + "\n{{#if scenario}}{{scenario}}\n{{/if}}{{#if persona}}{{persona}}\n{{/if}}",
    "use_stop_strings": True,
    "trim_sentences": False,
}

with open(os.path.join(out_dir, "instruct-fablelayer.json"), "w", encoding="utf-8") as f:
    json.dump(instruct, f, ensure_ascii=False, indent=2)
with open(os.path.join(out_dir, "context-fablelayer.json"), "w", encoding="utf-8") as f:
    json.dump(context, f, ensure_ascii=False, indent=2)
print("WROTE", os.path.join(out_dir, "instruct-fablelayer.json"))
print("WROTE", os.path.join(out_dir, "context-fablelayer.json"))
PY
```

생성한 두 preset의 JSON 유효성을 직접 확인한다.

```bash
for f in out/sillytavern/instruct-fablelayer.json out/sillytavern/context-fablelayer.json; do
  python3 -m json.tool "$f" >/dev/null && echo "valid: $f rc=$?"
done
```

SillyTavern의 Instruct / Context Template 패널에서 각각 Import한다. SillyTavern 버전에 따라 preset 키 이름이 다를 수 있으므로, import 후 system 블록에 절차 본문이 실제로 들어갔는지 미리보기로 확인한다.

## 한계

- SillyTavern preset 스키마는 버전마다 키가 바뀐다. 위 스니펫은 일반적 구조를 따르며, import가 실패하면 system_prompt / story_string 값만 떼어 해당 필드에 수동 입력한다.
- 컨텍스트 상한이 작으면 절차 전문이 잘릴 수 있다. 핵심 절차 헤더만 우선 주입한다.
- 절차 주입은 capability를 보상하지 않는다. 작은 양자화 모델일수록 준수가 불안정하며, 이는 capability 비전이의 직접 결과다. 성능 비교가 필요하면 동일 백엔드로 직접 측정하고 방법론은 `bench/RESULTS.md`를 참조한다.
