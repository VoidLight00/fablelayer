# FableLayer — ROADMAP (FL14 범위 관리)

> 이 문서는 REQUIREMENTS.md(SSoT)의 **FL14**를 충족한다. FableLayer 제품의 구현 범위를 Phase로 구분하고, MVP 범위 밖 기능을 명시적으로 defer한다.
>
> **보고 무결성 규칙(HARD)**: 미구현 항목을 "구현됨"으로 보고하지 않는다. 각 Phase의 항목 상태는 산출물 존재와 게이트 exit code로만 판정한다(자가보고 금지, NFR4). Phase 2 항목은 코드/문서가 존재하지 않으므로 어떤 산출물·README·벤치에서도 "지원함/완료됨"으로 기술하지 않는다.

## 범위 판정의 근거 (정찰 실측 반영)

Phase 구분은 PRD의 야망이 아니라 정찰 실측으로 검증된 전이 가능성에 따른다.

- 모델 capability는 하네스로 전이되지 않는다. 전이되는 것은 절차뿐이다(verification grounding, multi-story completion + evidence gate, systematic investigation, early-stop 방지). 그러므로 MVP는 **절차 레이어와 그 한계를 증명하는 벤치**에 집중한다. 모델 교체를 시사하는 기능(LoRA 학습 등)은 capability 영역이므로 별도 Phase로 분리한다.
- value-for-fable 중립 재검증 결과 Sonnet+v2 출력구조가 Opus와 노이즈 내 동률, 출력비 0.30배였다. 따라서 가성비 운영(ValueOptimizer)은 MVP에 포함한다. 단, 깊은 추론에서 Opus가 우세하므로 Smart Model Router는 단순 라우팅으로 시작하고 정교화는 Phase 1로 미룬다.
- 원판 벤치가 원자료 분실로 재현 실패한 사례가 있으므로, MVP의 벤치는 원자료·재현 스크립트·한계 섹션을 동봉한다(FL6). 대규모 공개 리더보드·커뮤니티 제출은 운영 비용이 크므로 Phase 2로 미룬다.

## Phase 0 — MVP (현재 범위)

목표: 절차·검증·출력구조 레이어를 로컬 산출물로 완성하고, 그 한계를 정직한 벤치로 증명한다.

| 항목 | 대응 FL | 산출물 | 완료 판정 |
|------|--------|--------|----------|
| PromptCore (Layer 1) | FL1 | `core/` (inspired-by 패턴 요약, 버전 디렉토리) | `license_gate.sh` PASS + 버전 파일 존재 |
| ProcedureHarness (Layer 2) | FL2 | 4절차 산출물/hook + early-stop hook 셀프테스트 | hook 파일 4종 + 셀프테스트 exit 0 |
| ValueOptimizer (Layer 3) — VFF v2 | FL3 | output-style 파일 + COST 라우팅 규칙 문서 | output-style 존재 + 압축 규칙 부재 grep |
| CLI 스캐폴드 (init만) | FL5(b) | `fablelayer init` 서브커맨드 | CLI usage 출력 |
| Claude Code Plugin | FL5(a) | `.claude-plugin/marketplace.json` + `plugin.json` | `python -m json.tool` 통과 |
| 라이선스/법적 | FL7 | `ATTRIBUTION.md` + `LICENSE`(AGPL-3.0) + `NOTICE` | `license_gate.sh` exit 2 차단 동작 |
| Fallback-Zero | FL8 | 생성물 lint (`fable_lint.sh` 재사용) | `verify_fablelayer.sh` fable_lint 호출 + exit 0 |
| 성능 주장 정직성 | FL9 | README capability/procedure 구분 문구 | `perf_claim_gate.sh` exit 2 차단 동작 |
| 한국어·영어 README | FL10 | `README.md` + `README.ko.md` | 두 파일 비어있지 않음 |
| RUN_MANIFEST / FAILURE_LOG | FL11, FL12 | `runs/<run_id>/RUN_MANIFEST.json`, `FAILURE_LOG.md` | 매니페스트 생성 + 승격 경로 문구 |
| 완전성 게이트 | FL13 | `completeness_gate.sh` | 셀프테스트 pass→0, fail→3 |
| 범위 관리 문서 | FL14 | 이 `ROADMAP.md` | Phase 0/1/2 구분 + defer 명시 |
| 안전·승인 경계 | FL15 | 파이프라인 SKILL.md 승인 게이트 단계 | 기본 동작 로컬 산출물만 |

