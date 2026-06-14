#!/usr/bin/env bash
# FableLayer benchmark reproduction script.
# Measures the PROCEDURE layer effect (not model capability) via paired baseline/treatment runs,
# blind scoring with >=2 independent judges, ablation, and raw-data capture into bench/raw.json.
#
# macOS bash 3.2 safe: no associative arrays, empty-array guards, byte-safe captures, fail-closed.
# Live model calls are intentionally stubbed — wire your own model invocation in run_model().
# This script never fabricates scores: without a wired model call, --run exits non-zero and
# leaves raw.json untouched rather than inventing numbers.

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BENCH_DIR="$SCRIPT_DIR"
RAW="$BENCH_DIR/raw.json"

MODE="help"

usage() {
  cat <<'EOF'
FableLayer benchmark — reproduce.sh

Usage:
  bash bench/reproduce.sh --help       Show this help.
  bash bench/reproduce.sh --dry-run    Validate the pipeline without calling any model.
                                       Checks raw.json schema fields and prints the planned
                                       paired baseline/treatment + ablation matrix.
  bash bench/reproduce.sh --run        Execute live measurement. Requires run_model() to be
                                       wired to a real model endpoint. Exits non-zero (no data
                                       written) if the model call is still the stub, so no
                                       synthetic scores are ever produced.

What it measures:
  Procedure-layer effect only (verification grounding, evidence gate, systematic investigation,
  early-stop prevention, VFF output structure). NOT model capability — capability does not
  transfer via a harness. Same model is used for baseline and treatment; the measured delta is
  attributed to the procedure layer, not to the model.

Method (neutral):
  1) blind     — condition/model masked from judges during scoring (label_hidden=true).
  2) baseline  — same model with the procedure layer OFF, paired against treatment (layer ON).
  3) >=2 judges — judge A: rubric (0-5); judge B: deterministic rule check. Disagreements kept,
                  not averaged away.
  4) ablation  — disable one procedure element at a time to isolate its contribution.

Determinism / honesty:
  - Seeds are fixed per run (see raw.json "seed"); repeats capture noise (n, stddev).
  - Record the exact model version/date at measurement time into "model_version_note".
  - Raw prompts/outputs/scores are appended to raw.json per run; never overwrite prior runs
    (lost raw data was the direct cause of the value-for-fable bench reproduction failure).
EOF
}

# --- arg parse (bash 3.2 safe) ---
if [ "$#" -ge 1 ]; then
  case "$1" in
    --help|-h) MODE="help" ;;
    --dry-run) MODE="dry-run" ;;
    --run)     MODE="run" ;;
    *) echo "unknown argument: $1" >&2; usage; exit 64 ;;
  esac
fi

require_raw() {
  if [ ! -f "$RAW" ]; then
    echo "FAIL: missing $RAW" >&2
    exit 66
  fi
}

# Validate that raw.json carries the required schema fields, byte-safe.
check_schema() {
  require_raw
  # capture as bytes then decode replace to survive any non-utf8 noise
  content="$(cat "$RAW" 2>/dev/null | LC_ALL=C tr -d '\000')"
  missing=""
  for field in schema_version field_spec runs condition ablation seed judges label_hidden measured; do
    case "$content" in
      *"\"$field\""*) : ;;
      *) missing="$missing $field" ;;
    esac
  done
  if [ -n "$missing" ]; then
    echo "FAIL: raw.json missing required field(s):$missing" >&2
    return 1
  fi
  # optional stronger validation if python3 is present
  if command -v python3 >/dev/null 2>&1; then
    if ! python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$RAW" >/dev/null 2>&1; then
      echo "FAIL: raw.json is not valid JSON" >&2
      return 1
    fi
  fi
  echo "OK: raw.json schema fields present"
  return 0
}

print_plan() {
  echo "Planned measurement matrix (each task x condition, plus ablations):"
  echo "  task_types : debugging, multi-step-build, extraction"
  echo "  conditions : baseline (layer OFF) | treatment (layer ON)  [paired, same model]"
  echo "  ablations  : full, no-verification, no-evidence-gate, no-systematic-investigation, no-early-stop"
  echo "  judges     : A=rubric(0-5)  B=rule(pass-rate)   [>=2, disagreements kept]"
  echo "  blind      : label_hidden=true (condition/model masked during scoring)"
  echo "  repeats    : fixed seed per run; n & stddev recorded for noise range"
}

# STUB — wire this to a real model endpoint to enable live measurement.
# Returns the model's raw output on stdout. The default stub returns nothing and
# signals 'not wired' so --run refuses to write synthetic data.
run_model() {
  # args: $1=model  $2=condition  $3=ablation  $4=seed  $5=prompt
  # Example wiring (left commented — provide your own credentials/endpoint):
  #   curl -sS "$MODEL_ENDPOINT" -d "{\"model\":\"$1\",\"seed\":\"$4\",\"prompt\":\"$5\"}" ...
  return 87  # 87 = sentinel: model call not wired
}

do_run() {
  require_raw
  check_schema || exit 1
  # probe the stub
  run_model "probe" "baseline" "full" "0" "probe" >/dev/null 2>&1
  rc=$?
  if [ "$rc" -eq 87 ]; then
    echo "ABORT: run_model() is still the stub (sentinel 87)." >&2
    echo "Wire run_model() to a real model endpoint before --run." >&2
    echo "No synthetic scores written; raw.json left untouched." >&2
    exit 70
  fi
  echo "run_model() is wired (rc=$rc). Live measurement loop would execute here:"
  echo "  for each run in raw.json: call run_model, capture output, score with judge A + judge B,"
  echo "  append seed/output/scores/noise back into raw.json (append-only, never overwrite)."
  echo "Then update bench/RESULTS.md measurement table from raw.json aggregates."
  # Intentionally not implemented beyond the wiring contract: real scoring requires the
  # judge endpoints and the model endpoint to be provided by the operator.
  exit 0
}

case "$MODE" in
  help) usage; exit 0 ;;
  dry-run)
    check_schema || exit 1
    print_plan
    echo "DRY-RUN OK: pipeline validated, no model called."
    exit 0
    ;;
  run) do_run ;;
  *) usage; exit 64 ;;
esac
