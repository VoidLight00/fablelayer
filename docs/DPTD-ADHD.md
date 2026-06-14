# FableLayer DPTD-ADHD — 빠르게 이해하는 설치·사용 가이드

## 한 줄 요약

FableLayer는 AI 모델을 “더 똑똑하게 바꾸는 마법”이 아니라, **일을 끝까지 검증하게 만드는 작업 규율 세트**입니다.

설치해서 바로 확인할 수 있습니다.

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer
python3 tests/run_tests.py
bash gates/verify_fablelayer.sh . --mode new
```

## 먼저 알아야 할 것

### FableLayer가 하는 일

- 완료했다고 말하기 전에 증거를 요구합니다.
- 성능 수치를 근거 없이 쓰지 못하게 막습니다.
- private/non-public prompt text를 복사하지 못하게 막습니다.
- Claude Code, Ollama, LM Studio, SillyTavern용 profile을 만들 수 있습니다.
- 로컬에서 먼저 검증하고, 외부 공개는 승인 뒤에만 하게 만듭니다.

### FableLayer가 하지 않는 일

- 모델의 기본 지능을 바꾸지 않습니다.
- 특정 비공개 prompt를 복제하지 않습니다.
- 승인 없이 GitHub push, package publish, marketplace 등록을 하지 않습니다.
- benchmark 없이 “좋아졌다”고 주장하지 않습니다.

## 1단계 — 설치

터미널에서 실행합니다.

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer
```

필요한 것:

- Python 3.10 이상
- Bash
- Git

외부 Python package는 필요 없습니다.

## 2단계 — 작동 확인

아래 세 줄을 그대로 실행합니다.

```bash
python3 tests/run_tests.py
bash gates/selftest.sh
bash gates/verify_fablelayer.sh . --mode new
```

성공하면 대략 이런 문구가 보입니다.

```text
OK
SELFTEST PASS
VERIFY PASS
```

## 3단계 — CLI 보기

```bash
./cli/fablelayer --help
```

주요 명령은 이렇습니다.

| 명령 | 의미 |
|---|---|
| `init` | FableLayer profile을 프로젝트에 만들 준비를 합니다. |
| `init --apply` | 실제로 local profile 파일을 씁니다. |
| `upgrade sonnet` | Sonnet에 어떤 절차 layer를 붙일지 미리 봅니다. |
| `benchmark` | deterministic benchmark fixture를 실행합니다. |
| `check --file output.md` | 파일 안에 근거 없는 완료 주장이 있는지 봅니다. |
| `status` | 최근 run 상태를 봅니다. |
| `resume` | 끝나지 않은 run을 이어갈 준비를 합니다. |

## 4단계 — demo profile 만들기

안전하게 `_dist/demo`에 만들어 봅니다.

```bash
./cli/fablelayer init --target ./_dist/demo --apply
```

생성되는 것:

```text
_dist/demo/
├── .claude/skills/fablelayer-runtime/SKILL.md
├── ollama/...
├── lm-studio/...
└── sillytavern/...
```

`_dist/`는 git에 올라가지 않게 무시됩니다.

## 머릿속 모델

FableLayer는 네 층으로 보면 쉽습니다.

```text
PromptCore
  ↓
Procedure / Evidence Gate
  ↓
Router / Adapter
  ↓
Benchmark / Gates
```

### PromptCore

공개-safe 작업 규칙을 한 파일로 만듭니다.

### Evidence Gate

“완료했습니다” 같은 말을 할 때 증거가 있는지 봅니다.

### Router

작업이 복잡하면 더 강한 모델을 쓰라고 판단합니다. 단, 모델 능력이 옮겨진다고 말하지 않습니다.

### Benchmark / Gates

테스트, benchmark, license, publish 안전장치를 확인합니다.

## 자주 헷갈리는 지점

### “이거 설치하면 모델이 Fable처럼 되나요?”

아닙니다. 모델의 기본 capability는 그대로입니다. 대신 작업 절차를 더 빡빡하게 만들어서 모델이 자기 한계 안에서 더 일관되게 일하게 합니다.

### “private prompt가 들어 있나요?”

아닙니다. 그런 텍스트는 포함하지 않는 방향으로 설계했고, gate로도 막습니다.

### “그냥 public repo로 써도 되나요?”

네. 현재 public GitHub repo에서 clone할 수 있습니다. 다만 package registry나 marketplace 배포는 아직 별도 단계입니다.

### “뭘 먼저 읽으면 되나요?”

순서 추천:

1. `README.md`
2. `docs/INSTALL.md`
3. `docs/DPTD-ADHD.md`
4. `docs/DEVELOPMENT.md`
5. `INTERFACE.md`

## 작업 체크리스트

처음 설치한 사람은 이것만 확인하면 됩니다.

```text
[ ] git clone 성공
[ ] python3 tests/run_tests.py 성공
[ ] bash gates/verify_fablelayer.sh . --mode new 성공
[ ] ./cli/fablelayer --help 출력 확인
[ ] ./cli/fablelayer init --target ./_dist/demo --apply 실행
```

개발자는 이것까지 확인합니다.

```text
[ ] 변경 전 INTERFACE.md 확인
[ ] 테스트 추가
[ ] gates/selftest.sh 통과
[ ] gates/verify_fablelayer.sh 통과
[ ] README/docs 갱신
[ ] CHANGELOG 갱신
```

## 문제가 생겼을 때

### Python import가 안 됩니다

레포 루트에서 실행 중인지 확인합니다.

```bash
pwd
ls fablelayer
python3 -m fablelayer.cli --help
```

### gate가 실패합니다

실패한 gate 이름을 봅니다.

```text
LICENSE FAIL → source/attribution 문제
PERF FAIL → 근거 없는 성능 주장
BENCH FAIL → raw data/reproduce/한계 섹션 문제
RUNTIME FAIL → Python import/test/CLI 문제
PUBLISH FAIL → 승인 없는 공개 작업 차단. 정상일 수 있음
```

### publish gate가 실패합니다

승인 토큰 없이 실패하는 것이 정상입니다. FableLayer는 외부 공개 작업을 자동으로 하지 않게 설계되어 있습니다.

## 5분 루틴

시간이 없으면 이것만 실행합니다.

```bash
git clone https://github.com/VoidLight00/fablelayer.git
cd fablelayer
python3 tests/run_tests.py
bash gates/verify_fablelayer.sh . --mode new
./cli/fablelayer --help
```

여기까지 되면 설치와 기본 검증은 끝입니다.
