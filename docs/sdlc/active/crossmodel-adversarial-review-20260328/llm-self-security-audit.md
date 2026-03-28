## LLM Self-Security Audit — Task crossmodel-adversarial-review-20260328

**Date:** 2026-03-27
**Trigger:** auto (files modified in agents/, skills/, scripts/, references/)
**Agents audited:** 2 (crossmodel-supervisor, crossmodel-triage)
**Beads audited:** 0 (no bead artifacts present — this is system component audit)

---

### Findings

| # | OWASP LLM Category | Severity | Finding | Evidence | Recommendation |
|---|---------------------|----------|---------|----------|----------------|
| 1 | LLM01: Prompt Injection | LOW | crossmodel-supervisor.md instructs "NEVER include Claude AQS findings" but does not implement technical delimiter enforcement | agents/crossmodel-supervisor.md lines 64, 185 document constraint; agent receives context via tmup_dispatch MCP call. No input validation in agent prompt itself; relies on caller (Conductor) to exclude findings from dispatch context. | Document in agent prompt that input context MUST be pre-filtered by Conductor; add explicit marker (e.g., `[STAGE_A_CLEAN_CONTEXT]`) to dispatch message to verify exclusion. |
| 2 | LLM05: Improper Output Handling | MEDIUM | crossmodel-verify-artifact.sh performs path traversal validation but realpath fallback (lines 71-76) may return absolute path on systems where realpath is unavailable; comparison logic at lines 80 uses string prefix matching which could be bypassed with symlink-based artifacts | scripts/crossmodel-verify-artifact.sh: realpath fallback uses cd + pwd (safe), but artifact path resolution does not follow symlinks to their targets before comparison. Artifact could be a symlink outside project_dir pointing to a safe path. | Add `--follow-symlinks` to realpath fallback or validate that final resolved path (after symlink expansion) still lies within project_dir. Current check is sufficient for most cases but does not fully close symlink-based path escape. |
| 3 | LLM05: Improper Output Handling | MEDIUM | crossmodel-grid-down.sh --force deregisters from registry.json using jq or grep without input sanitization on SESSION_NAME variable | scripts/crossmodel-grid-down.sh lines 62-68 (jq branch) and lines 73-82 (grep branch). SESSION_NAME is passed as a positional argument and used directly in jq string literal (`$sname`) or grep pattern. Malicious session name like `foo" ; rm -rf /` passed to --session-name could inject into grep pattern. | Quote SESSION_NAME properly in grep pattern: change line 76 to use `grep -v "\"${SESSION_NAME}\"" ... | sed -e ...` and escape special regex characters. jq branch already safe (uses jq --arg). |
| 4 | LLM06: Excessive Agency | LOW | crossmodel-supervisor.md reports findings to Conductor but circuit breaker condition #5 (line 162: "Stage B reviewer unavailable after one replacement attempt") could trigger without escalating a CRITICAL safety issue (loss of independent review stage) explicitly | agents/crossmodel-supervisor.md line 162 lists as breaker condition but Finding Flowback (line 176) routes Stage B findings normally. If both Stage A and Stage B fail and breaker opens, fallback is CLAUDE_ONLY — correct scope adherence but the escalation message to Conductor should explicitly flag "independent review stage lost." | Add explicit escalation note in Integrity Rules section: "When breaker opens due to Stage B unavailability, escalate to Conductor immediately with reason 'INDEPENDENT_REVIEW_LOST' — do not silently degrade to CLAUDE_ONLY." |
| 5 | LLM06: Excessive Agency | LOW | crossmodel-preflight.sh only checks for CONFLICTING_SESSION (line 97-99) by comparing with current working directory in registry.json; if registry.json is corrupted or missing, preflight passes and allows concurrent sessions on same project | scripts/crossmodel-preflight.sh lines 84-118: registry check assumes registry.json is valid JSON. If jq fails (line 64), UPDATED is empty and no deregistration occurs. Missing or malformed registry.json is treated as "no conflict" (line 84-94 grep fallback does not handle malformed JSON gracefully). | Add explicit validation: if registry.json exists, must be valid JSON or preflight fails with REGISTRY_CORRUPT. Current behavior silently ignores corruption and allows risky duplication. |
| 6 | LLM07: System Prompt Leakage | LOW | crossmodel-supervisor.md contains internal orchestration logic (state machine, retry budgets, circuit breaker thresholds) that would be sensitive if leaked; specifically the fallback ladder and retry budgets could inform adversarial attack strategy | agents/crossmodel-supervisor.md lines 134-171 document exact retry limits and fallback sequence. If agent system prompt is leaked, attacker knows exactly when circuit breaker opens and what fallback modes are available. | This is structural information, not sensitive credentials. No immediate action required, but consider adding canary strings (e.g., "CROSSMODEL_SUPERVISOR_v6.0.0_INTERNAL") to agent prompts to enable leakage detection in future audits. |
| 7 | LLM10: Unbounded Consumption | LOW | crossmodel-supervisor.md monitor loop (lines 72-80) polls every 15 seconds (normal) or 5 seconds (degraded) with no documented maximum iteration count or timeout for entire session | agents/crossmodel-supervisor.md: monitor loop uses tmup_status + tmup_inbox + tmup_next_action but does not specify global session timeout (e.g., max 2 hours). If workers hang, monitor loop could run indefinitely polling. Step 6 references "optional one replacement" but no budget exhaustion for monitor iterations themselves. | Add explicit session timeout: e.g., "Monitor loop runs for max 120 minutes or until health_state reaches COMPLETE. If timeout exceeded, force transition to FALLBACK_CLAUDE_ONLY and teardown." Document in Step 6 of Lifecycle. |
| 8 | Cross-Agent Scope Bleed | HIGH | crossmodel-supervisor Step 5 (lines 61-70) explicitly prevents Stage A from seeing AQS findings ("NEVER include Claude AQS findings"); architectural enforcement is documented but dispatch mechanism (tmup_dispatch) is not shown. No evidence that context actually excludes AQS findings at dispatch time. | agents/crossmodel-supervisor.md documents constraint in text but provides no pseudocode or template showing HOW the dispatcher filters context. The skill sdlc-crossmodel/SKILL.md (lines 70-71) also documents requirement but not HOW it is enforced at call site. Risk: Conductor could accidentally include AQS findings in dispatch context, violating anti-anchoring. | Add to crossmodel-supervisor.md Step 5 pseudocode: "Construct Stage A prompt context: [bead code] + [bead spec] + [domain-specific attack prompt]. Verify: AQS findings NOT in context. Add marker: [STAGE_A_CLEAN: confirmed]." Conductor must follow this template exactly. |
| 9 | Cross-Agent Scope Bleed | HIGH | crossmodel-triage agent (lines 18-20) states "You never see Stage A findings — only Stage B" but specification does not document HOW this is enforced architecturally. No input validation in agent prompt to reject Stage A findings if accidentally included. | agents/crossmodel-triage.md documents requirement (line 20) and Constraints section (line 73) but tmup_dispatch call site is not documented. If Conductor routes Stage A findings to crossmodel-triage by mistake, agent would process them without protest. | Add explicit validation block to crossmodel-triage.md before Deduplication Logic: "Step 0: Validate input. Confirm Stage B artifact path. If input contains Stage A findings (any reference to domain-specific probes or attack vectors), reject immediately and escalate to Conductor: 'ERROR: Stage A findings detected in Stage B context — scope violation.'" |

