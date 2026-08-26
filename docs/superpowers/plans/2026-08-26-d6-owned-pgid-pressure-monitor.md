# D6 Owned-PGID Pressure Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify the P1-6 wrapper that continuously monitors host load, swap use, and aggregate RSS for one runner-owned process group without executing the D6 composite.

**Architecture:** Add a standalone Python wrapper beside `run_pipeline.py`. It starts a caller-supplied command in a new session, proves `child_pid == pgid`, samples the host and owned process group once per second, and writes one private atomic JSON receipt. A breached or unavailable monitor axis freezes the outcome as `Inconclusive`, sends bounded TERM then KILL to that PGID only, and refuses a clean result unless census proves the group is gone.

**Tech Stack:** Python 3.12 standard library, pytest, Ruff.

## Global Constraints

- Build-only authority comes from round9 ledger event 25; never execute or admit the D6 composite under this plan.
- The wrapper must not modify `run_pipeline.py` or the ordinary pipeline execution path.
- Launch with `start_new_session=True`; the monitor process must remain outside the child group.
- Ownership admission requires the observed child PGID to equal the child PID.
- Thresholds are `load1 < 8.0`, swap used `<= 12288.0 MiB`, and aggregate live owned-PGID RSS `<= 6144.0 MiB`.
- Default sample interval is `1.0s`; TERM and KILL grace intervals are each `2.0s`.
- Equality is allowed for swap/RSS ceilings and refused for the strict load ceiling.
- Any missing, malformed, non-finite, timed-out, or failed probe is `Inconclusive` and triggers owned-group cleanup.
- Signals may target only the admitted owned PGID. Escaped groups are observed as ownership loss and make the result `Inconclusive`; they are not signalled.
- A command exit of zero is `Pass`; an ordinary nonzero command exit is `Fail`; monitor breach/uncertainty, cleanup uncertainty, interruption, or receipt-publication failure is `Inconclusive`.
- Receipt directories are mode `0700`; receipts are atomic, fsynced, mode `0600`, bounded, and contain no environment values.
- New production behavior follows real red-before-green TDD.

---

### Task 1: Standalone owned-PGID pressure wrapper

**Files:**
- Create: `skills/deduplicating-functions/d6_pressure_monitor.py`
- Create: `skills/deduplicating-functions/tests/test_d6_pressure_monitor.py`

**Interfaces:**
- Produces: `MonitorThresholds(max_load1=8.0, max_swap_used_mb=12288.0, max_group_rss_mb=6144.0, sample_interval_s=1.0, term_grace_s=2.0, kill_grace_s=2.0)`.
- Produces: immutable `PressureSample(load1, swap_used_mb, group_rss_mb, member_pids, observed_at_utc)`.
- Produces: `run_monitored(argv: list[str], receipt_path: pathlib.Path, thresholds: MonitorThresholds = MonitorThresholds()) -> int`.
- Produces CLI: `python3 d6_pressure_monitor.py --receipt /absolute/private/result.json -- <exact command argv>`.
- Exit contract: `0=Pass`, `1=command Fail`, `2=usage refusal before launch`, `3=Inconclusive`.

- [ ] **Step 1: Write the failing unit tests for thresholds and probe parsing**

  Add tests that import the wished-for module and prove:

  ```python
  def test_pressure_boundaries_are_fail_closed():
      assert evaluate_sample(sample(load1=7.99)).breach is False
      assert evaluate_sample(sample(load1=8.0)).code == "D6_LOAD_BREACH"
      assert evaluate_sample(sample(swap_used_mb=12288.0)).breach is False
      assert evaluate_sample(sample(swap_used_mb=12288.01)).code == "D6_SWAP_BREACH"
      assert evaluate_sample(sample(group_rss_mb=6144.0)).breach is False
      assert evaluate_sample(sample(group_rss_mb=6144.01)).code == "D6_RSS_BREACH"
  ```

  Cover empty/malformed/non-finite load, swap, process census, and a census containing live, zombie, foreign-PGID, and owned-PGID rows. Assert only live owned members contribute to aggregate RSS.

