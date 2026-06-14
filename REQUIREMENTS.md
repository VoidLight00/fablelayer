# FableLayer — REQUIREMENTS (SSoT)

> 이 파일이 FableLayer **개발 하네스**의 단일 진실(SSoT)이다. 모든 게이트·QA·완전성 검증은 이 파일의 `FL` 번호를 기준으로 판정한다. 하네스가 만드는 산출물(FableLayer 제품)은 이 명세를 충족해야 한다.
>
> 근거 정찰(2026-06-14 verified, exit-code fail-closed):
> - `fivetaku/fablize` 48★ — ProcedureHarness 원천. **저자 실증 결론: 모델 capability는 전이 불가, 절차만 전이.**
> - `itsinseong/value-for-fable` 139★ — ValueOptimizer(VFF v2) 원천. **원판 벤치 재현 실패 → 중립 재검증: Sonnet+v2 ≈ Opus(동률), 0.30배 비용. 깊은 추론은 Opus 우세.**
> - `robzilla1738/supergoal` 478★ — 자율 빌드 루프 + adaptive phase + self-healing.
> - `ucsandman/context-handoff-bundle` 1★ — 세션 핸드오프 + drift detection.
> - `blocked non-public prompt source class` — high-risk source category(라이선스·재배포 권리 불명확 → 원문 포함 금지).

## 정체성 (PRD 전제의 실측 보정)

FableLayer는 **"모델을 Fable 5로 바꾸는 도구"가 아니다.** 정찰로 확인된 실측 근거상 그것은 불가능하다(capability 비전이). FableLayer는:

1. **절차·검증·출력구조 레이어** — Fable 5에서 *전이 가능하다고 실증된* 행동(verification grounding, 완결성 evidence gate, 체계적 조사, early-stop 방지, VFF 출력구조)을 Opus/Sonnet/Local LLM에 모듈로 주입한다.
2. **가성비 운영 구조** — Sonnet+구조로 Opus 근접 품질을 낮은 단가에 낸다(value-for-fable 실증 범위 내에서).
3. **정직한 벤치마크** — 성능 주장은 재현 가능한 실측과 한계 명시로만 한다. 마케팅 단언을 코드 게이트로 차단한다.

슬로건은 유지하되 정직하게: **"Fable is a discipline, not a capability transplant. We open-source the discipline — and the benchmark that proves its limits."**

## Functional Requirements

