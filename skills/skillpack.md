# FableLayer SkillPack — 통합 매니페스트 (Layer 4 / FL4)

> 이 매니페스트는 네 개의 외부 패턴(supergoal·context-handoff·skill-fable·Cheswick optimizer)을
> **코드 복사 없이 inspired-by**로 재구성해 하나의 인터페이스로 묶는다. 각 패턴에서 가져오는 것은
> *절차·구조*이며 모델 capability가 아니다 — Fable 5에서 전이 가능하다고 실증된 것은 절차뿐이다(REQUIREMENTS.md 정체성 절).
>
> 출처·라이선스 상태의 단일 진실은 루트 `ATTRIBUTION.md`다. 이 파일은 그 항목을 참조하며,
> ATTRIBUTION에 없는 소스를 새로 끌어오지 않는다(`gates/license_gate.sh`가 출처 누락·전문 포함을 HARD 차단).

## 무엇을 묶는가 (그리고 묶지 않는가)

SkillPack은 FableLayer가 주입하는 **절차 모듈의 진입점**이다. 묶는 대상은 다음 네 가지 *행동 패턴*이고, 각각에서 우리가 재구현하는 범위를 표로 못박는다. capability(추론력·지식)는 어떤 패턴으로도 옮기지 않는다.

| 패턴 | 출처 (ATTRIBUTION 항목) | 라이선스 상태(2026-06-14, 통합 직전 LICENSE 원문 재확인) | 가져오는 절차/구조 | 우리 재구현 범위 | 진입 트리거 |
|------|------------------------|----------------------------------------------------------|--------------------|------------------|-------------|
| supergoal | `robzilla1738/supergoal` | LICENSE 존재(원문 재확인 필요) | 자율 빌드 루프의 *진행 판정 구조*: adaptive phase 전환, self-healing 재시도 경계 | 우리 phase enum(`0-context`/`1-spec`/`2-build`/`3-gates`/`4-bench`/`5-report`)에 매핑한 진행 판정만 재구현. 빌드 루프 코드는 복사하지 않는다. 완료 판정은 게이트 exit code(FL2 evidence gate)로만 한다 | "자율로 끝까지 빌드", "막히면 스스로 복구", `new` 모드 전 단계 |
| context-handoff | `ucsandman/context-handoff-bundle` | README MIT 배지(원문 재확인 필요) | 세션 재개의 *상태 직렬화 구조*: 핸드오프 번들, drift detection | `runs/<run_id>/RUN_MANIFEST.json`(FL11) 기반 상태 스냅샷 직렬화/복원만 재구현. 매니페스트의 단일 owner는 conductor다 | "이어서", "resume", "세션 재개", "이전 결과 기반" |
| skill-fable | `sgup/ai`(Fable5 operating profiles 구조 참조) + `itsinseong/value-for-fable`(VFF v2 output-style) | sgup/ai 라이선스 불명확(구조 참조만) / value-for-fable LICENSE+NOTICE 존재(재확인 필요) | Fable5 operating profile의 *섹션 골격*과 VFF v2 출력구조를 절차 모듈로 노출 | Layer 1(`core/promptcore.md`)·Layer 3(`styles/vff-v2.md`) 산출물을 SkillPack에서 호출하는 어댑터만. 원문 프로파일·leaked 프롬프트 전문은 포함하지 않는다(패턴 요약만) | "Fable 절차 적용", "출력구조 주입", `layer 1`/`layer 3` |
| Cheswick optimizer | `CheswickDEV/claude-fable-5-prompt-optimizer` | 라이선스 불명확(개념 참조만) | source-backed 프롬프트 개선 룰의 *접근 개념*(근거 있는 룰만 적용) | 개념 참조만. 룰셋 코드·룰 본문을 복사하지 않고, "근거 없는 룰 미적용" 원칙을 Layer 3 drift 방지와 정렬해 노출 | "프롬프트 최적화", "근거 기반 개선" |

명시적 비범위: Web Dashboard·Community Marketplace·LoRA는 MVP 밖이다(FL14, `ROADMAP.md` 참조). SkillPack은 이들을 "구현됨"으로 노출하지 않는다.

## 통합 인터페이스

SkillPack은 네 패턴을 하나의 진입 표면으로 노출한다. 각 항목은 *어디로 위임하는지*를 명시하고, 실제 산출물은 해당 Layer가 소유한다(이 파일은 인덱스이지 구현이 아니다).

| 인터페이스 항목 | 위임 대상 | 산출물 위치 |
|----------------|-----------|-------------|
| 자율 빌드 진행 판정 | conductor 파이프라인의 phase 진행 + evidence gate | `runs/<run_id>/RUN_MANIFEST.json`, `gates/completeness_gate.sh` |
| 세션 재개 / 상태 복원 | conductor의 resume/status 모드 | `runs/<run_id>/RUN_MANIFEST.json`(FL11) |
| Fable 출력구조 주입 | Layer 1 PromptCore + Layer 3 ValueOptimizer | `core/promptcore.md`, `styles/vff-v2.md` |
| 모델 라우팅 결정 | 이 디렉토리의 `router.md`(Smart Model Router) | `skills/router.md` |
| 근거 기반 개선 원칙 | Layer 3 drift 방지 규칙 | `styles/vff-v2.md` |

라우팅 결정은 단일 출처를 둔다: `skills/router.md`. Layer 3의 COST optimizer와 라우팅 기준이 갈라지면 어느 한쪽이 조용히 무시되므로, router.md와 Layer 3 COST 규칙은 같은 신호·같은 분기를 쓰도록 정렬한다. 충돌 시 conductor가 우선순위를 결정한다.

## 원칙 (게이트 정합)

- **inspired-by only.** 위 어떤 소스에서도 코드·룰 본문·leaked 프롬프트 전문을 복사하지 않는다. 패턴·구조·접근 개념만 재구현한다(`license_gate.sh` HARD).
- **압축 규칙 부재.** SkillPack과 그 하위 인터페이스에 "압축/compress" 강제 규칙을 두지 않는다. value-for-fable v2 교훈상 출력 압축은 품질 부채다(FL3). 토큰 절감은 출력 축소가 아니라 `router.md`의 모델 라우팅으로 달성한다.
- **수치 단언 금지.** SkillPack 문서는 성능 우위를 수치로 단언하지 않는다("N% 절감"·"M점"). 정성 서술(우세/동률 범위)과 `bench/` 실측 참조로만 표현한다(FL9). 근거 한계는 `router.md`에 명시한다.
- **fallback-zero 전제.** SkillPack이 노출하는 절차 모듈 텍스트는 Opus fallback 유발 패턴을 넣지 않는다(FL8). 작성 후 `~/fable-forge/gates/fable_lint.sh`(의존성 재사용) 셀프 검증 대상이다.
- **자가보고 금지.** 통합 정합 여부는 conductor가 `gates/license_gate.sh`·`gates/perf_claim_gate.sh`·`gates/completeness_gate.sh` exit code로 판정한다. 이 매니페스트의 서술은 증거가 아니다(NFR4).
