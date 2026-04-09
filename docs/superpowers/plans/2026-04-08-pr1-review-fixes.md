# PR #1 Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all critical and important issues found during code review of PR #1 (colony hardening, capture scripts, hook portability).

**Architecture:** Five independent fixes across deacon.py, capture scripts, and test file. No interdependencies — tasks can run in any order. All changes are on branch `feat/colony-hardening-and-hook-portability`.

**Tech Stack:** Python 3.12 (deacon.py), TypeScript/tsx (capture scripts), vitest (brick-hooks tests)

**Branch:** `feat/colony-hardening-and-hook-portability`
**Working directory:** `/Users/q/.claude/plugins/sdlc-os`

---

### Task 1: Fix broken import path in bp-long-running.ts

**Files:**
- Modify: `colony/scripts/bp-long-running.ts:1`

- [ ] **Step 1: Verify the bug exists**

Run: `cd colony && npx tsx scripts/bp-long-running.ts 2>&1 | head -5`
Expected: Module resolution error (cannot find `./events-db.js` from `scripts/` subdirectory)

- [ ] **Step 2: Fix the import path**

In `colony/scripts/bp-long-running.ts`, change line 1 from:
```typescript
import { openEventsDb, insertEvent, closeEventsDb } from './events-db.js';
```
to:
```typescript
import { openEventsDb, insertEvent, closeEventsDb } from '../events-db.js';
```

- [ ] **Step 3: Verify the fix compiles**

Run: `cd colony && npx tsc --noEmit 2>&1 | grep bp-long`
Expected: No errors mentioning bp-long-running

- [ ] **Step 4: Commit**

```bash
git add colony/scripts/bp-long-running.ts
git commit -m "fix: correct import path in bp-long-running.ts (../events-db.js)"
```

---

### Task 2: Remove PII defaults from deacon.py constants

**Files:**
- Modify: `colony/deacon.py:65-71`

- [ ] **Step 1: Run existing deacon tests to establish baseline**

Run: `cd colony && python3 -m pytest deacon_test.py -q 2>&1 | tail -5`
Expected: All tests pass (84+ passed)

- [ ] **Step 2: Replace hardcoded PII with empty/sentinel defaults**

In `colony/deacon.py`, replace lines 65-71:

```python
MAINTENANCE_ALERT_TARGET = os.environ.get("DEACON_MAINTENANCE_ALERT_TARGET", "18454174651")
MAINTENANCE_ALERT_BIN = os.environ.get("WHATSAPP_NOTIFY_BIN", "/home/q/.local/bin/whatsapp-notify")
MAINTENANCE_ALERT_TIMEOUT_S = 10
DEACON_EVENT_WORKSTREAM_ID = "deacon"
CONDUCTOR_PROMPT_FILE = Path(__file__).parent / "conductor-prompt.md"
TMUP_PLUGIN_DIR = Path("/home/q/.claude/plugins/tmup")
SDLC_PLUGIN_DIR = Path("/home/q/.claude/plugins/sdlc-os")
```

with:

```python
MAINTENANCE_ALERT_TARGET = os.environ.get("DEACON_MAINTENANCE_ALERT_TARGET", "")
MAINTENANCE_ALERT_BIN = os.environ.get("WHATSAPP_NOTIFY_BIN", "whatsapp-notify")
MAINTENANCE_ALERT_TIMEOUT_S = 10
DEACON_EVENT_WORKSTREAM_ID = "deacon"
CONDUCTOR_PROMPT_FILE = Path(__file__).parent / "conductor-prompt.md"
TMUP_PLUGIN_DIR = Path(os.environ.get("TMUP_PLUGIN_DIR", str(Path.home() / ".claude" / "plugins" / "tmup")))
SDLC_PLUGIN_DIR = Path(os.environ.get("SDLC_PLUGIN_DIR", str(Path.home() / ".claude" / "plugins" / "sdlc-os")))
```

