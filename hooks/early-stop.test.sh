#!/usr/bin/env bash
# early-stop.test.sh — early-stop.sh 셀프테스트.
#
# 양성(차단되어야 할 조기 종료 패턴 → exit 2)과 음성(정상 완료 → exit 0)을
# 모두 검증한다. 입력 방식(인자/파일/stdin)도 검증한다.
# OR 집계: 한 케이스라도 기대와 다르면 전체 비0(fail-closed).
#
# 사용법: early-stop.test.sh
# 종료 코드: 0 전체 통과 / 1 하나 이상 실패.

set -u
export LC_ALL=C.UTF-8 2>/dev/null || export LC_ALL=en_US.UTF-8 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/early-stop.sh"

if [ ! -f "$HOOK" ]; then
  printf 'FAIL: hook not found: %s\n' "$HOOK" >&2
  exit 1
fi

FAILURES=0
PASSES=0

# run_case <기대코드> <라벨> <입력텍스트>
run_case() {
  expected="$1"
  label="$2"
  text="$3"
  "$HOOK" "$text" >/dev/null 2>&1
  actual="$?"
  if [ "$actual" -eq "$expected" ]; then
    printf 'PASS  [%s] exit=%s\n' "$label" "$actual"
    PASSES=$((PASSES + 1))
  else
    printf 'FAIL  [%s] expected=%s actual=%s\n' "$label" "$expected" "$actual"
    FAILURES=$((FAILURES + 1))
  fi
}

# --- 양성 케이스: 차단되어야 함 (exit 2) -----------------------------------
run_case 2 "약속-미실행(하겠습니다)" \
  "분석을 마쳤습니다. 이제 게이트 스크립트를 작성하겠습니다."
run_case 2 "약속-미실행(할 예정입니다)" \
  "구조를 잡았으니 다음으로 테스트를 추가할 예정입니다."
run_case 2 "약속-미실행(I will)" \
  "The plan looks good. I will implement the parser next."
run_case 2 "범위축소(시간 관계상)" \
  "핵심 함수만 구현했고 시간 관계상 나머지는 생략합니다."
run_case 2 "범위축소(omitted for brevity)" \
  "Here is the first handler; the rest is omitted for brevity."
run_case 2 "범위축소(이하 동일)" \
  "FL1 처리 코드입니다. FL2~FL16 이하 동일."
run_case 2 "약속+범위축소 동시" \
  "여기까지만 하고 나머지는 다음에 구현하겠습니다."

# --- 음성 케이스: 통과해야 함 (exit 0) -------------------------------------
run_case 0 "완료+증거(종료 코드)" \
  "게이트를 작성했습니다. verify.sh 실행 결과 종료 코드 0을 확인했습니다."
run_case 0 "완료+증거(tests passed)" \
  "Implemented the parser. Ran the suite: 12 tests passed, exit 0."
run_case 0 "완료+증거(WROTE)" \
  "절차팩 4종을 작성했습니다. WROTE /tmp/a.md /tmp/b.md, 파일 존재 확인."
run_case 0 "순수 사실 보고(약속·축소 없음)" \
  "현재 FL2 판정 기준은 절차별 산출물 4종과 hook 셀프테스트입니다."
run_case 0 "약속표현+증거 동반(오탐 완화)" \
  "확인하겠습니다라고 했던 빌드를 실행했고 종료 코드 0, 테스트 통과."

# --- 입력 방식 검증 --------------------------------------------------------
# 파일 입력: 차단 케이스가 파일로도 동일 판정인지.
TMPF="$(mktemp -t earlystop.XXXXXX)"
trap 'rm -f "$TMPF"' EXIT
printf '%s\n' "이제 다음 단계를 진행하겠습니다." > "$TMPF"
"$HOOK" --file "$TMPF" >/dev/null 2>&1
if [ "$?" -eq 2 ]; then
  printf 'PASS  [파일입력 차단] exit=2\n'
  PASSES=$((PASSES + 1))
else
  printf 'FAIL  [파일입력 차단] expected=2\n'
  FAILURES=$((FAILURES + 1))
fi

# stdin 입력: 정상 완료가 통과인지.
printf '%s\n' "구현했습니다. 종료 코드 0 확인." | "$HOOK" >/dev/null 2>&1
if [ "$?" -eq 0 ]; then
  printf 'PASS  [stdin 통과] exit=0\n'
  PASSES=$((PASSES + 1))
else
  printf 'FAIL  [stdin 통과] expected=0\n'
  FAILURES=$((FAILURES + 1))
fi

# 사용법 오류: 빈 입력은 exit 1.
"$HOOK" "" >/dev/null 2>&1
if [ "$?" -eq 1 ]; then
  printf 'PASS  [빈입력 사용법오류] exit=1\n'
  PASSES=$((PASSES + 1))
else
  printf 'FAIL  [빈입력 사용법오류] expected=1\n'
  FAILURES=$((FAILURES + 1))
fi

# --- 집계 -----------------------------------------------------------------
printf '\n--- summary: %s passed, %s failed ---\n' "$PASSES" "$FAILURES"
if [ "$FAILURES" -ne 0 ]; then
  exit 1
fi
exit 0