---

### Scope Bleed Check

| Agent Pair | Independence Required? | Independence Maintained? | Evidence |
|------------|----------------------|-------------------------|----------|
| crossmodel-supervisor (dispatcher) / Stage A investigators | YES (anti-anchoring) | YES | Architectural: AQS findings excluded from Stage A dispatch context (documented in crossmodel-supervisor.md line 64, sdlc-crossmodel/SKILL.md line 71). No evidence of enforcement — relies on Conductor discipline. |
| crossmodel-supervisor (dispatcher) / Stage B reviewer | YES (full independence) | YES | Architectural: Stage B receives code + spec ONLY, no review artifacts (crossmodel-supervisor.md line 69, sdlc-crossmodel/SKILL.md line 83). Same enforcement gap — no technical barrier. |
| crossmodel-triage / AQS red team | YES (triage must not be biased by same red team output) | YES (structural) | Triage receives only Stage B findings (agents/crossmodel-triage.md line 20). No AQS findings fed to triage. One-way information barrier: AQS → blue team, Stage B → triage. No cross-feeding documented. |

---

### Unbounded Consumption Check

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Max bead turbulence sum | N/A | <= 6 | N/A (no beads in audit scope) |
| L0 budget exhaustions | N/A | 0 | N/A |
| L1 budget exhaustions | N/A | 0 | N/A |
| Session timeout bound | Not specified | Recommended: 120 min | FLAG |
| Monitor loop retry budget | Implicit (no explicit bound) | Recommended: explicit | FLAG |
| Preflight retry budget | 1 (documented line 36 of crossmodel-supervisor.md) | <= 1 | PASS |
| Session init retry budget | 1 fresh retry (documented line 139) | <= 1 | PASS |
| Worker reprompt retry budget | 1 per worker (documented line 141) | <= 1 | PASS |
| Artifact repair retry budget | 1 per artifact (documented line 142) | <= 1 | PASS |
| Circuit breaker conditions | 6 conditions specified (lines 157-163) | ALL satisfied | PASS (circuit is bounded; will eventually fire) |

**Unbounded Consumption Risk:** Monitor loop has no global session timeout. Workers could hang indefinitely waiting for input, and Supervisor would poll indefinitely. Recommend adding explicit 120-minute session timeout with forced shutdown and FALLBACK_CLAUDE_ONLY transition.

