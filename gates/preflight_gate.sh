#!/usr/bin/env bash
# FL17 preflight — root sole-occupancy guard. exit 4 if ROOT belongs to another project/agent.
# Prevents FLOG-001 (cp merge into another agent's working dir during parallel build).
# macOS bash 3.2 safe, fail-closed.
set -u
ROOT="${1:-$(pwd)}"
RC=0

# empty root => safe to occupy
if [ -z "$(ls -A "$ROOT" 2>/dev/null)" ]; then
  echo "PREFLIGHT PASS (empty root)"; exit 0
fi

# REQUIREMENTS.md present must be FableLayer's (our marker), else foreign occupancy
if [ -f "$ROOT/REQUIREMENTS.md" ]; then
  if ! grep -qiE 'FableLayer' "$ROOT/REQUIREMENTS.md" 2>/dev/null; then
    echo "PREFLIGHT FAIL(4): REQUIREMENTS.md present but not FableLayer's — root occupied by another project"; RC=4
  fi
fi

# foreign verify_*.sh gate (another agent's harness) signals shared territory
foreign=$(ls "$ROOT"/gates/verify_*.sh 2>/dev/null | grep -v 'verify_fablelayer.sh' | head -1)
if [ -n "$foreign" ]; then
  echo "PREFLIGHT FAIL(4): foreign gate present ($foreign) — possible other-agent territory"; RC=4
fi

[ "$RC" -eq 0 ] && echo "PREFLIGHT PASS"
exit "$RC"
