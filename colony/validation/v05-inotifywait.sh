#!/usr/bin/env bash
set -euo pipefail

# V-05: inotifywait monitors SQLite WAL-mode DB file changes
SCRIPT_NAME="V-05 inotifywait"
TMPDIR_BASE=$(mktemp -d "/tmp/v05-XXXXXX")
trap 'rm -rf "$TMPDIR_BASE"; kill %1 2>/dev/null || true' EXIT

echo "=== $SCRIPT_NAME ==="
echo "Testing: inotifywait detects changes to WAL-mode SQLite DB"

# Check inotifywait is installed
if ! command -v inotifywait &>/dev/null; then
  echo "FAIL — inotifywait not installed (apt install inotify-tools)"
  exit 1
fi
echo "  [ok] inotifywait found"

DB_PATH="$TMPDIR_BASE/test.db"
EVENTS_LOG="$TMPDIR_BASE/events.log"

# Create WAL-mode DB
python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('CREATE TABLE items (id INTEGER PRIMARY KEY, val TEXT)')
conn.commit()
conn.close()
"
echo "  [ok] WAL-mode DB created"

# Start inotifywait monitoring .db and .db-wal files
inotifywait -m -e modify,create,close_write \
  "$TMPDIR_BASE" \
  --include '\.(db|db-wal)$' \
  > "$EVENTS_LOG" 2>&1 &
INOTIFY_PID=$!

sleep 0.5

# Insert a row to trigger file changes
python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute(\"INSERT INTO items (val) VALUES ('hello')\")
conn.commit()
conn.close()
"

sleep 1

kill $INOTIFY_PID 2>/dev/null || true
wait $INOTIFY_PID 2>/dev/null || true

echo "--- Events captured ---"
cat "$EVENTS_LOG" | head -20

EVENT_COUNT=$(wc -l < "$EVENTS_LOG")
if [ "$EVENT_COUNT" -gt 0 ]; then
  echo "  [ok] $EVENT_COUNT events detected"
  echo "PASS"
else
  echo "FAIL — no file events detected"
  exit 1
fi
