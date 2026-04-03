#!/usr/bin/env python3
"""V-04: SQLite concurrency — 9 threads, IMMEDIATE transactions, WAL mode."""

import sqlite3
import threading
import tempfile
import os
import sys
import shutil

SCRIPT_NAME = "V-04 sqlite-concurrency"
NUM_THREADS = 9
TASKS_PER_THREAD = 10
TOTAL_TASKS = NUM_THREADS * TASKS_PER_THREAD

print(f"=== {SCRIPT_NAME} ===")
print(f"Testing: {NUM_THREADS} threads, {TASKS_PER_THREAD} tasks each, IMMEDIATE transactions, WAL mode")

tmpdir = tempfile.mkdtemp(prefix="v04-")
db_path = os.path.join(tmpdir, "tasks.db")

# Setup DB with WAL mode
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("""
    CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        status TEXT NOT NULL DEFAULT 'pending',
        worker TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP
    )
""")
for i in range(TOTAL_TASKS):
    conn.execute("INSERT INTO tasks (status) VALUES ('pending')")
conn.commit()
conn.close()

results: list[tuple[int, int]] = [None] * NUM_THREADS  # type: ignore


def worker(thread_id: int) -> tuple[int, int]:
    """Each worker claims and completes tasks in IMMEDIATE transactions."""
    local_completed = 0
    local_errors = 0

    db = sqlite3.connect(db_path, timeout=8.0)
    db.execute("PRAGMA busy_timeout=8000")
    db.execute("PRAGMA journal_mode=WAL")

    for _ in range(TASKS_PER_THREAD):
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT id FROM tasks WHERE status='pending' LIMIT 1"
            ).fetchone()
            if row:
                db.execute(
                    "UPDATE tasks SET status='completed', worker=?, completed_at=CURRENT_TIMESTAMP WHERE id=?",
                    (f"worker-{thread_id}", row[0]),
                )
                db.execute("COMMIT")
                local_completed += 1
            else:
                db.execute("ROLLBACK")
        except Exception:
            try:
                db.execute("ROLLBACK")
            except Exception:
                pass
            local_errors += 1

    db.close()
    return local_completed, local_errors


def run_worker(tid: int) -> None:
    results[tid] = worker(tid)


threads: list[threading.Thread] = []
for i in range(NUM_THREADS):
    t = threading.Thread(target=run_worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

total_completed = sum(r[0] for r in results if r)
total_errors = sum(r[1] for r in results if r)

print(f"  Completed: {total_completed}/{TOTAL_TASKS}")
print(f"  Errors: {total_errors}")

# Verify DB state
conn = sqlite3.connect(db_path)
db_completed = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE status='completed'"
).fetchone()[0]
db_pending = conn.execute(
    "SELECT COUNT(*) FROM tasks WHERE status='pending'"
).fetchone()[0]
conn.close()

print(f"  DB completed: {db_completed}, DB pending: {db_pending}")

shutil.rmtree(tmpdir, ignore_errors=True)

if total_completed >= 50 and total_errors == 0:
    print("PASS")
else:
    print(f"FAIL — completed={total_completed} (need >=50), errors={total_errors} (need 0)")
    sys.exit(1)