| ID | 요구사항 | 판정 방법 (이진) |
|----|---------|----------------|
| FL1 | **PromptCore (Layer 1)** — leaked prompt를 *전문 포함 없이* "inspired-by" 패턴으로 요약·구조 추출, `sgup/ai` Fable5.md + value-for-fable 8섹션을 병합해 버전 관리(V2/V3…). | `core/` 산출물 존재 + `license_gate.sh` PASS(전문 미포함) + 버전 디렉토리/파일 존재 |
| FL2 | **ProcedureHarness (Layer 2)** — fablize의 *실증 전이* 4절차: verification grounding(산출물 실행·관찰 후 완료), multi-story completion + evidence gate(근거 없는 "done" 거부), systematic investigation(재현→가설경쟁→인과사슬), early-stop 방지 hook. 2-pass review(옵션). | 절차별 산출물/hook 파일 4종 존재 + early-stop hook 셀프테스트 |
| FL3 | **ValueOptimizer (Layer 3)** — VFF v2 output-style 적용, COST optimizer(작업유형별 모델 라우팅), drift prevention, passive mode(항상 ON). **압축 규칙은 품질 부채이므로 도입 금지(value-for-fable v2 교훈).** | output-style 파일 존재 + COST 라우팅 규칙 문서 + grep "압축/compress" 강제 규칙 부재 |
| FL4 | **SkillPack & Router (Layer 4)** — supergoal(자율 빌드)·context-handoff(세션 재개)·skill-fable·Cheswick optimizer 통합 인터페이스 + Smart Model Router(Sonnet 기본→복잡 작업 Opus 자동 전환, 라우팅 기준 문서화). | 통합 매니페스트 + 라우터 규칙 파일 존재 |
| FL5 | **배포 3형태** — (a) Claude Code Plugin(`.claude-plugin/marketplace.json`+`plugin.json` 유효 JSON), (b) CLI(`fablelayer init`/`upgrade <model>`/`benchmark` 서브커맨드), (c) Local LLM Adapter(Ollama/LM Studio/SillyTavern config 생성기). | 3형태 산출물 존재 + plugin.json `python -m json.tool` 통과 + CLI usage 출력 |
| FL6 | **재현 가능 Benchmark Suite** — `bench/RESULTS.md` + 원자료(`raw.json` 등) + 재현 스크립트 + 중립 채점표·독립 심판 ≥2 방법론 + **`## 한계`/`## Limitations` 섹션 필수**. | `bench_integrity_gate.sh` PASS |
| FL7 | **라이선스/법적 (HARD)** — leaked prompt **전문 미포함**, 모든 소스 `ATTRIBUTION.md`에 기재(라이선스 상태 정직 표기: MIT/불명확 구분), `LICENSE`(AGPL-3.0)+`NOTICE` 존재. | `license_gate.sh` exit 2 차단 + ATTRIBUTION/LICENSE/NOTICE 존재 |
| FL8 | **Fallback-Zero** — FableLayer가 *생성하는* 프롬프트/에이전트 산출물은 Opus fallback 유발 패턴이 없어야 한다. 기존 `~/fable-forge/gates/fable_lint.sh`를 의존성으로 재사용(중복 구현 금지). | `verify_fablelayer.sh`가 fable_lint 호출 + 생성물 lint exit 0 |
| FL9 | **성능 주장 정직성 (HARD)** — "85%/90% similarity", "87점", "65% 절감" 등 수치 주장이 `bench/` 실측 참조(`[bench/...]` 링크) 없이 README/문서에 단언되면 차단. capability(전이불가) vs procedure(전이) 구분을 README에 명시. | `perf_claim_gate.sh` exit 2 + grep capability/procedure 구분 문구 |
| FL10 | **한국어·영어 완벽** — `README.md`(영어) + `README.ko.md`(한국어) 동시 유지. | 두 파일 존재 + 비어있지 않음 |
| FL11 | **RUN_MANIFEST** — 매 실행 `runs/<run_id>/RUN_MANIFEST.json`에 mode/입력/phase/게이트 결과 기록. phase는 canonical enum(`0-context/1-spec/2-build/3-gates/4-bench/5-report`)만. `resume`/`status` 지원. | 매니페스트 생성 + `completeness_gate.sh` phase enum 검사 |
| FL12 | **FAILURE_LOG** — 발견 결함이 `FAILURE_LOG.md`에 누적, 재발 패턴은 게이트 룰로 승격(경로 명시). | 파일 존재 + 승격 경로 문구 |
| FL13 | **완전성 게이트 (fail-closed)** — 매 실행 마지막에 모드별 필수 산출물 존재 검증, 누락 시 exit 3. | `completeness_gate.sh` 존재 + 셀프테스트(pass→0, fail→3) |
| FL14 | **부가 기능 범위 관리** — Web Dashboard / Community Marketplace / LoRA는 MVP 범위 밖. `ROADMAP.md`에 Phase별 명시적 defer. 미구현을 "구현됨"으로 보고 금지. | `ROADMAP.md`에 Phase 0/1/2 구분 + defer 항목 명시 |
| FL15 | **안전·승인 경계 (HARD-by-policy)** — GitHub repo 생성, push, `/plugin marketplace` 공개 등록, PR 자동 merge는 **사용자 명시 승인 게이트 뒤에서만**. submodule/fork 연결도 승인 후. | 파이프라인 SKILL.md에 승인 게이트 단계 명시 + 기본 동작은 로컬 산출물만 |
| FL16 | **건전성 ≥90** — 하네스 자체가 `harness-soundness` 루브릭 ≥90 / verdict `sound`. | `harness-soundness-auditor` 채점 결과 |
| FL17 | **preflight 단독점유 (HARD)** — 빌드 시작 전 루트가 타 프로젝트/에이전트 작업물인지 검사, 충돌 시 exit 4. FLOG-001(병렬 빌드 머지 오염) 재발 방지. | `preflight_gate.sh` 셀프테스트(pass→0, foreign→4) |
| FL18 | **render/실행 충실도 (HARD)** — plugin/marketplace JSON 유효성, CLI usage exit 0, README의 `bench/` 링크 실재 검증, 위반 시 exit 2. | `render_gate.sh` 셀프테스트 + 마스터 OR집계 배선 |
| FL19 | **publish 승인 게이트 (HARD)** — 외부 publish는 전 게이트 green + 승인 토큰(`runs/<id>/APPROVED` 또는 `--approved`) 존재 시에만 exit 0. FL15를 SOFT→HARD 승격. | `publish_gate.sh` 셀프테스트(승인 부재→2) |
| FL20 | **runtime 무결성 (HARD)** — `fablelayer/*.py` syntax(compileall)·import 무결성 + `tests/run_tests.py` 통과 + CLI 서브커맨드(--help/status) 실행. markdown 명세만으로 `--mode new` PASS 금지(runnable 요건). 위반 시 exit 2. | `runtime_gate.sh` 셀프테스트(pass→0, syntax err→2) + 마스터 배선 + completeness new에 fablelayer/*.py·tests·pyproject 요구 |

## Non-Functional Requirements

| ID | 요구사항 |
|----|---------|
| NFR1 | 하네스 루트는 `~/projects/fablelayer/`. 제품 산출물도 같은 루트(core/ styles/ skills/ agents/ bench/ cli/ adapters/). |
| NFR2 | 에이전트 정의는 `~/projects/fablelayer/.claude/agents/fablelayer-*`, 스킬은 `~/projects/fablelayer/.claude/skills/fablelayer-*`. |
| NFR3 | SKILL.md 본문 500줄 이내, 상세는 references/로 분리. |
| NFR4 | 게이트 판정은 스크립트 exit code로만(자가보고 금지). macOS bash 3.2 안전(빈 배열 가드, bytes decode), fail-closed(`|| echo 0` 금지, OR집계 rc≠0 전부 실패). |
| NFR5 | 기본 동작은 외부 push/deploy 없음 — 전부 로컬 산출물. 외부 작업은 FL15 승인 게이트 뒤. |
| NFR6 | 모든 에이전트는 `model: opus` (하네스 품질은 추론력에 직결). |

## 모드 정의

| 모드 | 입력 | 필수 산출물 |
|------|------|------------|
| `new` | (없음/PRD) | 제품 스캐폴드 전체(core/styles/skills/agents/bench/cli/adapters) + 게이트 PASS |
| `layer <1-4>` | 레이어 번호 | 해당 Layer 산출물 + 관련 게이트 PASS |
| `bench` | (없음) | `bench/RESULTS.md` + 원자료 + 재현 스크립트, `bench_integrity_gate` PASS |
| `package` | 형태(plugin/cli/adapter) | 해당 배포 산출물, `license_gate`+`perf_claim_gate` PASS |
| `audit` | 경로 | `runs/<id>/audit-report.md` + 전 게이트 exit code |
| `status`/`resume` | run_id | 매니페스트 기반 보고/재개 |
| `publish` | run_id | **FL15 승인 게이트** → repo/push/marketplace (승인 시에만) |

## 게이트 맵 (HARD = exit code 차단)

| 게이트 | 대상 FL | 성격 | exit |
|--------|---------|------|------|
| `gates/license_gate.sh` | FL7 | HARD | leaked 전문 발견/attribution·LICENSE 누락 시 2 |
| `gates/perf_claim_gate.sh` | FL9 | HARD | 미검증 성능 단언 시 2 |
| `gates/bench_integrity_gate.sh` | FL6 | HARD | RESULTS·원자료·한계섹션·재현스크립트 누락 시 2 |
| `gates/completeness_gate.sh` | FL13 | HARD | 모드별 필수 산출물 누락 시 3 |
| `gates/preflight_gate.sh` | FL17 | HARD | 루트 타 작업물 점유 시 4 |
| `gates/render_gate.sh` | FL18 | HARD | JSON 무효/CLI 실패/dead 링크 시 2 |
| `gates/runtime_gate.sh` | FL20 | HARD | import/syntax 실패·테스트 실패·CLI 비0 시 2 |
| `gates/publish_gate.sh` | FL15·FL19 | HARD | 승인 토큰 부재/게이트 미green 시 2 |
| `gates/verify_fablelayer.sh` | 마스터 | HARD | license/perf/bench/complete/render + fable_lint(FL8) OR집계, 하나라도 실패 시 비0 |

## 변경 이력

| 날짜 | 변경 | 사유 |
|------|------|------|
| 2026-06-14 | 초기 작성 | 하네스 신규 구축. PRD 전제(capability 전이)를 정찰 실측으로 보정 — FL9(성능 단언 차단)·FL7(라이선스 HARD)·FL6(벤치 무결성) 신설 |
| 2026-06-14 | FL17(preflight)·FL18(render)·FL19(publish) 신설, FLOG-001을 preflight_gate로 승격, 마스터에 render_gate 배선 | soundness 91 감사 상위 3갭 보강(recover/verify/extend) |
| 2026-06-14 | FL20(runtime 무결성) 신설 — 동작 Python 런타임(fablelayer/ 8모듈 + 98 단위테스트) 구현 후 게이트 실행배선, completeness new에 runnable 요건 추가, judge B 벤치 실측 | GPT-5.5 비교 최대 약점(동작코드 부재) 해소, 개선 발굴 P0 16건 반영 |
