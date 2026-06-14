#!/usr/bin/env bash
# FL13 completeness gate — HARD exit 3 (fail-closed). macOS bash 3.2 safe.
# Verifies mode-required artifacts exist. Unknown mode => exit 3.
set -u
ROOT="${1:-$(pwd)}"
MODE="all"
prev=""
for a in "$@"; do
  if [ "$prev" = "--mode" ]; then MODE="$a"; fi
  prev="$a"
done
RC=0
miss() { echo "COMPLETE FAIL(3): missing $1"; RC=3; }
need_file() { [ -f "$ROOT/$1" ] || miss "$1"; }
need_dir()  { [ -d "$ROOT/$1" ] || miss "$1/"; }

case "$MODE" in
  new|all)
    for d in core styles skills agents bench cli adapters .claude-plugin fablelayer tests; do need_dir "$d"; done
    need_file "core/promptcore.md"
    need_file "styles/vff-v2.md"
    need_file "cli/fablelayer"
    need_file ".claude-plugin/marketplace.json"
    need_file ".claude-plugin/plugin.json"
    need_file "adapters/README.md"
    need_file "bench/RESULTS.md"
    # runnable 산출물 요구 (markdown 명세만으로 PASS 금지 — GATE-04)
    need_file "fablelayer/promptcore.py"
    need_file "fablelayer/cli.py"
    need_file "fablelayer/adapters.py"
    need_file "tests/run_tests.py"
    need_file "pyproject.toml"
    ;;
  bench)
    need_dir "bench"; need_file "bench/RESULTS.md"
    ;;
  package)
    need_file ".claude-plugin/plugin.json"; need_file "cli/fablelayer"
    ;;
  layer|audit|status|resume|publish)
    : # 부분/배포 모드: 고정 manifest 없음 (publish 완전성은 publish_gate가 verify --mode all로 강제)
    ;;
  *)
    echo "COMPLETE FAIL(3): unknown mode '$MODE'"; RC=3
    ;;
esac

[ "$RC" -eq 0 ] && echo "COMPLETE PASS (mode=$MODE)"
exit "$RC"
