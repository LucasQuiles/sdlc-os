#!/usr/bin/env bash
# ABOUTME: Compatibility shim — the enhanced report is now produced by
# generate_report.py (single streaming pass, bounded rows, atomic write).
# The previous implementation ran ≥6 whole-document jq passes; on 2026-08-22
# that reached a 22.7 GB footprint on a 2.05 GB input and exhausted swap.
# This shim keeps the legacy invocation (<merged-results.json|dir> [output])
# and propagates the generator's exit status and stderr unchanged.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${PYTHON:-python3}" "$here/generate_report.py" "$@"
