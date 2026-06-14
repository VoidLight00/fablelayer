#!/usr/bin/env bash
# FL9 performance-claim honesty gate — HARD exit 2. macOS bash 3.2 safe, fail-closed.
# Blocks numeric perf claims (similarity %, score, savings) not backed by bench/ ref or honesty marker.
# Requires capability-vs-procedure distinction in README.
set -u
ROOT="${1:-$(pwd)}"
RC=0

FILES=""
for f in README.md README.ko.md; do [ -f "$ROOT/$f" ] && FILES="$FILES $ROOT/$f"; done
if [ -d "$ROOT/docs" ]; then
  for f in $(find "$ROOT/docs" -name '*.md' 2>/dev/null); do FILES="$FILES $f"; done
fi

if [ -z "$FILES" ]; then
  echo "PERF FAIL(2): no README to inspect"; exit 2
fi

# unbacked perf claim lines: number (NN% or N점) + perf keyword, lacking bench ref / honesty marker / price-table context
bad=$(grep -nIE '([0-9]{2}%|[0-9]+ *점)' $FILES 2>/dev/null \
      | grep -iE 'similar|동률|동등|능가|opus|fable|품질|quality|절감|saving|cheaper|score|점수|상회|tie' \
      | grep -ivE 'bench/|\[bench|target|목표|미검증|추정|aspirational|claim-only|한계|limitation|noise|노이즈|예시|example|\$[0-9]|/1M|입력|출력|input \$|output \$|price|단가' )
if [ -n "$bad" ]; then
  echo "PERF FAIL(2): unbacked performance claim(s):"
  printf '%s\n' "$bad"
  RC=2
fi

# capability vs procedure distinction must be present
if ! grep -liE 'capability' $FILES >/dev/null 2>&1; then
  echo "PERF FAIL(2): README missing 'capability' (non-transfer) framing"; RC=2
fi
if ! grep -liE 'procedure|절차' $FILES >/dev/null 2>&1; then
  echo "PERF FAIL(2): README missing 'procedure/절차' (transferable) framing"; RC=2
fi

[ "$RC" -eq 0 ] && echo "PERF PASS"
exit "$RC"
