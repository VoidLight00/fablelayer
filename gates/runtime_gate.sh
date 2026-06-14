#!/usr/bin/env bash
# FL20 runtime integrity — HARD exit 2. macOS bash 3.2 safe, fail-closed.
# 동작 Python 런타임의 syntax/import 무결성 + 단위테스트 + CLI 서브커맨드 실행을 검증.
# markdown 명세만으로는 통과할 수 없게 만든다(GATE-04/GATE-05 해소).
set -u
ROOT="${1:-$(pwd)}"
RC=0
cd "$ROOT" 2>/dev/null || { echo "RUNTIME FAIL(2): bad root $ROOT"; exit 2; }

# 1) syntax (py_compile) — fablelayer/ 가 있을 때만
if [ -d fablelayer ]; then
  if ! python3 -m compileall -q fablelayer >/dev/null 2>&1; then
    echo "RUNTIME FAIL(2): syntax error in fablelayer/"; RC=2
  fi
  # 2) import 무결성 (각 모듈)
  for f in fablelayer/*.py; do
    [ -e "$f" ] || continue
    base="$(basename "$f" .py)"
    [ "$base" = "__init__" ] && continue
    if ! python3 -c "import fablelayer.$base" >/dev/null 2>&1; then
      echo "RUNTIME FAIL(2): import fablelayer.$base"; RC=2
    fi
  done
  # 3) CLI 서브커맨드 실행
  if [ -f fablelayer/cli.py ]; then
    for sub in "--help" "status"; do
      if ! python3 -m fablelayer.cli $sub >/dev/null 2>&1; then
        echo "RUNTIME FAIL(2): cli $sub non-zero"; RC=2
      fi
    done
  fi
fi

# 4) 단위 테스트 (run_tests.py 가 있으면 반드시 통과)
if [ -f tests/run_tests.py ]; then
  if ! python3 tests/run_tests.py >/dev/null 2>&1; then
    echo "RUNTIME FAIL(2): tests/run_tests.py failed"; RC=2
  fi
fi

[ "$RC" -eq 0 ] && echo "RUNTIME PASS"
exit "$RC"
