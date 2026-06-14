# RETRO — run 20260614-mvp-001

FL-AUDIT-003 산출물. run별 결정·리스크·다음 액션·증거를 남겨 실행 간 학습을 굳힌다.

## 결정
- PRD의 "Fable 5 capability 전이" 전제를 정찰 실측으로 보정 — capability 비전이, 절차만 전이. `perf_claim_gate`로 성능 단언 HARD 차단.
- 동작 Python 런타임 신설(`fablelayer/` 8모듈 + 98 단위테스트) — GPT-5.5 비교에서 드러난 최대 약점(동작 코드 부재) 정면 해소.
- 게이트를 9종으로 확장하고 런타임을 실행 배선(`runtime_gate.sh`) — markdown 명세만으로는 `--mode new` 통과 불가.
- 디렉토리 격리(`fablelayer-opus`) — FLOG-001 재발 방지를 `preflight_gate`(exit 4)로 코드 승격.

## 리스크 (남은 미완)
- bench 라이브 측정 미완: judge B 결정론 채점기는 fixture로 실증(mean 83.33)했으나, baseline↔treatment 절차 효과(paired)는 라이브 모델 호출 필요로 미측정. RESULTS.md 한계에 정직 표기.
- 외부 push/marketplace 미수행 — FL15/FL19 승인 게이트 뒤. 사용자 명시 승인 전 금지.
- P1 14건(CI GitHub Actions, RETRO 자동화, adapter 필수키 게이트, early-stop 음성커버리지) 미반영 — 선택.

## 다음 액션
1. 라이브 모델 벤치(baseline/treatment paired, n·노이즈 병기) 실측 → RESULTS 측정 슬롯 채움.
2. GitHub repo 생성 + `/plugin marketplace` 등록은 `publish_gate` 통과 + 사용자 승인 후.
3. P1 우선순위: GitHub Actions CI(run_tests+selftest) → adapter export 키 게이트 → RETRO 자동 생성.

## 증거 (실측)
- `gates/selftest.sh` 15/15 PASS (exit 0)
- `gates/verify_fablelayer.sh . --mode new` PASS (license/perf/bench/complete/render/runtime, exit 0)
- `python3 tests/run_tests.py` 98 tests OK
- `~/fable-forge/gates/fable_lint.sh` HARD=0 WARN=0 (FL8)
- import 7/7, cli 서브커맨드 4/4 exit 0, adapters export 5 파일, promptcore --check 드리프트 0
