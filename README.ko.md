# FableLayer

> 한국어 문서입니다. 영어판은 [README.md](./README.md)를 참조하십시오.
> 모든 요구사항·게이트 판정의 단일 진실(SSoT)은 [REQUIREMENTS.md](./REQUIREMENTS.md)입니다.

FableLayer는 Fable 5에서 *전이 가능하다고 실측된* 절차·검증·출력구조를 Opus / Sonnet / 로컬 LLM에 모듈로 주입하는 레이어입니다.

## 한 줄 요약

> Fable is a discipline, not a capability transplant. We open-source the discipline — and the benchmark that proves its limits.

Fable은 능력 이식이 아니라 규율입니다. 이 프로젝트는 그 규율을 오픈소스로 공개하고, 그 규율의 한계까지 드러내는 벤치마크를 함께 공개합니다.

## capability(능력) vs procedure(절차) — 가장 먼저 읽어야 할 구분

이 구분은 FableLayer의 정체성이며, 정찰 실측에서 도출된 결론입니다.

- **capability(모델 지능)는 전이되지 않습니다.** Fable 5의 추론 능력 자체를 프롬프트나 하네스로 다른 모델에 옮길 수 없습니다. `fablize` 저자의 실증(19런 A/B + 26세션)이 이를 가리킵니다. FableLayer는 모델의 천장(ceiling)을 올리지 않습니다.
- **procedure(절차)는 전이됩니다.** 옮길 수 있는 것은 행동 절차뿐입니다. 산출물을 실행·관찰한 뒤에 완료하는 verification grounding, 근거 없는 "done"을 거부하는 evidence gate, 재현→가설경쟁→인과사슬의 systematic investigation, 그리고 early-stop(조기 중단) 방지입니다.

FableLayer가 하는 일은 "모델이 자기 천장에 닿게 하는 것"이지, 천장을 올리는 것이 아닙니다. 따라서 이 도구는 **"내 모델을 Fable 5로 바꿔준다"는 도구가 아닙니다.** 그런 주장은 실측 근거상 성립하지 않으므로 하지 않습니다.

## 4개 레이어 (FL1~FL4)

FableLayer는 4개의 레이어로 구성됩니다. 각 레이어는 독립적으로 적용할 수 있으며, `layer <1-4>` 모드로 개별 빌드합니다.

### Layer 1 — PromptCore (`core/`)

공개적으로 관찰된 프롬프트 *패턴*을 "inspired-by" 방식으로 요약·구조 추출하고, 운영 프로파일과 출력구조 섹션을 병합해 버전(V2/V3…)으로 관리합니다.

leaked prompt **전문은 포함하지 않습니다.** 패턴 요약과 구조만 다루며, 전문 포함 시도는 `gates/license_gate.sh`가 HARD로 차단합니다(exit 2). 자세한 정책은 [ATTRIBUTION.md](./ATTRIBUTION.md)를 보십시오.

### Layer 2 — ProcedureHarness

`fablize`에서 *전이가 실증된* 4개 절차를 hook과 산출물로 구현합니다.

1. **verification grounding** — 산출물을 실행·관찰한 뒤에야 완료로 본다.
2. **multi-story completion + evidence gate** — 근거가 없는 "done" 선언을 거부한다.
3. **systematic investigation** — 재현 → 가설 경쟁 → 인과사슬 순으로 조사한다.
4. **early-stop 방지 hook** — 조기 중단을 막는다(셀프테스트 포함).

2-pass review는 옵션입니다.

### Layer 3 — ValueOptimizer (`styles/`)

VFF v2 output-style을 적용하고, 작업 유형별 모델 라우팅(COST optimizer), drift 방지, passive mode(항상 ON)를 제공합니다.

**압축 규칙은 도입하지 않습니다.** `value-for-fable` v2의 교훈상 압축 규칙은 품질 부채이므로, 제거가 곧 개선입니다. 강제 압축 규칙이 끼어들면 게이트가 이를 검출합니다.

### Layer 4 — SkillPack & Router (`skills/`)

자율 빌드 루프, 세션 핸드오프(재개), prompt optimizer 룰셋을 통합 인터페이스로 묶고, Smart Model Router를 둡니다. 라우터는 Sonnet을 기본으로 두고 복잡한 작업에서 Opus로 자동 전환하며, 라우팅 기준은 문서로 명시합니다.

## 배포 3형태 (FL5)

| 형태 | 산출물 | 용도 |
|------|--------|------|
| **Claude Code Plugin** | `.claude-plugin/marketplace.json` + `plugin.json` (유효 JSON) | Claude Code에 레이어를 플러그인으로 설치 |
| **CLI** | `fablelayer init` / `upgrade <model>` / `benchmark` 서브커맨드 | 프로젝트 부트스트랩, 모델 업그레이드, 벤치 실행 |
| **Local LLM Adapter** | Ollama / LM Studio / SillyTavern config 생성기 | 로컬 LLM에 절차·출력구조 주입 |

