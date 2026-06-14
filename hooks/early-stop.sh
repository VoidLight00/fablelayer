#!/usr/bin/env bash
# early-stop.sh — 조기 종료(약속-미실행 / 범위 임의 축소) 결정론 감지 hook.
#
# FableLayer 절차 4(early-stop prevention) 구현. 모델 출력에서 "X 하겠다"고
# 선언만 하고 실제로는 하지 않은 채 끝맺는 패턴, 또는 명시 범위를 임의로
# 줄이는 패턴을 감지하면 종료 코드 비0으로 차단한다(fail-closed).
#
# 판정은 종료 코드로만 한다(NFR4). 산문 경고를 신뢰 근거로 쓰지 않는다.
#
# 사용법:
#   early-stop.sh "검사할 텍스트"        # 텍스트 직접 전달
#   early-stop.sh --file <경로>          # 파일 내용 검사
#   echo "텍스트" | early-stop.sh        # stdin 검사
#
# 종료 코드:
#   0  조기 종료 패턴 없음(통과)
#   2  조기 종료 패턴 감지(차단)
#   1  사용법 오류(입력 없음 / 파일 없음)
#
# macOS bash 3.2 안전: 빈 배열 가드, grep -c 미사용(매치 여부는 grep -q),
# 한글 크래시 방지 LC 고정.

set -u
export LC_ALL=C.UTF-8 2>/dev/null || export LC_ALL=en_US.UTF-8 2>/dev/null || true

usage() {
  printf 'usage: %s "text" | %s --file <path> | echo text | %s\n' "$0" "$0" "$0" >&2
  exit 1
}

# --- 입력 수집 -------------------------------------------------------------
INPUT=""
if [ "$#" -ge 1 ]; then
  if [ "$1" = "--file" ]; then
    if [ "$#" -lt 2 ]; then
      usage
    fi
    if [ ! -f "$2" ]; then
      printf 'error: file not found: %s\n' "$2" >&2
      exit 1
    fi
    INPUT="$(cat "$2")"
  else
    INPUT="$1"
  fi
else
  # stdin (파이프) 입력. 터미널이면 입력 없음으로 본다.
  if [ -t 0 ]; then
    usage
  fi
  INPUT="$(cat)"
fi

if [ -z "$INPUT" ]; then
  printf 'error: empty input\n' >&2
  exit 1
fi

# --- 패턴 정의 -------------------------------------------------------------
# 약속-미실행: 미래 의지/예정 표현으로 끝맺는 패턴 (한국어 + 영어).
# 범위 축소: 명시 작업 범위를 임의로 줄이는 표현.
PROMISE_PATTERNS=(
  '하겠습니다'
  '하겠음'
  '할 것입니다'
  '할 예정입니다'
  '할 예정이다'
  '다음으로 .*하겠'
  '이제 .*하겠'
  '진행하겠습니다'
  '작성하겠습니다'
  '구현하겠습니다'
  '확인하겠습니다'
  '시작하겠습니다'
  'will now '
  'I will '
  'next, I'\''ll'
  'going to '
  'let me '
)

SCOPE_REDUCTION_PATTERNS=(
  '시간 관계상'
  '지면 관계상'
  '나머지는 생략'
  '이하 생략'
  '이하 동일'
  '여기까지만'
  '일부만 '
  '간단히만'
  '생략하겠습니다'
  '생략합니다'
  'omitted for brevity'
  'truncated for brevity'
  'left as an exercise'
  'rest is similar'
  'and so on'
  '\.\.\. *$'
)

# 약속이 "실행됨"을 시사하는 증거 표현. 약속 패턴이 있어도 같은 입력에
# 아래 완료-증거 표현이 함께 있으면 약속만으로 차단하지 않는다(오탐 완화).
# fail-closed 방향이 기본이므로 증거 표현은 명시적인 것만 인정한다.
EVIDENCE_PATTERNS=(
  'exit code'
  'exit 0'
  '종료 코드'
  '테스트 통과'
  'tests passed'
  'PASS'
  '완료했습니다'
  '작성했습니다'
  '구현했습니다'
  '실행 결과'
  'WROTE '
)

# --- 결정론 감지 -----------------------------------------------------------
# grep -q 로 매치 여부만 본다(카운트 미사용 → || echo 0 함정 회피).
# 입력에 newline 보존을 위해 printf '%s' 사용.

has_match() {
  # $1: 검사 텍스트, $2: 패턴(확장 정규식). 매치=0, 미매치=1.
  printf '%s' "$1" | grep -Eq "$2"
}

# 1) 범위 축소 패턴: 발견 즉시 차단(증거와 무관하게 명시적 범위 축소는 위반).
if [ "${#SCOPE_REDUCTION_PATTERNS[@]}" -ne 0 ]; then
  for pat in "${SCOPE_REDUCTION_PATTERNS[@]}"; do
    if has_match "$INPUT" "$pat"; then
      printf 'BLOCK: scope-reduction pattern detected: %s\n' "$pat" >&2
      exit 2
    fi
  done
fi

# 2) 약속-미실행 패턴: 약속 표현이 있고 완료-증거 표현이 전혀 없으면 차단.
PROMISE_HIT=""
if [ "${#PROMISE_PATTERNS[@]}" -ne 0 ]; then
  for pat in "${PROMISE_PATTERNS[@]}"; do
    if has_match "$INPUT" "$pat"; then
      PROMISE_HIT="$pat"
      break
    fi
  done
fi

if [ -n "$PROMISE_HIT" ]; then
  EVIDENCE_HIT=""
  if [ "${#EVIDENCE_PATTERNS[@]}" -ne 0 ]; then
    for pat in "${EVIDENCE_PATTERNS[@]}"; do
      if has_match "$INPUT" "$pat"; then
        EVIDENCE_HIT="$pat"
        break
      fi
    done
  fi
  if [ -z "$EVIDENCE_HIT" ]; then
    printf 'BLOCK: promise-without-execution detected: %s (no completion evidence)\n' "$PROMISE_HIT" >&2
    exit 2
  fi
fi

# 통과: 조기 종료 패턴 없음.
exit 0
