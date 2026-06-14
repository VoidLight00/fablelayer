#!/usr/bin/env bash
# FableLayer master gate — OR-aggregate, fail-closed. macOS bash 3.2 safe.
# Usage: verify_fablelayer.sh [ROOT] [--mode new|layer|bench|package|audit]
# Exit: 0 PASS, non-zero FAIL. Sub-gate exits surfaced.
set -u

ROOT="${1:-$(pwd)}"
[ "${ROOT#--}" != "$ROOT" ] && ROOT="$(pwd)"   # first arg was a flag
MODE="all"
for a in "$@"; do
  case "$a" in
    --mode) NEXT_MODE=1 ;;
    *) if [ "${NEXT_MODE:-0}" = "1" ]; then MODE="$a"; NEXT_MODE=0; fi ;;
  esac
done

GATES_DIR="$(cd "$(dirname "$0")" && pwd)"
RC=0
FAILED=""

log()  { printf '%s\n' "$*"; }
fail() { RC=1; FAILED="$FAILED $1"; log "FAIL[$1]: $2"; }

# --- structure (SSoT + safety docs must exist) ---
for f in REQUIREMENTS.md README.md README.ko.md LICENSE NOTICE ATTRIBUTION.md ROADMAP.md FAILURE_LOG.md; do
  if [ ! -f "$ROOT/$f" ]; then fail "structure" "missing $f"; fi
done

# --- sub-gates (each HARD). collect rc, fail-closed on crash too ---
run_subgate() {
  local name="$1"; shift
  local script="$GATES_DIR/$name"
  if [ ! -x "$script" ] && [ ! -f "$script" ]; then fail "$name" "gate script absent"; return; fi
  bash "$script" "$@"
  local rc=$?
  if [ "$rc" -ne 0 ]; then fail "$name" "exit $rc"; fi
}

run_subgate "license_gate.sh"        "$ROOT"
run_subgate "perf_claim_gate.sh"     "$ROOT"
run_subgate "bench_integrity_gate.sh" "$ROOT"
run_subgate "completeness_gate.sh"   "$ROOT" "--mode" "$MODE"
run_subgate "render_gate.sh"         "$ROOT"
run_subgate "runtime_gate.sh"        "$ROOT"
# publish 모드에서만 승인 게이트 배선 (publish_gate는 verify --mode all을 호출하므로 무한루프 없음)
if [ "$MODE" = "publish" ]; then run_subgate "publish_gate.sh" "$ROOT"; fi

# --- FL8 fallback-zero: reuse fable-forge lint on generated .md (dependency) ---
FABLE_LINT="$HOME/fable-forge/gates/fable_lint.sh"
if [ -f "$FABLE_LINT" ]; then
  # lint generated product artifacts (core/styles/skills/agents/adapters), not the harness spec itself
  LINT_TARGETS=""
  for d in core styles skills agents adapters; do
    [ -d "$ROOT/$d" ] && LINT_TARGETS="$LINT_TARGETS $ROOT/$d"
  done
  if [ -n "$LINT_TARGETS" ]; then
    bash "$FABLE_LINT" $LINT_TARGETS >/dev/null 2>&1
    lrc=$?
    # fable_lint exit 2 = HARD fallback pattern; 0 = clean; other = treat as fail-closed
    if [ "$lrc" -eq 2 ]; then fail "fallback_zero" "fable_lint HARD violation (exit 2)"; fi
  fi
else
  log "WARN: fable-forge lint not found ($FABLE_LINT) — FL8 unverified"
fi

if [ "$RC" -eq 0 ]; then
  log "VERIFY PASS (mode=$MODE root=$ROOT)"
else
  log "VERIFY FAIL:$FAILED"
fi
exit "$RC"