Phase 0 정의에서 SkillPack & Router(FL4)는 통합 매니페스트와 단순 라우터 규칙까지만 MVP에 포함한다. Smart Model Router의 정교한 작업유형 분류는 Phase 1로 미룬다.

## Phase 1 — 운영 확장

목표: MVP를 실사용 가능한 도구로 확장한다. 모두 절차/운영 영역이며 capability 전이를 시도하지 않는다.

| 항목 | 대응 FL | 비고 |
|------|--------|------|
| CLI 전체 서브커맨드 | FL5(b) | `upgrade <model>` / `benchmark` 추가 (Phase 0은 `init`만) |
| Local LLM Adapter | FL5(c) | Ollama / LM Studio / SillyTavern config 생성기 |
| 재현 가능 Benchmark Suite | FL6 | `bench/RESULTS.md` + 원자료 + 재현 스크립트 + 독립 심판 ≥2 + 한계 섹션. `bench_integrity_gate.sh` PASS |
| Smart Model Router 정교화 | FL4 | 작업유형별 모델 라우팅 기준 정밀화. 깊은 추론은 Opus로 라우팅(value-for-fable 실측 반영) |

Phase 1 항목은 Phase 0 게이트가 전부 통과한 뒤에 착수한다. 벤치는 Phase 0의 정직성 게이트(FL9)와 결합되어야 의미가 있으므로 Phase 1에서 실측을 채운다.

## Phase 2 — 명시적 Defer (MVP 범위 밖)

목표: 아래 항목은 MVP에서 구현하지 않는다. 운영 비용·capability 영역·외부 의존성 때문에 의도적으로 미룬다. **현재 산출물·README·벤치 어디에도 이 항목을 구현됨으로 기술하지 않는다.**

| 항목 | defer 사유 |
|------|-----------|
| Web Dashboard | 호스팅·인증·상태 관리 운영 비용. MVP는 로컬 CLI/플러그인으로 충분히 검증 가능하다. |
| Community Marketplace | 사용자 제출·검수·라이선스 검증·모더레이션 파이프라인이 필요하다. FL7(라이선스 HARD)을 외부 기여물까지 강제하는 별도 게이트 설계 선행이 필요하다. |
| LoRA / 파인튜닝 | **capability 영역.** 정찰 실증상 capability는 하네스로 전이 불가다. LoRA는 모델 가중치를 바꾸는 작업으로, 절차 레이어인 FableLayer의 정체성과 다른 축이다. 별도 연구 트랙으로 분리하며, 채택 여부는 재현 가능한 실측이 선행되어야 한다. |
| 공개 리더보드 / 대규모 벤치 제출 | 원자료 보존·중립 채점 운영 비용. 원판 벤치가 원자료 분실로 재현 실패한 전례가 있어, 운영 인프라 없이 공개하면 같은 부채를 반복한다. |

### Defer 항목 보고 규칙

- 이 항목들이 구현되지 않은 상태에서 "FableLayer는 웹 대시보드/마켓플레이스/LoRA를 지원한다"고 쓰면 FL14 위반이다.
- Phase 2 항목을 Phase 0/1로 승격할 때는 REQUIREMENTS.md 변경 이력에 사유를 기록하고, 해당 항목 전용 게이트(존재·동작 검증)를 추가한 뒤에만 "구현됨"으로 보고한다.
- `completeness_gate.sh`는 모드별 필수 산출물에 Phase 2 항목을 포함하지 않는다. Phase 2 산출물 부재는 결함이 아니라 설계된 범위다.

## Phase 전이 기준

| 전이 | 선행 조건 |
|------|----------|
| Phase 0 → Phase 1 | `verify_fablelayer.sh` exit 0 (license/perf_claim/completeness/fable_lint OR집계 전부 통과) |
| Phase 1 → Phase 2 | `bench_integrity_gate.sh` PASS + 실측 RESULTS 동봉 + FL16 건전성 ≥90 |
| Phase 2 항목 승격 | REQUIREMENTS.md 변경 이력 기록 + 항목 전용 게이트 추가 + 승격 후 산출물 존재 검증 |
