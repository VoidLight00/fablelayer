#!/usr/bin/env bash
# FL6 benchmark integrity gate — HARD exit 2. macOS bash 3.2 safe, fail-closed.
# Requires bench/ with RESULTS.md + raw data + reproduction script + Limitations section.
set -u
ROOT="${1:-$(pwd)}"
RC=0
BENCH="$ROOT/bench"

if [ ! -d "$BENCH" ]; then echo "BENCH FAIL(2): no bench/ dir"; exit 2; fi

if [ ! -f "$BENCH/RESULTS.md" ]; then echo "BENCH FAIL(2): no bench/RESULTS.md"; RC=2; fi

raw=$(find "$BENCH" -name '*.json' 2>/dev/null | head -1)
if [ -z "$raw" ]; then echo "BENCH FAIL(2): no raw data (bench/*.json)"; RC=2; fi

repro=$(find "$BENCH" \( -name '*.sh' -o -name '*.js' -o -name '*.py' -o -name '*.mjs' \) 2>/dev/null | head -1)
if [ -z "$repro" ]; then echo "BENCH FAIL(2): no reproduction script (bench/*.sh|js|py)"; RC=2; fi

if [ -f "$BENCH/RESULTS.md" ]; then
  if ! grep -qiE '^#{1,6} *(한계|limitation)' "$BENCH/RESULTS.md"; then
    echo "BENCH FAIL(2): RESULTS.md missing '## 한계' / '## Limitations' section"; RC=2
  fi
fi

[ "$RC" -eq 0 ] && echo "BENCH PASS"
exit "$RC"
