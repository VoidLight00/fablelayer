# FableLayer Benchmark — RESULTS

> 이 문서는 FableLayer가 주입하는 **절차 레이어**(verification grounding, evidence gate, systematic investigation, VFF 출력구조)의 효과를 재현 가능한 형태로 측정하기 위한 방법론과 측정 슬롯이다. 측정 대상은 모델 capability가 아니라 절차의 전이 효과다. capability는 정찰 실증상 하네스로 전이되지 않으므로(capability 비전이) 이 벤치는 "Fable 5로 바꿔준다"식 주장을 측정하지도 기술하지도 않는다.
>
> 현재 상태: **초기 placeholder.** 라이브 모델 호출 측정은 미완(환경 미가용)이다. 방법론·중립 채점표·재현 스크립트·원자료 스키마는 완비했고, 측정값 칸은 측정이 가능해지면 `reproduce.sh`로 채운다. 합성된 가짜 수치는 넣지 않는다.

## 측정 대상 (무엇을 재는가)

| 절차 요소 | 출처(inspired-by) | 측정 가설 |
|----------|------------------|----------|
| verification grounding | fablize (산출물 실행·관찰 후 완료) | 적용 시 "검증 없이 done 선언" 빈도가 줄어든다 |
| evidence gate | fablize (근거 없는 done 거부) | 적용 시 근거 인용 비율이 오른다 |
| systematic investigation | fablize (재현→가설경쟁→인과사슬) | 디버깅 task에서 근본원인 도달률이 오른다 |
| early-stop 방지 | fablize (조기 종료 hook) | 멀티스텝 task에서 미완 종료 비율이 준다 |
| VFF 출력구조 | value-for-fable (VFF v2 output-style) | 구조화 채점 항목 통과율이 오른다 |

측정하지 않는 것: 모델 capability 전이(불가), 압축 우위(value-for-fable v2 교훈상 압축은 품질 부채이므로 절차 레이어에 비포함, FL3 정합).

## 채점 방법론 (중립 설계)

1. **블라인드.** 채점자는 어느 출력이 절차 적용본(treatment)인지 미적용본(baseline)인지 모른다. `raw.json`의 각 run에 `label_hidden: true` 로 라벨을 가리고, 채점 단계에서 model/condition 필드를 마스킹한 뷰만 채점자에게 노출한다.
2. **중립 베이스라인.** 동일 모델·동일 프롬프트에서 절차 레이어만 제거한 대조군(`condition: "baseline"`)을 둔다. 절차 적용본(`condition: "treatment"`)과 짝(pair)으로 비교한다. 모델 자체를 바꾸지 않으므로 측정되는 차이는 절차 효과로 귀속된다(capability 차이가 아니다).
3. **독립 심판 ≥2.** 단일 LLM-judge는 자기 편향이 있으므로 최소 두 방법론으로 교차한다.
   - judge A: rubric 기반 정량 채점(0~5 척도, 항목별 점수).
   - judge B: 규칙 기반 결정론 검사(예: 근거 인용 존재 여부, 검증 단계 실행 흔적, 미완 종료 마커 부재를 정규식/구조 파싱으로 판정).
   두 판정의 불일치는 평균으로 덮지 않고 둘 다 `raw.json`에 남기며 본 문서 "## 심판 불일치" 절에 기록한다.
4. **Ablation.** 절차 요소를 하나씩 끄며(`ablation: "no-verification"` 등) 각 요소의 기여도를 분리한다. 전체 적용 대비 단일 요소 제거의 점수 변화로 기여도를 추정한다.

각 condition은 동일 task에 대해 시드 고정 반복(`repeats`)으로 노이즈 범위를 함께 측정한다.

## 측정 슬롯 (현재 미측정 — 환경 미가용)

> 아래 표의 점수 칸은 **미측정**이다. `reproduce.sh`로 라이브 측정이 가능해지면 `raw.json`의 원자료에서 집계해 채운다. 표본 수(n)·노이즈 범위(±)·모델 버전·측정 일자를 반드시 병기한다. 현재 단언 가능한 수치는 없다.

