#!/usr/bin/env bash
# FL7 license/legal gate — HARD exit 2. macOS bash 3.2 safe, fail-closed.
# Blocks: non-public prompt text / copy directives + missing LICENSE/NOTICE/ATTRIBUTION + non-AGPL.
set -u
ROOT="${1:-$(pwd)}"
RC=0

# 1) non-public prompt text or copy directives anywhere in product artifacts
if grep -RIElq --include='*.md' --include='*.txt' --include='*.py' --include='*.sh' --include='*.json' \
   --exclude='REQUIREMENTS.md' --exclude='ATTRIBUTION.md' --exclude='license_gate.sh' \
   --exclude-dir='.git' --exclude-dir='node_modules' --exclude-dir='fixtures' --exclude-dir='snapshots' \
   -e '12만 자 leaked prompt' \
   -e 'leaked prompt 자동 압축' \
   -e 'blocked-prompt-source.*copy' \
   -e 'non-public prompt.*copy' \
   -e 'full leaked system prompt' \
   -e 'reproduce the full system prompt' \
   "$ROOT" 2>/dev/null; then
  echo "LICENSE FAIL(2): non-public prompt copy directive or full text present"; RC=2
fi

# 2) required legal files
for f in LICENSE NOTICE ATTRIBUTION.md; do
  if [ ! -f "$ROOT/$f" ]; then echo "LICENSE FAIL(2): missing $f"; RC=2; fi
done

# 3) AGPL declared (FL7 license goal)
if [ -f "$ROOT/LICENSE" ]; then
  if ! grep -qiE 'AGPL|GNU AFFERO GENERAL PUBLIC LICENSE' "$ROOT/LICENSE"; then
    echo "LICENSE FAIL(2): LICENSE is not AGPL-3.0"; RC=2
  fi
fi

# 4) ATTRIBUTION must list methodology sources and blocked source policy honestly
if [ -f "$ROOT/ATTRIBUTION.md" ]; then
  for src in fablize value-for-fable supergoal "Blocked source class"; do
    if ! grep -qi "$src" "$ROOT/ATTRIBUTION.md"; then
      echo "LICENSE FAIL(2): ATTRIBUTION.md missing source $src"; RC=2
    fi
  done
fi

[ "$RC" -eq 0 ] && echo "LICENSE PASS"
exit "$RC"