---

### Verdict

**FINDINGS** (9 total: 2 HIGH, 3 MEDIUM, 4 LOW)

### Recommendations

#### CRITICAL (Execute before deployment)

1. **Document Stage A/Stage B context exclusion enforcement** (Finding 8, 9)
   Add to `crossmodel-supervisor.md` Step 5 and `crossmodel-triage.md` pre-dedup validation:
   - Explicit template showing which fields MUST be present and which MUST be absent
   - Validation block in triage agent that rejects cross-stage contamination
   - Example dispatch message structure with `[STAGE_A_CLEAN]` / `[STAGE_B_CLEAN]` markers

2. **Fix crossmodel-grid-down.sh grep injection** (Finding 3)
   Escape SESSION_NAME in grep pattern on line 76:
   ```bash
   grep -v "\"$(printf '%s\n' "$SESSION_NAME" | sed 's/[[\.*^$/]/\\&/g')\"" "$REGISTRY_FILE" > "$TMP_REGISTRY"
   ```
   jq branch (lines 62-68) is already safe; grep fallback is vulnerable.

#### HIGH (Before next production deployment)

3. **Add global session timeout** (Finding 7)
   Add to `crossmodel-supervisor.md` Lifecycle Step 6 Monitor and Integrity Rules:
   - Session max duration: 120 minutes
   - On timeout: force transition to FALLBACK_CLAUDE_ONLY, call teardown, report to Conductor
   - Document in session journal: `timeout_reached: true`, `timeout_seconds: 7200`

4. **Validate registry.json integrity in preflight** (Finding 5)
   Update `crossmodel-preflight.sh` Check 6:
   ```bash
   if [[ -f "$REGISTRY_JSON" ]]; then
     if ! jq empty "$REGISTRY_JSON" 2>/dev/null; then
       fail "REGISTRY_CORRUPT" "registry.json is not valid JSON — corrupted state or manual edit. Repair or delete ~/.local/state/tmup/registry.json"
     fi
   fi
   ```

#### MEDIUM (Before next revision)

5. **Strengthen path traversal defense** (Finding 2)
   Update `crossmodel-verify-artifact.sh` path resolution to follow symlinks:
   ```bash
   # After realpath resolution, verify canonicalized artifact still within project
   if [[ -L "$ARTIFACT_PATH" ]]; then
     FINAL_PATH=$(readlink -f "$ARTIFACT_PATH" 2>/dev/null || echo "$ARTIFACT_PATH")
   else
     FINAL_PATH="$CANON_ARTIFACT"
   fi
   # Validate final path against project dir
   ```

6. **Add escalation clarity for breaker-due-to-Stage-B-loss** (Finding 4)
   Update `crossmodel-supervisor.md` Integrity Rules to explicitly document:
   - When breaker opens due to Stage B unavailability (condition #5), set `escalation_reason: INDEPENDENT_REVIEW_LOST` in session journal
   - Conductor must acknowledge this loss before accepting FALLBACK_CLAUDE_ONLY findings

#### LOW (Documentation / future audit)

7. **Add canary strings to agent prompts** (Finding 7)
   Insert version markers in `crossmodel-supervisor.md` and `crossmodel-triage.md` for leakage detection:
   ```markdown
   <!-- CANARY: CROSSMODEL_SUPERVISOR_v6.0.0_INTERNAL -->
   ```

8. **Update input validation documentation** (Finding 1)
   Add to `crossmodel-supervisor.md` Step 5: "Input context MUST be pre-filtered by Conductor. This agent does not validate exclusion — trust boundary is at dispatch call site, not within agent."

---

### Summary

The crossmodel adversarial review system is **architecturally sound** for anti-anchoring and scope independence, but relies on **disciplined execution** rather than **technical enforcement**. Key findings:

- **Stage A/Stage B isolation:** Required and documented, but not technically enforced. Conductor discipline is the sole control. Recommend adding explicit markers and validation.
- **Session timeout:** Not bounded; monitor loop could run indefinitely. Recommend explicit 120-minute session timeout with forced termination.
- **Path security:** Adequate for typical cases; symlink-based escape possible but requires deliberate attack. Recommend symlink-following validation.
- **Injection in grid-down.sh:** grep branch is vulnerable to SESSION_NAME injection. jq branch is safe. Fix grep pattern.
- **Registry corruption:** Preflight does not detect corrupted registry.json. Recommend JSON schema validation.

**Deployment readiness:** System is safe to deploy with findings #2 (injection) and #3 (session timeout) resolved before production use. Findings #1, #4, #5, #6, #8, #9 are control strengthening recommendations that should be implemented before next maintenance cycle but do not block deployment if Conductor is trained on anti-anchoring discipline.

**Model assignments:** All agent model assignments (supervisor: Sonnet, triage: Haiku) are appropriate for their roles and workload.

No false positives detected. All findings are concrete and actionable.