Key changes:
- Phone number → empty string (forces explicit config)
- whatsapp-notify → bare binary name (relies on $PATH)
- Hardcoded `/home/q/` paths → `Path.home()` with env override

- [ ] **Step 3: Run deacon tests to verify nothing broke**

Run: `cd colony && python3 -m pytest deacon_test.py -q 2>&1 | tail -5`
Expected: All tests pass (same count as baseline)

- [ ] **Step 4: Commit**

```bash
git add colony/deacon.py
git commit -m "fix: remove PII defaults from deacon.py constants

Replace hardcoded phone number, user paths with empty/sentinel defaults.
All values remain env-overridable via existing env vars."
```

---

### Task 3: Remove unused import in brick-hooks.test.ts

**Files:**
- Modify: `colony/brick-hooks.test.ts:3`

- [ ] **Step 1: Run brick-hooks tests to establish baseline**

Run: `cd colony && npx vitest run brick-hooks.test.ts 2>&1 | tail -10`
Expected: All tests pass

- [ ] **Step 2: Remove the unused import**

In `colony/brick-hooks.test.ts`, delete line 3:
```typescript
import { execSync as realExecSync } from 'node:child_process';
```

- [ ] **Step 3: Run brick-hooks tests to verify nothing broke**

Run: `cd colony && npx vitest run brick-hooks.test.ts 2>&1 | tail -10`
Expected: Same tests pass, same count

- [ ] **Step 4: Commit**

```bash
git add colony/brick-hooks.test.ts
git commit -m "fix: remove unused realExecSync import from brick-hooks.test.ts"
```

---

### Task 4: Add makedirs safety to deadletter write paths in deacon.py

**Files:**
- Modify: `colony/deacon.py:357,434`
- Modify: `colony/deacon_test.py` (add test)

- [ ] **Step 1: Write test for maintenance alert deadletter directory creation**

Add this test to the `TestMaintenanceWatchdog` class in `colony/deacon_test.py`, after the existing `test_dead_letter_on_alert_timeout` test (around line 1057):

```python
    def test_maintenance_deadletter_creates_parent_dir(self, tmp_db: str, tmp_path: Path) -> None:
        deacon = Deacon(db_path=tmp_db, project_dir=str(tmp_path))
        nested_dl = tmp_path / "nested" / "deep" / "deadletter.jsonl"
        with patch.dict(os.environ, {"DEACON_MAINTENANCE_ALERT_DEADLETTER": str(nested_dl)}):
            with patch("asyncio.create_subprocess_exec", side_effect=OSError("fail")):
                asyncio.run(deacon._send_maintenance_alert("test_fn", RuntimeError("boom"), 3))
        assert nested_dl.exists()
        data = json.loads(nested_dl.read_text().strip())
        assert data["maintenance_function"] == "test_fn"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd colony && python3 -m pytest deacon_test.py -q -k "test_maintenance_deadletter_creates_parent_dir" 2>&1`
Expected: FAIL — FileNotFoundError because parent dir doesn't exist

- [ ] **Step 3: Add makedirs to both deadletter write paths**

In `colony/deacon.py`, in `_send_escalation_alert` (around line 357), change:

```python
            log.warning("escalation_deadletter bead_id=%s", bead_id)
            with open(dl_path, "a") as f:
                f.write(json.dumps(record) + "\n")
```

to:

```python
            log.warning("escalation_deadletter bead_id=%s", bead_id)
            os.makedirs(os.path.dirname(dl_path), exist_ok=True)
            with open(dl_path, "a") as f:
                f.write(json.dumps(record) + "\n")
```

In `_send_maintenance_alert` (around line 434), change:

```python
            log.warning("maintenance_alert_deadletter function=%s", maintenance_function)
            with open(deadletter_path, "a") as f:
                f.write(json.dumps(record) + "\n")
```

to:

