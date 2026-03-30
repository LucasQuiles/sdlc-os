#!/bin/bash
# extract-functions.sh — AST-based function extraction for JS/TS
# Uses the TypeScript compiler API for real AST parsing — not regex.
# Exports: function name, parameter signature, body hash, line count, branch count, nesting depth
# Output: JSON array of function descriptors
# Usage: bash scripts/extract-functions.sh [paths...]
# Example: bash scripts/extract-functions.sh lib/utils/ lib/storage/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Resolve target paths
TARGETS=("$@")
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "Usage: bash scripts/extract-functions.sh <path1> [path2] ..." >&2
  exit 1
fi

# Require node — no regex fallback. AST accuracy is the contract.
if ! command -v node &> /dev/null; then
  echo '{"error": "node not found — AST extraction requires Node.js", "functions": [], "file_count": 0}'
  exit 0
fi

# Build file list — JS/TS only, exclude tests/vendor/generated
FILE_LIST=$(find "${TARGETS[@]}" \
  -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) \
  ! -path "*/__tests__/*" \
  ! -path "*/node_modules/*" \
  ! -path "*/*.test.*" \
  ! -path "*/*.spec.*" \
  ! -path "*/.next/*" \
  ! -path "*/dist/*" \
  2>/dev/null || true)

if [[ -z "$FILE_LIST" ]]; then
  echo '{"functions": [], "file_count": 0}'
  exit 0
fi

# Pass file list to the AST extraction module
echo "$FILE_LIST" | node "$SCRIPT_DIR/lib/ast-extract-functions.js"