| task 유형 | 모델 | condition | judge A (rubric 0-5) | judge B (rule pass率) | n | 노이즈(±) |
|----------|------|-----------|----------------------|------------------------|---|-----------|
| debugging | (측정 예정) | baseline | 미측정 | 미측정 | 미측정 | 미측정 |
| debugging | (측정 예정) | treatment | 미측정 | 미측정 | 미측정 | 미측정 |
| multi-step build | (측정 예정) | baseline | 미측정 | 미측정 | 미측정 | 미측정 |
| multi-step build | (측정 예정) | treatment | 미측정 | 미측정 | 미측정 | 미측정 |
| extraction | (측정 예정) | baseline | 미측정 | 미측정 | 미측정 | 미측정 |
| extraction | (측정 예정) | treatment | 미측정 | 미측정 | 미측정 | 미측정 |

집계 규칙(측정 시 적용): treatment − baseline 의 paired 차이를 효과로 보고, n과 노이즈 범위를 병기한다. 차이가 노이즈 범위 안이면 "동률(노이즈 내)"로 정직하게 표기하고 우위 주장으로 바꾸지 않는다.

## 정찰 기준선 (벤치 설계의 출발점)

정찰 중립 재검증 결과를 설계 기준선으로 둔다. 이는 본 벤치의 직접 측정값이 아니라 외부 정찰 관찰이며, 본 벤치는 이를 절차 레이어 맥락에서 재측정 대상으로 삼는다(아래 수치는 정찰 관찰이고 미검증 외부 추정으로 표기).

- value-for-fable 중립 재검증(외부 정찰, 미검증): Sonnet+v2 출력은 Opus와 노이즈 내 동률 수준으로 관찰됨, 출력 단가는 약 0.30배. 깊은 추론 task는 Opus 우세 경향. 이 관찰은 노이즈·표본 한계가 있어 본 벤치에서 재측정 대상이다.

위 정찰 관찰을 우위 주장으로 확장하지 않는다. 본 벤치가 직접 측정하기 전까지는 단언하지 않는다.

## 심판 불일치

judge A(rubric 0-5 모사)와 judge B(rule 키워드 커버리지)의 판정이 어긋난 case다. 두 점수 차가 25점(0..100) 이상이면 불일치로 본다. 불일치는 평균으로 덮지 않고 양쪽 점수를 그대로 남긴다(recover 축: 실패 비삭제). 출처 원자료는 `bench/fixtures_raw.json` 의 각 run.raw(other_judge/other_score/delta).

| task_id | judge A (0-100) | judge B (0-100) | Δ | 근거(matched/rubric, markers) | 원인 추정 |
|---|---|---|---|---|---|
| disagree-001 | 50.00 | 100.00 | 50.00 | matched 6/6, markers 0 | B 높고 A 낮음 → 키워드는 채웠으나 근거/검증 마커 부족(rule 과탐, rubric 엄격) |
| extract-001 | 50.00 | 100.00 | 50.00 | matched 6/6, markers 0 | B 높고 A 낮음 → 키워드는 채웠으나 근거/검증 마커 부족(rule 과탐, rubric 엄격) |

해석: 위 불일치는 단일 LLM-judge 의 자기편향을 교차 검증으로 드러낸 것이다. rubric 주관성(judge A)과 rule 과탐/미탐(judge B)은 아래 '한계' 절의 judge 편향 항목과 연결된다.

## 재현 절차

```bash
bash bench/reproduce.sh --help          # 사용법
bash bench/reproduce.sh --dry-run       # 모델 호출 없이 파이프라인 점검
bash bench/reproduce.sh --run           # 실제 측정(모델 호출 스텁 구현 필요)
```

원자료는 `bench/raw.json`에 프롬프트·출력·점수·시드·모델버전을 그대로 남긴다. 원자료를 덮어쓰지 않고 run 단위로 누적한다 — 원자료 분실이 value-for-fable 원판 벤치 재현 실패의 직접 원인이었다.

## 한계

이 섹션은 선택이 아니라 필수다(없으면 `bench_integrity_gate.sh` exit 2).

