#!/usr/bin/env bash
# FL15/FL19 publish guard — HARD exit 2. Blocks external publish unless ALL gates green
# AND explicit approval token present. macOS bash 3.2 safe, fail-closed.
# Usage: publish_gate.sh [ROOT] [--approved]
set -u
ROOT="${1:-$(pwd)}"
APPROVAL="${2:-}"
GATES_DIR="$(cd "$(dirname "$0")" && pwd)"
RC=0

# approval token: explicit --approved arg OR a runs/<id>/APPROVED file
approved=0
[ "$APPROVAL" = "--approved" ] && approved=1
if ls "$ROOT"/runs/*/APPROVED >/dev/null 2>&1; then approved=1; fi
if [ "$approved" -ne 1 ]; then
  echo "PUBLISH FAIL(2): no approval token (FL15) — external publish/push/marketplace blocked"; RC=2
fi

# all gates must be green
if ! bash "$GATES_DIR/verify_fablelayer.sh" "$ROOT" --mode all >/dev/null 2>&1; then
  echo "PUBLISH FAIL(2): verify_fablelayer not green — cannot publish"; RC=2
fi

[ "$RC" -eq 0 ] && echo "PUBLISH PASS (approved + all gates green)"
exit "$RC"
