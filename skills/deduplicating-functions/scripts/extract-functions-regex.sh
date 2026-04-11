#!/usr/bin/env bash
# ABOUTME: Multi-language regex-based function extractor (shim to Python implementation).
# ABOUTME: Delegates to extract-functions-regex.py because BSD grep lacks -P (PCRE) support.

# The prior bash implementation used `grep -P` with Perl-compatible regex and
# \K lookbehind, which only works on GNU grep. macOS ships BSD grep, causing
# the extractor to silently produce zero results for all languages on macOS.
# The Python implementation uses the stdlib `re` module and works on any
# platform with Python 3.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

exec "$PY" "$SCRIPT_DIR/extract-functions-regex.py" "$@"
