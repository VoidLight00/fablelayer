# FableLayer Benchmark Suite (`bench/`)

이 디렉토리는 FableLayer가 주입하는 **절차 레이어**의 효과를 재현 가능하고 정직하게 측정하기 위한 자료다(FL6). 측정 대상은 모델 capability가 아니라 절차의 전이 효과다. capability는 하네스로 전이되지 않으므로(capability 비전이), 이 벤치는 "Fable 5로 바꿔준다"식 주장을 측정하지도 기술하지도 않는다.

## 파일

| 파일 | 역할 |
|------|------|
| `RESULTS.md` | 방법론(블라인드·중립 베이스라인·독립 심판 ≥2·ablation), 측정 슬롯, 심판 불일치 기록, `## 한계` 섹션 |
| `raw.json` | 원자료 스키마 + placeholder run. 프롬프트·출력·점수·시드·모델버전을 run 단위로 누적(append-only) |
| `reproduce.sh` | 재현 절차 스크립트. macOS bash 3.2 안전. 모델 호출은 스텁(`run_model`)으로 안내 |
| `README.md` | 이 파일 |

## 현재 상태

초기 placeholder다. 라이브 모델 호출 측정은 환경 미가용으로 미완이다. 방법론·중립 채점표·재현 스크립트·원자료 스키마는 완비했고, 측정값 칸은 측정이 가능해지면 `reproduce.sh`로 채운다. 합성된 가짜 수치는 넣지 않는다. 현재 단언 가능한 성능 수치는 없다.

## 사용법

```bash
bash bench/reproduce.sh --help      # 사용법
bash bench/reproduce.sh --dry-run   # 모델 호출 없이 raw.json 스키마·측정 매트릭스 점검
bash bench/reproduce.sh --run       # 라이브 측정 (run_model 을 실제 엔드포인트에 배선해야 동작)
```

`--run` 은 `run_model()` 이 스텁(sentinel 87)인 동안에는 비0으로 중단하고 `raw.json` 을 건드리지 않는다 — 합성 수치를 만들지 않기 위한 fail-closed 설계다.

## 측정 원칙 (왜 이렇게 설계했나)

- **capability vs procedure 구분.** baseline/treatment는 같은 모델을 쓴다. 측정되는 차이는 절차 효과로 귀속되며, 모델 추론력 향상이 아니다.
- **블라인드·중립 베이스라인.** 채점자는 적용/미적용을 모른다(`label_hidden`). 동일 모델 대조군으로 절차 효과만 분리한다.
- **독립 심판 ≥2.** judge A(rubric 정량) + judge B(규칙 결정론). 불일치는 평균으로 덮지 않고 둘 다 남긴다.
- **원자료 보존.** run 단위 append-only. 원자료 분실이 value-for-fable 원판 벤치 재현 실패의 직접 원인이었다.

## 게이트

이 디렉토리는 `gates/bench_integrity_gate.sh` 의 대상이다. `RESULTS.md` + 원자료(`*.json`) + 재현 스크립트(`*.sh`/`*.js`/`*.py`) + `## 한계` 섹션이 모두 있어야 PASS다(누락 시 exit 2). 수치 표현은 `gates/perf_claim_gate.sh` 의 차단 패턴(근거 없는 성능 단언)에 걸리지 않게 측정값+근거 참조+한계 병기로만 기술한다.

```bash
bash gates/bench_integrity_gate.sh .   # PASS / FAIL(2)
bash gates/perf_claim_gate.sh .        # PASS / FAIL(2)
```
