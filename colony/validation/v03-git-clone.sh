#!/usr/bin/env bash
set -euo pipefail

# V-03: Git clone via file://, commit, no-push, fetch-merge
SCRIPT_NAME="V-03 git-clone"
TMPDIR_BASE=$(mktemp -d "/tmp/v03-XXXXXX")
trap 'rm -rf "$TMPDIR_BASE"' EXIT

echo "=== $SCRIPT_NAME ==="
echo "Testing: git clone file://, commit, no-push URL, fetch-merge"

SRC="$TMPDIR_BASE/source-repo"
CLONE="$TMPDIR_BASE/cloned-repo"

# Create source repo with initial commit on main
mkdir -p "$SRC"
git -C "$SRC" init -b main
git -C "$SRC" config user.email "test@test.com"
git -C "$SRC" config user.name "Test"
echo "initial" > "$SRC/file.txt"
git -C "$SRC" add file.txt
git -C "$SRC" commit -m "initial commit"

# Clone via file://
git clone "file://$SRC" "$CLONE"
ERRORS=0

# Check 1: .git exists
if [ -d "$CLONE/.git" ]; then
  echo "  [ok] .git exists"
else
  echo "  [FAIL] .git missing"
  ERRORS=$((ERRORS + 1))
fi

# Check 2: commit works in clone
git -C "$CLONE" config user.email "test@test.com"
git -C "$CLONE" config user.name "Test"
echo "change1" >> "$CLONE/file.txt"
git -C "$CLONE" add file.txt
git -C "$CLONE" commit -m "clone commit 1"
echo "change2" >> "$CLONE/file.txt"
git -C "$CLONE" add file.txt
git -C "$CLONE" commit -m "clone commit 2"

AHEAD=$(git -C "$CLONE" log origin/main..HEAD --oneline | wc -l)
if [ "$AHEAD" -eq 2 ]; then
  echo "  [ok] origin/main..HEAD counts 2 commits"
else
  echo "  [FAIL] expected 2 ahead commits, got $AHEAD"
  ERRORS=$((ERRORS + 1))
fi

# Check 3: no-push URL — set push URL to invalid, verify push fails
git -C "$CLONE" remote set-url --push origin no-push
PUSH_OUTPUT=$(git -C "$CLONE" push 2>&1 || true)
if echo "$PUSH_OUTPUT" | grep -qiE '(fatal|error|no-push|could not)'; then
  echo "  [ok] no-push URL blocks push"
else
  echo "  [FAIL] push should have failed with no-push URL"
  echo "  push output: $PUSH_OUTPUT"
  ERRORS=$((ERRORS + 1))
fi

# Check 4: fetch-merge works — add commit to source (different file to avoid conflicts), fetch+merge in clone
echo "upstream content" > "$SRC/upstream.txt"
git -C "$SRC" add upstream.txt
git -C "$SRC" commit -m "upstream commit"

git -C "$CLONE" fetch origin
git -C "$CLONE" merge origin/main --no-edit
if git -C "$CLONE" log --oneline | grep -q "upstream commit"; then
  echo "  [ok] fetch-merge works"
else
  echo "  [FAIL] fetch-merge did not bring upstream commit"
  ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -eq 0 ]; then
  echo "PASS"
else
  echo "FAIL — $ERRORS checks failed"
  exit 1
fi
