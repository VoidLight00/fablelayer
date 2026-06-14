#!/usr/bin/env bash
# FL18 render/exec fidelity — HARD exit 2. macOS bash 3.2 safe, fail-closed.
# Validates: plugin manifests are valid JSON, CLI runs (--help or no-arg usage exit 0),
# README bench/ links resolve to real files.
set -u
ROOT="${1:-$(pwd)}"
RC=0

# 1) plugin/marketplace manifests valid JSON
for j in .claude-plugin/plugin.json .claude-plugin/marketplace.json; do
  if [ -f "$ROOT/$j" ]; then
    if ! python3 -m json.tool "$ROOT/$j" >/dev/null 2>&1; then
      echo "RENDER FAIL(2): invalid JSON $j"; RC=2
    fi
  fi
done

# 2) CLI usable: --help OR no-arg must exit 0
if [ -f "$ROOT/cli/fablelayer" ]; then
  if ! { bash "$ROOT/cli/fablelayer" --help >/dev/null 2>&1 || bash "$ROOT/cli/fablelayer" >/dev/null 2>&1; }; then
    echo "RENDER FAIL(2): cli/fablelayer usage non-zero"; RC=2
  fi
fi

# 3) README bench/ links resolve
for readme in README.md README.ko.md; do
  if [ -f "$ROOT/$readme" ]; then
    for ref in $(grep -oE 'bench/[A-Za-z0-9_./-]+' "$ROOT/$readme" 2>/dev/null | sort -u); do
      p="${ref%%)*}"; p="${p%.}"; p="${p%,}"
      [ "$p" = "bench" ] || [ "$p" = "bench/" ] && continue
      if [ ! -e "$ROOT/$p" ]; then echo "RENDER FAIL(2): dead bench link in $readme -> $p"; RC=2; fi
    done
  fi
done

[ "$RC" -eq 0 ] && echo "RENDER PASS"
exit "$RC"
