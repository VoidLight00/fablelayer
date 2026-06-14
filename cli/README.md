# FableLayer CLI

FableLayer 배포 3형태 중 (b) CLI. 단일 진입점 `cli/fablelayer` 는 POSIX/bash 스크립트이며 macOS의 bash 3.2 에서 동작하도록 작성했다. 추가 런타임 의존성은 없다(서브커맨드 `benchmark` 가 실행하는 재현 스크립트만 그 언어 런타임을 요구한다).

## 정직성 경계

이 CLI 가 설치하는 것은 **전이 가능한 절차·출력구조 레이어**다. 모델의 **capability 는 전이하지 않는다**. 정찰 실측상 capability 비전이가 결론이며, 전이되는 것은 절차(procedure)뿐이다.

- 전이되는 절차: verification grounding(산출물 실행·관찰 후 완료), evidence gate(근거 없는 "done" 거부), systematic investigation(재현 → 가설 경쟁 → 인과 사슬), early-stop 방지, VFF 출력구조.
- 전이되지 않는 것: 모델 자체의 추론력·지식·생성 품질. 이 부분은 설치로 바뀌지 않는다.

성능 수치(유사도·점수·절감률)는 이 CLI 의 어떤 출력에도 단언하지 않는다. 측정값은 `bench/RESULTS.md` 의 한계(`## 한계`) 명시와 함께만 해석한다.

## 설치 / 실행

스크립트는 그 자체로 실행 가능하다.

```sh
chmod +x cli/fablelayer
./cli/fablelayer --help
```

PATH 에 두려면 심볼릭 링크보다 디렉토리를 직접 가리키는 편이 안전하다.

```sh
ln -s "$(pwd)/cli/fablelayer" /usr/local/bin/fablelayer
```

## 명령

| 명령 | 동작 | 기본 모드 |
|------|------|-----------|
| `fablelayer init` | 현재 프로젝트(또는 `--target DIR`)의 `.fablelayer/` 아래에 존재하는 절차 레이어(`core/ styles/ skills/ agents/ adapters/`)를 복사하고 `MANIFEST` 를 기록 | dry-run |
| `fablelayer upgrade <model>` | 대상 모델 라우팅 설정을 `.fablelayer/routing.<model>.conf` 로 작성. `<model>` = `opus` \| `sonnet` \| `local` | dry-run |
| `fablelayer benchmark` | `bench/` 의 재현 스크립트(`*.sh` \| `*.js` \| `*.py` \| `*.mjs`)를 찾아 실행하고 그 출력을 그대로 표시 | 즉시 실행(읽기) |

인자 없이 호출하면 usage 를 출력하고 종료 코드 0 으로 끝난다.

### 전역 옵션

| 옵션 | 의미 |
|------|------|
| `--apply` | 파괴적 동작(파일 쓰기)을 실제로 수행. 없으면 dry-run(미리보기만). |
| `--target DIR` | `init`/`upgrade` 의 대상 디렉토리. 기본은 현재 작업 디렉토리. |
| `-h`, `--help` | 도움말 출력 후 종료(0). |
| `-V`, `--version` | 버전 출력 후 종료(0). |

## dry-run 과 --apply

파일을 쓰는 동작(`init`, `upgrade`)은 기본적으로 **dry-run** 이다. 무엇을 어디에 쓸지 미리 보여줄 뿐 실제로 쓰지 않는다. 실제 적용은 `--apply` 를 붙일 때만 일어난다.

```sh
fablelayer init                       # 무엇을 설치할지 미리보기
fablelayer init --apply               # 현재 프로젝트에 실제 설치
fablelayer init --target ./my-app --apply

fablelayer upgrade sonnet             # 라우팅 설정 미리보기
fablelayer upgrade sonnet --apply     # routing.sonnet.conf 작성
```

`benchmark` 는 측정(읽기)이며 `--apply` 가 필요 없다. 결과 파일을 새로 쓰지 않고, 재현 스크립트의 출력만 그대로 전달한다.

## 종료 코드

| 코드 | 의미 |
|------|------|
| 0 | 정상(usage 출력, dry-run, 적용 성공, benchmark 성공) |
| 1 | 실행 중 실패(디렉토리 생성/복사 실패, 재현 스크립트 부재 또는 실패) |
| 2 | 사용 오류(알 수 없는 명령/옵션, 모델 누락/미지원, 대상 디렉토리 부재) |

종료 코드는 자가보고가 아니라 실제 실행 결과다. CI 에서 그대로 판정에 쓸 수 있다.

## 선행 레이어 부재 처리

이 CLI 는 레이어를 **발명하지 않는다**. `core/ styles/ skills/ agents/ adapters/` 중 아직 생성되지 않은 레이어가 있으면 `[없음]` 으로 정직하게 표시하고, 존재하는 레이어만 설치 대상으로 삼는다. `benchmark` 도 `bench/` 또는 재현 스크립트가 없으면 그 사실을 보고하고 비0 으로 끝난다(없는 측정을 만들어내지 않는다).

## 안전 경계

- 외부 작업(`git push`, `npm publish`, `/plugin marketplace` 공개 등록, repo 생성)은 이 CLI 가 수행하지 않는다. 그런 동작은 FL15 승인 게이트(파이프라인 conductor)의 책임이다.
- 파괴적 동작은 항상 `--apply` 뒤에서만 일어난다.
- 설치 산출물(`.fablelayer/`)에 leaked prompt 전문을 포함하지 않는다. inspired-by 패턴 요약·구조만 다룬다.

## 검증

작성 후 다음을 실제 실행해 확인했다(증거는 종료 코드).

```sh
bash -n cli/fablelayer          # 구문 검사: rc 0
cli/fablelayer                  # usage 출력, rc 0
cli/fablelayer --help           # rc 0
cli/fablelayer | grep -cE '^  (init|upgrade|benchmark) '   # 3 (서브커맨드 3종 노출)
cli/fablelayer upgrade          # 모델 누락 → rc 2
cli/fablelayer upgrade gpt5     # 미지원 모델 → rc 2
cli/fablelayer frobnicate       # 알 수 없는 명령 → rc 2
```

## 관련 요구사항

- FL5 — 배포 3형태 중 CLI 진입점과 서브커맨드(`init`/`upgrade`/`benchmark`).
- FL9 — 성능 수치 단언 금지. capability(전이 불가) vs procedure(전이) 구분 유지.
- FL15 / NFR5 — 기본 동작은 로컬 산출물만. 외부 작업은 승인 게이트 뒤.
