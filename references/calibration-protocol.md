# Calibration Protocol

Procedures for detecting and correcting agent drift, noise, and quality degradation across sessions.

---

## Agent Drift Monitoring (L6 Calibration Loop)

### Cadence
- **Routine:** Every 5th task, the Conductor injects a calibration bead
- **On suspicion:** If the Conductor notices declining quality, unexpected agent behavior, or increasing arbiter invocations

### Calibration Bead Process
1. Select or create a calibration bead — known-good code with 3-5 deliberately planted defects spanning at least 2 domains (e.g., one security flaw, one logic error, one missing timeout)
2. Run the calibration bead through L1 (Sentinel) + L2 (Oracle) + L2.5 (AQS)
3. Compare detection results against known-planted defects
4. **Detection rate >= baseline** → System is calibrated. Log result and continue.
5. **Detection rate < baseline** → System is drifting. Investigate:
   - Which defect types were missed? → Update regression watchlist
   - Which agents failed to detect? → Review agent prompts for decay
   - Has the constitution grown rules that conflict with detection? → Constitution review
6. After recalibration changes, re-run the same calibration bead to verify improvement

### Baseline
The baseline detection rate is established by the first calibration run. Initial target: detect >= 80% of planted defects. The baseline may increase as the system matures.

---

## Drift Signals

Three types of drift to monitor (from Agent Drift research, arXiv:2601.04170):

| Drift Type | Definition | Detection Signal | Response |
|-----------|-----------|-----------------|----------|
| **Semantic drift** | Agent outputs diverge from task intent while remaining syntactically valid | Fitness function scores declining across sessions; LOSA quality scores trending downward | Review agent prompts; check for prompt pollution from accumulated context |
| **Coordination drift** | Multi-agent consensus degrades | Arbiter invocations increasing per bead; more disputes, fewer clean resolutions | Review agent role boundaries; check for overlapping or conflicting instructions |
| **Behavioral drift** | Agents develop strategies not in their prompts | Agent outputs stop matching expected format; unexpected response patterns | Full agent prompt review; check for learned anti-patterns |

---

## Regression Watchlist

A running list of defect types that have been found and fixed in prior sessions. The Conductor periodically verifies these would still be caught.

| Defect Type | First Found | Domain | Detection Agent | Last Verified |
|-------------|------------|--------|-----------------|---------------|
| _(populated through adversarial engagement)_ | | | | |

Update this table after every calibration run. If a previously-caught defect type is missed, escalate immediately.

---

## Noise Audit

Measures consistency of the system's judgment by re-running the same review and comparing results.

### Cadence
- **Routine:** Every 10th task
- **On suspicion:** If the Conductor observes contradictory verdicts on similar findings

### Procedure
1. Select a completed bead that produced findings during its AQS engagement
2. Re-run the AQS cycle on the SAME bead (using different agent instances — fresh context)
3. Compare findings from the original run vs. the re-run:

| Overlap | Noise Level | Interpretation | Action |
|---------|------------|----------------|--------|
| > 80% | **LOW** | System is consistent | No action needed |
| 50-80% | **MODERATE** | Some inconsistency | Investigate which finding types are inconsistent; tighten rubrics |
| < 50% | **HIGH** | System is unreliable | Full investigation required — see noise type analysis below |

### Noise Type Analysis (for MODERATE or HIGH noise)

| Noise Type | Definition | Cause | Mitigation |
|-----------|-----------|-------|------------|
| **Level noise** | Different model instances produce systematically different severity ratings | Model temperature, sampling variation | Standardize rubrics with concrete anchored examples per severity level |
| **Pattern noise** | Same model weights some domains over others consistently | Training data skew, prompt emphasis | Rebalance domain emphasis in agent prompts; add calibration examples |
| **Occasion noise** | Same model rates same code differently based on what it reviewed just before | Context pollution, ordering effects | Reset agent context between beads; randomize review order |