```python
            log.warning("maintenance_alert_deadletter function=%s", maintenance_function)
            os.makedirs(os.path.dirname(deadletter_path), exist_ok=True)
            with open(deadletter_path, "a") as f:
                f.write(json.dumps(record) + "\n")
```

- [ ] **Step 4: Run the new test to verify it passes**

Run: `cd colony && python3 -m pytest deacon_test.py -q -k "test_maintenance_deadletter_creates_parent_dir" 2>&1`
Expected: PASS

- [ ] **Step 5: Run full deacon test suite**

Run: `cd colony && python3 -m pytest deacon_test.py -q 2>&1 | tail -5`
Expected: All tests pass (previous count + 1)

- [ ] **Step 6: Commit**

```bash
git add colony/deacon.py colony/deacon_test.py
git commit -m "fix: ensure deadletter parent directories exist before write

Add os.makedirs(exist_ok=True) to both _send_escalation_alert and
_send_maintenance_alert deadletter fallback paths."
```

---

### Task 5: Add DB path override to remaining capture scripts

**Files:**
- Modify: `colony/scripts/bp-long-running.ts:2`
- Modify: `colony/scripts/capture-memory-extra.ts:4`
- Modify: `colony/scripts/capture-memory-findings.ts:4`

These three scripts hardcode the DB path with no override. The pattern used by `capture-findings.ts` and `capture-todo-findings.ts` is:
```typescript
const dbPath = process.argv[2] || '/home/q/.local/state/tmup/colony-events.db';
openEventsDb(dbPath);
```

- [ ] **Step 1: Fix bp-long-running.ts**

In `colony/scripts/bp-long-running.ts`, change line 2 from:
```typescript
openEventsDb('/home/q/.local/state/tmup/colony-events.db');
```
to:
```typescript
const dbPath = process.argv[2] || '/home/q/.local/state/tmup/colony-events.db';
openEventsDb(dbPath);
```

- [ ] **Step 2: Fix capture-memory-extra.ts**

In `colony/scripts/capture-memory-extra.ts`, change line 4 from:
```typescript
openEventsDb('/home/q/.local/state/tmup/colony-events.db');
```
to:
```typescript
const dbPath = process.argv[2] || '/home/q/.local/state/tmup/colony-events.db';
openEventsDb(dbPath);
```

- [ ] **Step 3: Fix capture-memory-findings.ts**

In `colony/scripts/capture-memory-findings.ts`, change line 4 from:
```typescript
openEventsDb('/home/q/.local/state/tmup/colony-events.db');
```
to:
```typescript
const dbPath = process.argv[2] || '/home/q/.local/state/tmup/colony-events.db';
openEventsDb(dbPath);
```

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd colony && npx tsc --noEmit 2>&1 | tail -5`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add colony/scripts/bp-long-running.ts colony/scripts/capture-memory-extra.ts colony/scripts/capture-memory-findings.ts
git commit -m "fix: add argv DB path override to all capture scripts

Match the pattern used by capture-findings.ts and capture-todo-findings.ts.
All scripts now accept optional process.argv[2] for DB path."
```

---

### Post-Implementation Verification

After all 5 tasks are complete, run the full verification suite:

```bash
# TypeScript compilation
cd colony && npx tsc --noEmit

# Vitest (brick-hooks + others)
cd colony && npx vitest run

# Deacon tests
cd colony && python3 -m pytest deacon_test.py -q

# Grep for remaining PII
grep -rn '/home/q/' colony/deacon.py
# Expected: no matches

# Grep for remaining hardcoded DB without override
grep -n "openEventsDb('/home/q" colony/scripts/*.ts
# Expected: no matches (all should use dbPath variable)

# Verify import path fixed
head -1 colony/scripts/bp-long-running.ts
# Expected: from '../events-db.js'
```

Push the branch:
```bash
git push origin feat/colony-hardening-and-hook-portability
```
