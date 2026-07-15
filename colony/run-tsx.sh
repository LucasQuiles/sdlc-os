#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
TSX_BIN="$SCRIPT_DIR/node_modules/.bin/tsx"
if [[ ! -x "$TSX_BIN" ]]; then
  printf 'ERROR: local tsx is not installed; run npm ci in colony\n' >&2
  exit 127
fi
exec "$TSX_BIN" "$@"
