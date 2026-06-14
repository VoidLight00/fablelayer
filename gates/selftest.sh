#!/usr/bin/env bash
# Gate self-test — fixtures drive expected exit codes. macOS bash 3.2 safe.
set -u
GATES="$(cd "$(dirname "$0")" && pwd)"
FIX="$GATES/fixtures"
FAILS=0
check() { # script fixture want_rc [extra args...]
  local s="$1" fx="$2" want="$3"; shift 3
  bash "$GATES/$s" "$FIX/$fx" "$@" >/dev/null 2>&1; local rc=$?
  if [ "$rc" -eq "$want" ]; then
    printf 'ok   %-26s %-16s rc=%s\n' "$s" "$fx" "$rc"
  else
    printf 'FAIL %-26s %-16s rc=%s want=%s\n' "$s" "$fx" "$rc" "$want"; FAILS=$((FAILS+1))
  fi
}
check license_gate.sh         license_pass   0
check license_gate.sh         license_fail   2
check perf_claim_gate.sh      perf_pass      0
check perf_claim_gate.sh      perf_fail      2
check bench_integrity_gate.sh bench_pass     0
check bench_integrity_gate.sh bench_fail     2
check completeness_gate.sh    complete_pass  0 --mode new
check completeness_gate.sh    complete_fail  3 --mode new
check preflight_gate.sh       preflight_pass 0
check preflight_gate.sh       preflight_fail 4
check render_gate.sh          render_pass    0
check render_gate.sh          render_fail    2
check publish_gate.sh         publish_fail   2
check runtime_gate.sh         runtime_pass   0
check runtime_gate.sh         runtime_fail   2
echo "---"
if [ "$FAILS" -eq 0 ]; then echo "SELFTEST PASS"; exit 0; else echo "SELFTEST FAIL: $FAILS"; exit 1; fi
