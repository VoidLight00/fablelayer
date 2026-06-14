# FableLayer DPTD — Professional Technical Document

## 문서 목적

이 문서는 FableLayer를 처음 보는 개발자, 팀 리드, 오픈소스 검토자가 레포의 목적·설치·검증·확장 지점을 빠르게 이해하도록 만든 전문 기술 문서입니다.

FableLayer는 모델의 기본 지능을 바꾸는 도구가 아닙니다. 공개-safe 절차, 근거 기반 검증, 라우팅, 벤치마크, 배포 전 게이트를 하나의 레포로 묶은 로컬 우선 툴킷입니다.

## 1. 설치 가능 여부

다른 사용자도 설치할 수 있습니다. 현재 public GitHub 레포는 다음 경로입니다.

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer
```

필수 조건은 다음과 같습니다.

| 항목 | 요구사항 |
|---|---|
| Python | 3.10 이상 |
| Shell | Bash 호환 환경 |
| Git | clone 및 버전 관리 |
| 외부 Python dependency | 없음 |

기본 실행은 source checkout 기반입니다.

```bash
python3 -m fablelayer.cli --help
./cli/fablelayer --help
```

선택적으로 editable install도 가능합니다.

```bash
python3 -m pip install -e .
fablelayer --help
```

## 2. 빠른 검증

설치 후 아래 세 명령이 통과하면 로컬 런타임·테스트·게이트가 정상입니다.

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

검증 범위는 다음과 같습니다.

| 검증 | 설명 |
|---|---|
| `tests/run_tests.py` | 표준 라이브러리 기반 Python 테스트 전체 실행 |
| `gates/selftest.sh` | 게이트 fixture의 기대 exit code 검증 |
| `gates/verify_fablelayer.sh` | license, performance, benchmark, completeness, render, runtime 통합 검사 |

## 3. 핵심 구조

```text
fablelayer/
├── fablelayer/              # Python runtime
├── cli/                     # CLI entrypoint
├── gates/                   # fail-closed 검증 게이트
├── bench/                   # deterministic benchmark fixture와 raw 결과
├── adapters/                # Ollama / LM Studio / SillyTavern 문서 및 exporter
├── core/                    # PromptCore canonical output
├── docs/                    # 설치·개발·해설 문서
├── tests/                   # stdlib unittest suite
└── .claude-plugin/          # Claude Code plugin skeleton
```

## 4. 런타임 모듈

| 모듈 | 역할 |
|---|---|
| `promptcore.py` | 공개-safe 절차 profile을 결정론적으로 렌더링합니다. |
| `evidence_gate.py` | 근거 없는 완료 주장을 차단합니다. |
| `router.py` | 작업 난도와 실패 신호를 바탕으로 모델 라우팅 결정을 만듭니다. |
| `source_policy.py` | 출처 분류와 non-public source 차단 정책을 검사합니다. |
| `benchmark.py` | 결정론적 fixture scoring과 raw JSON 기록을 생성합니다. |
| `adapters.py` | Claude Code, Ollama, LM Studio, SillyTavern profile을 export합니다. |
| `cli.py` | `init`, `upgrade`, `benchmark`, `check`, `status`, `resume` 명령을 제공합니다. |

## 5. CLI 사용 예

```bash
./cli/fablelayer init
./cli/fablelayer init --target ./_dist/demo --apply
./cli/fablelayer upgrade sonnet
./cli/fablelayer benchmark
./cli/fablelayer check --file output.md
./cli/fablelayer status
./cli/fablelayer resume
```

기본 원칙은 local-first입니다. 외부 push, package publish, marketplace 등록은 일반 명령의 부작용으로 실행되지 않습니다.

## 6. Adapter export

프로젝트에 local profile을 생성하려면 다음을 실행합니다.

```bash
./cli/fablelayer init --target ./_dist/demo --apply
```

생성 대상은 다음 계열입니다.

| Runtime | 산출물 |
|---|---|
| Claude Code | `.claude/skills/fablelayer-runtime/SKILL.md` |
| Ollama | Modelfile 계열 profile |
| LM Studio | preset JSON |
| SillyTavern | character/profile JSON |

## 7. Public-safe 정책

FableLayer는 private, proprietary, non-public prompt text를 포함하지 않습니다. 공개 문서와 방법론 참조는 `ATTRIBUTION.md`에 기록하되, runtime bundle에는 복사하지 않습니다.

정책은 코드와 게이트로 강제됩니다.

```bash
bash gates/license_gate.sh .
bash gates/perf_claim_gate.sh .
bash gates/publish_gate.sh .
```

`publish_gate.sh`는 승인 토큰이 없으면 비정상 종료하는 것이 정상 동작입니다.

## 8. 개발 워크플로우

변경 전후로 다음을 실행합니다.

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

새 기능을 추가할 때의 기준은 다음과 같습니다.

1. 런타임 동작은 `fablelayer/*.py`에 둡니다.
2. 계약 변경은 `INTERFACE.md`에 먼저 반영합니다.
3. 테스트를 추가합니다.
4. 해당되는 게이트를 추가하거나 fixture를 갱신합니다.
5. README 또는 docs를 갱신합니다.
6. 검증 exit code를 보고합니다.

## 9. 현재 공개 버전의 한계

- public GitHub 설치와 로컬 실행은 가능합니다.
- marketplace 등록, PyPI 배포, release artifact 배포는 아직 수행하지 않았습니다.
- benchmark는 deterministic fixture 중심입니다. live paired benchmark를 공개 성능 주장으로 사용하려면 별도 실측이 필요합니다.
- source attribution은 보수적으로 reference-only 중심입니다.

## 10. 권장 다음 단계

| 우선순위 | 작업 |
|---|---|
| P0 | public README와 설치 절차가 실제 GitHub에서 잘 보이는지 확인 |
| P1 | GitHub Actions CI 첫 실행 결과 확인 |
| P1 | live benchmark protocol을 별도 문서로 분리 |
| P2 | PyPI packaging 여부 결정 |
| P2 | Claude Code plugin marketplace 등록 준비 |
