# FableLayer — FAILURE_LOG

> FL12 산출물이다. 빌드·게이트·운영 중 발견된 결함을 누적 기록한다. 같은 결함이 2회 이상 재발하면 산문 기록에 머무르지 않고 **게이트 룰로 승격**한다. 승격은 사람의 판단이 아니라 게이트 스크립트의 exit code로 재발을 차단하는 단계까지 도달해야 완료된다(선언≠증거).

## 형식

각 항목은 다음 필드를 가진다.

- **ID**: `FLOG-NNN` 일련번호. 한번 부여하면 재사용하지 않는다.
- **증상**: 관측된 현상. 추정이 아니라 실측한 사실만 적는다.
- **원인**: 재현→가설경쟁→인과사슬로 확정한 근본 원인. 미확정이면 "미확정"으로 명시한다.
- **조치**: 이번 결함에 대해 실제로 적용한 수정. 적용 증거(파일 경로, exit code 등)를 동반한다.
- **승격**: 재발 방지를 위해 어느 게이트의 어느 룰로 올렸는지. 미승격이면 "미승격(1회 발생, 재발 시 승격 대상)"으로 명시한다.

## 승격 경로 (재발 패턴 → 게이트 룰)

재발 결함은 성격에 따라 아래 게이트 중 하나로 승격한다. 승격은 해당 게이트 스크립트에 검출 룰을 추가하고, fixtures에 fail 케이스를 넣어 `gates/selftest.sh`가 그 룰의 차단을 exit code로 증명할 때 완료된다.

| 재발 결함 성격 | 승격 대상 게이트 | 승격 판정 |
|---|---|---|
| leaked prompt 전문 유입, attribution/LICENSE/NOTICE 누락 | `gates/license_gate.sh` (FL7, exit 2) | fixture fail 케이스가 exit 2를 반환 |
| 미검증 성능 수치 단언, capability/procedure 구분 누락 | `gates/perf_claim_gate.sh` (FL9, exit 2) | fixture fail 케이스가 exit 2를 반환 |
| 벤치 원자료·한계섹션·재현스크립트 누락 | `gates/bench_integrity_gate.sh` (FL6, exit 2) | fixture fail 케이스가 exit 2를 반환 |
| 모드별 필수 산출물 누락, phase enum 위반 | `gates/completeness_gate.sh` (FL13, exit 3) | fixture fail 케이스가 exit 3을 반환 |
| FableLayer 생성물의 Opus fallback 유발 패턴 | `~/fable-forge/gates/fable_lint.sh` 의존(FL8) | 생성물 lint exit ≠ 0로 검출 |
| 멀티 에이전트 빌드 시 루트 공유 오염 | `gates/preflight_gate.sh` (FL17, exit 4) | fixture fail이 exit 4 반환 |
| plugin/marketplace JSON 무효·CLI 실패·dead 링크 | `gates/render_gate.sh` (FL18, exit 2) | fixture fail이 exit 2 반환 |
| 승인 없는 외부 publish/push/marketplace | `gates/publish_gate.sh` (FL15·FL19, exit 2) | 승인 토큰 부재 시 exit 2 |
| 위 게이트 통합 회귀 | `gates/verify_fablelayer.sh` (마스터 OR집계) | 하나라도 실패 시 비0 종료 |

운영 규칙: 위 표에 분류되지 않는 신규 성격의 재발 결함은 적합한 게이트가 없다는 뜻이다. 이 경우 새 게이트를 추가하고 `gates/verify_fablelayer.sh` OR집계에 배선한 뒤 이 표를 갱신한다. 임시 우회 스크립트로 대체하지 않는다.

## 로그

### FLOG-001 — 멀티 에이전트 동시 빌드 시 디렉토리 미격리로 작업물 오염

- **ID**: FLOG-001
- **증상**: 빌드 중 `cp` 머지로 같은 경로에 있던 다른 에이전트(GPT-5.5) 작업물이 덮어써져 오염되었다. 비교 실험 대상이던 두 에이전트의 산출물이 한 디렉토리에서 섞였다.
- **원인**: 비교 실험인데도 두 에이전트가 동일 루트를 공유했다. 머지(`cp`)가 동일 경로 파일을 덮어쓰는 기본 동작이라, 한쪽이 다른 쪽의 산출물을 그대로 지웠다. 루트 사전 점유 확인 없이 동시 쓰기를 허용한 것이 근본 원인이다.
- **조치**: 분리 디렉토리 원칙을 도입했다. 본 하네스는 전용 격리 루트를 단독 사용한다. 비교 실험은 디렉토리 격리를 전제로 한다 — 에이전트별로 루트를 분리하고 머지를 금지한다.
- **승격**: `gates/preflight_gate.sh`(FL17, exit 4)로 **승격 완료**. 빌드 시작 전 루트가 타 프로젝트/에이전트 작업물이면(REQUIREMENTS.md가 FableLayer 것이 아니거나 foreign `verify_*.sh` 존재) exit 4로 차단한다. fixtures `preflight_pass`(→0)/`preflight_fail`(→4)가 `gates/selftest.sh`에서 차단을 exit code로 증명한다(현재 13/13 PASS). soundness 감사(91, recover 축 -3)의 최대 갭을 이 게이트로 해소했다.
