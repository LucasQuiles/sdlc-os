#!/bin/bash
# admission_wrapper.sh — reviewed point-of-use admission wrapper (round9
# remediation WP2, event 51). Replaces session-scratch admission scripts.
#
# Usage:
#   admission_wrapper.sh TREE HEAD_PIN ADMISSION_DIR -- COMMAND [ARGS...]
#
# Env:
#   ADMISSION_MAX_LOAD1  load1 ceiling for launch (default 8.0)
#   ADMISSION_PYTHON     interpreter (default /opt/homebrew/bin/python3.12)
#
# Contract (each check fail-closed, in order):
#   71  TREE's HEAD != HEAD_PIN
#   72  TREE not clean (porcelain non-empty)
#   75  the TREE'S OWN canonical safety.check_preflight refused, or load1
#       at/above the ceiling (the wrapper NEVER restates thresholds inline —
#       it calls the canonical gate; see round9 events 37/40)
#   73  ADMISSION_DIR already exists (vacancy violation)
#   74  mkdir failed
#   70  usage / cd failure
# Otherwise: ADMISSION_DIR is created 0700, the command runs from TREE with
# its combined stderr captured to ADMISSION_DIR/wrapped.stderr (artifact-bound
# refusal reasons), and the wrapped command's exit code passes through.
set -u

if [ "$#" -lt 5 ] || [ "$4" != "--" ]; then
  echo "usage: admission_wrapper.sh TREE HEAD_PIN ADMISSION_DIR -- COMMAND..." >&2
  exit 70
fi
TREE=$1; HEAD_PIN=$2; DIR=$3; shift 4
PY=${ADMISSION_PYTHON:-/opt/homebrew/bin/python3.12}
MAX_LOAD1=${ADMISSION_MAX_LOAD1:-8.0}

if [ "$(git -C "$TREE" rev-parse HEAD)" != "$HEAD_PIN" ]; then
  echo "ADMISSION: head pin mismatch"; exit 71
fi
if [ -n "$(git -C "$TREE" status --porcelain=v1)" ]; then
  echo "ADMISSION: tree not clean"; exit 72
fi

"$PY" - "$TREE" "$MAX_LOAD1" <<'PY'
import os, sys
tree, max_load1 = sys.argv[1], float(sys.argv[2])
sys.path.insert(0, tree)
import safety
load1 = os.getloadavg()[0]
ok, reason = safety.check_preflight()
print(f"ADMISSION preflight: load1={load1:.2f} ceiling={max_load1}; canonical: {reason}", flush=True)
if load1 >= max_load1:
    print("ADMISSION preflight: load1 at/above ceiling", flush=True)
    raise SystemExit(75)
if not ok:
    raise SystemExit(75)
PY
rc=$?
if [ "$rc" -ne 0 ]; then echo "ADMISSION: preflight refused (rc=$rc)"; exit 75; fi

if [ -e "$DIR" ]; then echo "ADMISSION: admission dir occupied"; exit 73; fi
mkdir -m 0700 "$DIR" || { echo "ADMISSION: mkdir failed"; exit 74; }
echo "ADMISSION: launched $(date -u +%Y-%m-%dT%H:%M:%SZ) head=$HEAD_PIN dir=$DIR"

cd "$TREE" || { echo "ADMISSION: cd failed"; exit 70; }
"$@" 2> "$DIR/wrapped.stderr"
rc=$?
echo "ADMISSION: wrapped exit=$rc at $(date -u +%Y-%m-%dT%H:%M:%SZ); stderr captured to $DIR/wrapped.stderr"
exit "$rc"