- [ ] **Step 2: Run the focused tests and verify RED**

  Run:

  ```bash
  cd skills/deduplicating-functions
  PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m pytest \
    tests/test_d6_pressure_monitor.py -q -p no:cacheprovider
  ```

  Expected: collection/import failure because `d6_pressure_monitor.py` does not exist. Preserve the command, stdout, stderr, and true exit in the task report.

- [ ] **Step 3: Implement the pure sample and decision layer minimally**

  Create frozen dataclasses for thresholds, samples, and decisions. Validate every threshold as finite and positive. Parse Darwin `vm.swapusage`, Linux `/proc/meminfo`, `os.getloadavg()`, and canonical `ps -axo pid=,pgid=,rss=,state=` output. Treat zero live owned members while the leader is expected alive, malformed rows affecting the owned PGID, and any probe failure as `D6_MONITOR_UNAVAILABLE`.

- [ ] **Step 4: Run focused tests and verify GREEN**

  Run the Step 2 command. Expected: all pure-layer tests pass with no warnings.

- [ ] **Step 5: Write failing lifecycle tests before lifecycle implementation**

  Add deterministic injected-fake tests proving:

  - healthy samples plus child exit zero sends no signal and publishes `Pass`;
  - ordinary child nonzero publishes `Fail`, not `Inconclusive`;
  - `pgid != child_pid` refuses ownership before monitoring;
  - breach and probe uncertainty signal only `child_pid` as PGID;
  - TERM-resistant group receives KILL for the same PGID after grace;
  - a survivor or unavailable final census remains `Inconclusive`;
  - an escaped descendant produces ownership-loss `Inconclusive` without signalling its group;
  - receipt-publication failure returns `3` and cannot be reported as clean;
  - receipt schema is closed, bounded, mode `0600`, command digest matches NUL-joined argv, and no environment value is present.

- [ ] **Step 6: Run lifecycle tests and verify RED**

  Run the Step 2 command. Expected: assertion failures for missing `run_monitored` lifecycle behavior, not collection or fixture errors.

- [ ] **Step 7: Implement minimal lifecycle and CLI behavior**

  Use dependency-injected callables only at the internal runner boundary so tests exercise real decision/publication code. Launch with `subprocess.Popen(..., start_new_session=True)`, verify PGID, sample immediately and every second, and retain bounded samples plus peaks. On breach/uncertainty/interruption, freeze `Inconclusive`, TERM the owned PGID, wait against live-group census, KILL the same PGID if necessary, and require a final empty group. Publish the receipt by same-directory temp file, `fsync`, `os.replace`, and parent-directory `fsync`.

- [ ] **Step 8: Verify GREEN and run a disposable real-process integration test**

  Run the focused suite, including a helper that creates a real isolated child group in `tmp_path`; never invoke `run_pipeline.py` or detector commands. Expected: all tests pass and the foreign helper remains alive when the owned group is terminated.

- [ ] **Step 9: Run regression and static gates**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m pytest \
    tests/test_d6_pressure_monitor.py \
    tests/test_output_containment_and_cancellation.py \
    tests/test_resource_policy.py tests/test_safety.py tests/test_run_pipeline_caps.py \
    -q -p no:cacheprovider
  /opt/homebrew/bin/python3.12 -m py_compile \
    d6_pressure_monitor.py tests/test_d6_pressure_monitor.py
  /opt/homebrew/bin/python3.12 -m ruff check \
    d6_pressure_monitor.py tests/test_d6_pressure_monitor.py
  git diff --check
  ```

  Expected: pytest/static exits `0`; no D6 composite process appears in the process census.

- [ ] **Step 10: Commit the reviewed build**

  ```bash
  git add docs/superpowers/plans/2026-08-26-d6-owned-pgid-pressure-monitor.md \
    skills/deduplicating-functions/d6_pressure_monitor.py \
    skills/deduplicating-functions/tests/test_d6_pressure_monitor.py
  git commit -m "feat(dedup): add owned-group pressure monitor"
  ```

  Do not push, merge, install, or execute the D6 composite under this task.