- **현재 미측정.** 라이브 모델 호출 측정은 환경 미가용으로 수행하지 못했다. 본 문서의 점수 칸은 전부 placeholder이며, 단언 가능한 성능 수치는 현재 없다. 합성 수치는 넣지 않았다.
- **capability 비전이.** 본 벤치는 절차 효과만 측정한다. 모델의 추론 capability 자체는 절차 주입으로 전이되지 않으므로, "Fable 5급으로 끌어올린다"는 측정 가능 범위 밖이다. 측정 결과가 좋아도 그것은 절차 준수율 개선이지 capability 향상이 아니다.
- **value-for-fable 노이즈·표본 한계 계승.** 기준선으로 인용한 정찰 관찰(Sonnet+v2 ≈ Opus 동률, 0.30배 단가)은 외부 정찰의 미검증 추정이며 표본이 작고 task 다양성이 제한적이다. 본 벤치도 초기 표본이 작으면 같은 한계를 가진다. 노이즈 범위 안의 차이는 우위로 해석하지 않는다.
- **judge 편향.** LLM-judge(judge A)는 자기 출력 선호·길이 선호 등 편향이 있다. rule 기반 judge B로 교차하지만 rule은 과탐/미탐이 있다. 두 심판 불일치를 평균으로 덮지 않고 둘 다 남기는 이유다.
- **task 일반화 한계.** debugging/build/extraction 위주 task로는 전체 작업 분포를 대표하지 못한다. 측정값은 측정된 task 유형에 한정해 해석한다.
- **모델 버전 의존성.** 결과는 측정 시점의 특정 모델 스냅샷에 의존한다. 모델 버전이 바뀌면 재측정이 필요하며, 과거 수치를 다른 버전에 적용하지 않는다.
- **재현 불안정 가능성.** 동일 시드라도 모델 비결정성으로 수치가 재현되지 않을 수 있다. 그 경우 측정값을 단언하지 않고 "재현 불안정"으로 표기한다.

## 결정론 채점기 실측 — judge A + judge B (2026-06-14, 라이브 모델 불요분)

`python3 -m fablelayer.cli benchmark` 로 judge A(rubric 0-5 모사)와 judge B(rule 키워드 커버리지)를 같은 출력에 모두 적용해 fixture 3건으로 실증했다. 두 심판 점수는 **평균으로 합치지 않고** task 당 나란히 남긴다. 원자료 `bench/fixtures_raw.json`(각 run.raw 에 other_judge/other_score/delta/disagree 동봉).

| task_id | judge A (0-100) | judge B (0-100) | Δ | 불일치 |
|---|---|---|---|---|
| dbg-001 | 50.00 | 66.67 | 16.67 | no |
| disagree-001 | 50.00 | 100.00 | 50.00 | YES |
| extract-001 | 50.00 | 100.00 | 50.00 | YES |
| (mean) | A 50.00 | B 88.89 | — | 2/3 |

mean 은 같은 심판끼리만 집계한다(A 끼리, B 끼리). A↔B 를 하나의 수로 평균내지 않는다 — 불일치를 지우지 않기 위해서다. 갈린 case 는 위 "## 심판 불일치" 절에 자동 반영된다.

**해석 한계:** 이 수치는 judge A·B 채점기가 동작하고 불일치를 보존함을 증명할 뿐, baseline↔treatment 절차 효과 측정이 아니다(그 측정은 라이브 모델 호출 필요로 여전히 미완). capability 주장이 아니며 우위 주장으로 확장하지 않는다.

## 변경 이력

| 날짜 | 변경 | 사유 |
|------|------|------|
| 2026-06-14 | 초기 placeholder 작성 | 방법론·중립 채점표·재현 스크립트·원자료 스키마 완비. 라이브 측정은 환경 미가용으로 미완 표기, 합성 수치 미포함 |
| 2026-06-14 | judge B 결정론 채점기 fixture 실측 추가(mean 83.33) | `fablelayer/benchmark.py` 동작 증명. baseline/treatment 라이브 측정은 여전히 미완으로 정직 표기 |
| 2026-06-14 | judge A(rubric 0-5 모사) 추가 + A/B 불일치 보존(평균 비대체) | recover 축: 실패 비삭제. 두 심판을 같은 출력에 적용해 양쪽 점수를 raw 에 모두 남기고, `disagree-001` fixture 와 `cli benchmark` 가 "## 심판 불일치" 절을 실데이터로 자동 갱신 |