기본 동작은 **로컬 산출물 생성까지**입니다. GitHub repo 생성·push·`/plugin marketplace` 공개 등록·PR 자동 merge는 사용자 명시 승인 게이트(FL15) 뒤에서만 실행됩니다.

## 설치

> 아래는 로컬 사용 절차입니다. 외부 push/deploy는 별도 승인이 필요합니다.

```bash
# 1. 저장소 클론
git clone <repo-url> fablelayer
cd fablelayer

# 2. 게이트 셀프테스트 (하네스가 정상인지 먼저 확인)
bash gates/selftest.sh

# 3. 제품 스캐폴드 빌드 (new 모드)
#    core/ styles/ skills/ agents/ bench/ cli/ adapters/ 전체 생성

# 4. 마스터 게이트로 검증
bash gates/verify_fablelayer.sh
```

### Claude Code Plugin으로 사용

플러그인 매니페스트(`.claude-plugin/plugin.json`)는 유효 JSON이어야 하며 다음으로 검증합니다.

```bash
python -m json.tool .claude-plugin/plugin.json
python -m json.tool .claude-plugin/marketplace.json
```

### CLI로 사용

```bash
fablelayer init          # 현재 프로젝트에 레이어 부트스트랩
fablelayer upgrade opus  # 대상 모델용 절차/출력구조 적용
fablelayer benchmark     # 재현 가능 벤치 실행
```

### 로컬 LLM 어댑터로 사용

`adapters/`의 생성기로 Ollama / LM Studio / SillyTavern용 config를 만들어, 로컬 LLM에 절차·출력구조 레이어를 주입합니다.

## 성능에 대한 정직한 기술 (FL6 / FL9)

성능 수치는 이 README에 단언하지 않습니다. 모든 정량 주장은 재현 가능한 벤치마크 `bench/`의 실측과 한계 명시를 통해서만 제시합니다. 검증되지 않은 수치 단언은 `gates/perf_claim_gate.sh`가 HARD로 차단합니다(exit 2).

지금까지의 정찰·재검증에서 관찰된 사실은 다음과 같습니다. 구체적 수치·표·원자료·재현 스크립트는 [bench/RESULTS.md](./bench/RESULTS.md)에서 확인하십시오.

- `value-for-fable`의 원판 벤치는 **원자료가 분실되어 재현에 실패**했습니다. 따라서 원판 수치는 그대로 인용하지 않습니다.
- 중립 재검증에서는 일반 작업에서 Sonnet+구조가 Opus와 노이즈 범위 내 동률로 관찰되었고, 출력 비용은 낮은 쪽이었습니다.
- 깊은 추론이 필요한 작업에서는 Opus가 우세했습니다.

즉, FableLayer는 "어떤 모델이든 최상위 모델과 동일해진다"고 주장하지 않습니다. 작업 유형에 따라 절차·출력구조가 주는 이득의 크기는 다르며, 그 한계는 `bench/`의 `## 한계` / `## Limitations` 섹션에 명시합니다.

벤치마크는 중립 채점표와 독립 심판 2종 이상의 방법론을 사용하며, 원자료(`raw.json` 등)와 재현 스크립트를 함께 제공합니다. 무결성은 `gates/bench_integrity_gate.sh`로 강제합니다.

## MVP 범위 밖 (FL14)

다음은 현재 MVP 범위 밖이며, 미구현입니다. 구현된 것으로 보고하지 않습니다. Phase별 defer 내역은 [ROADMAP.md](./ROADMAP.md)를 참조하십시오.

- Web Dashboard
- Community Marketplace
- LoRA 파인튜닝 경로

## 라이선스 / 저작자 표기

- **라이선스: AGPL-3.0.** 전문은 [LICENSE](./LICENSE)에 있습니다. 고지 사항은 [NOTICE](./NOTICE)를 보십시오.
- **저작자 표기: [ATTRIBUTION.md](./ATTRIBUTION.md).** 영감을 받은 모든 오픈소스/공개 자료를 소스별 라이선스 상태(MIT / 불명확 구분)와 함께 정직하게 기재합니다. 코드를 직접 복사하지 않고 방법론을 재구현하거나 `inspired-by`로 참조합니다.
- leaked prompt 전문은 어떤 산출물에도 포함하지 않습니다. 공개적으로 관찰된 패턴만 요약하며, 적용 여부는 사용자가 직접 결정합니다.

## 안전·승인 경계 (FL15)

기본 동작은 외부 작업 없이 로컬 산출물만 생성합니다. 다음은 모두 사용자 명시 승인 뒤에만 진행합니다.

- GitHub repo 생성, push
- `/plugin marketplace` 공개 등록
- PR 자동 merge
- submodule / fork 연결

## 더 읽기

- [REQUIREMENTS.md](./REQUIREMENTS.md) — SSoT (FL1~FL16, 모드 정의, 게이트 맵)
- [ROADMAP.md](./ROADMAP.md) — Phase별 범위와 defer 내역
- [ATTRIBUTION.md](./ATTRIBUTION.md) — 소스별 라이선스 상태와 통합 방식
- [bench/RESULTS.md](./bench/RESULTS.md) — 재현 가능 벤치마크 결과와 한계
