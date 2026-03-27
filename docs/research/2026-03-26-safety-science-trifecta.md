# The Safety Science Trifecta: Dekker, Reason, and Leveson Applied to Multi-Agent SDLC

**Date:** 2026-03-26
**Scope:** Complete framework analysis of three accident/safety models and their mapping to the SDLC-OS loop hierarchy (L0-L6)

---

## Preface: Why Three Models, Not One

These three scholars represent fundamentally different ontologies of how accidents happen:

- **James Reason** asks: "Which defenses failed?" -- Accidents are trajectories through holes in layered defenses
- **Sidney Dekker** asks: "How did this become normal?" -- Accidents are endpoints of locally rational drift
- **Nancy Leveson** asks: "Which controls were inadequate?" -- Accidents are control problems, not failure problems

No single model is complete. Reason's Swiss Cheese misses emergent behavior. Dekker's Drift misses structural control gaps. Leveson's STAMP misses the social dynamics that erode controls over time. Together, they form a trifecta that catches what each individually cannot.

---

# Part I: James Reason -- Defenses, Holes, and Latent Conditions

## 1.1 The Complete Model

### From "Human Error" (1990)

Reason's foundational contribution is the **Generic Error Modelling System (GEMS)**, which classifies human error by the cognitive level at which it occurs:

| Performance Level | Error Type | Mechanism | Example |
|---|---|---|---|
| **Skill-based** | Slips and lapses | Attentional failures in automated routines; memory failures | Typing the wrong command in a familiar workflow |
| **Rule-based** | Mistakes | Misapplying a good rule; applying a bad rule; failing to apply any rule | Using the right pattern for the wrong problem ("strong but wrong") |
| **Knowledge-based** | Mistakes | Reasoning failures when no rules apply; bounded rationality under novelty | Incorrect first-principles reasoning about an unfamiliar system state |

The critical insight: as expertise increases, errors shift from knowledge-based (wrong reasoning) to skill-based (right reasoning, wrong execution). Experts make *different* errors, not *fewer* errors.

**Active failures vs. latent conditions:** Active failures are unsafe acts committed by the people at the sharp end (the operator, the runner). Latent conditions are decisions made by designers, builders, and managers that lie dormant in the system until they combine with active failures and local triggers to breach all defenses. Latent conditions are the "resident pathogens" -- they are present long before the accident and are invisible to the people they will eventually harm.

### From "Managing the Risks of Organizational Accidents" (1997)

**The Swiss Cheese Model:** Multiple defensive layers, each with holes. The holes are caused by active failures (transient) and latent conditions (resident). An accident occurs when holes in successive layers momentarily align, creating a trajectory of opportunity for a hazard to reach a loss.

**The four levels of the organizational accident:**

1. **Organizational influences** -- corporate culture, resource allocation, strategic decisions
2. **Unsafe supervision** -- inadequate oversight, failed correction, supervision violations
3. **Preconditions for unsafe acts** -- adverse mental states, physical limitations, crew resource management failures
4. **Unsafe acts** -- errors (skill/rule/knowledge) and violations (routine or exceptional)

**Production vs. protection trade-off:** Every organization must balance production pressure against protective measures. Under sustained production pressure, protective measures are the first to erode because they cost money and slow output without producing visible returns -- until the accident.

**The five components of safety culture:**

1. **Informed culture** -- the organization collects, analyzes, and disseminates safety data
2. **Reporting culture** -- people report errors and near-misses without fear
3. **Just culture** -- clear line between acceptable and unacceptable behavior; honest errors distinguished from reckless violations
4. **Learning culture** -- the organization draws correct conclusions from safety data and implements reforms
5. **Flexible culture** -- the organization can shift from hierarchical to flat structures during crises

The first four create the fifth: an informed culture. Together they constitute what Reason calls a "safety culture."

## 1.2 Mapping to the SDLC-OS Loop Hierarchy

The SDLC-OS loop hierarchy (L0-L6) **is** a Swiss Cheese Model, whether it was designed as one or not. Each loop level is a defensive layer with its own holes:

| Loop Level | Reason's Defense Layer | Holes (What Gets Through) |
|---|---|---|
| **L0: Runner self-correction** | Sharp-end operator defense | Skill-based slips: runner makes the same mistake 3 times because the error is in its "reasoning pattern," not its attempt count. Knowledge-based mistakes when the problem is novel. |
| **L1: Sentinel + drift-detector** | Supervisory defense | Latent condition: Sentinel's verification checklist does not cover the specific failure mode. Drift-detector checks architectural patterns but not semantic correctness. |
| **L2: Oracle audit** | Technical defense (test quality) | Rule-based mistakes: Oracle applies VORP standard to tests that are structurally correct but semantically vacuous (the test passes but proves nothing meaningful). |
| **L2.5: AQS adversarial** | Adversarial defense (red/blue/arbiter) | Knowledge-based mistakes: Red team cannot imagine attack vectors outside its training distribution. Recon guppies miss threats in domains they are not assigned to probe. |
| **L3-L4: Bead/Phase management** | Organizational defense (Conductor decomposition) | Latent conditions in bead decomposition: the Conductor splits work such that a security-critical interaction falls between two beads, checked by neither. |
| **L5: Task loop** | Strategic defense (mission alignment) | Production pressure: the "3 full passes" budget creates implicit pressure to pass on the first try, discouraging the Conductor from detecting problems that would require re-entry. |
| **L6: Calibration** | Systemic defense (drift detection) | The 5-task cadence means latent conditions can accumulate for 4 tasks between checks. Planted defects may not cover the specific failure mode that has drifted. |

### GEMS Error Types in the Agent Context

| GEMS Level | Agent Analogue | Detection Layer |
|---|---|---|
| **Skill-based (slips/lapses)** | Syntax errors, wrong file paths, malformed output, off-by-one in generated code | L0 (runner self-correction via metric command -- lint, typecheck) |
| **Rule-based (mistakes)** | Applying a design pattern to the wrong problem; using the right convention in the wrong context; "strong but wrong" pattern matching | L1 (Sentinel/drift-detector catch pattern violations) and L2 (Oracle catches structurally-correct-but-wrong tests) |
| **Knowledge-based (mistakes)** | Fundamental misunderstanding of the problem domain; incorrect first-principles reasoning about novel system behavior; security threats the agent has never seen in training | L2.5 (AQS) and L6 (Calibration) -- these are the hardest to catch because they require adversarial thinking and cross-session learning |

## 1.3 Failure Modes Reason Predicts That the System Does Not Currently Catch

**1. Latent condition backtracing.** When AQS finds a defect, the system fixes the active failure (the code) but does not systematically trace backward to identify the latent condition. Why did L0, L1, and L2 miss it? The existing `Principle extracted` field in the Code Constitution is a step in this direction, but it captures the *rule* without diagnosing the *upstream hole*. A structured latent condition trace -- "this finding passed through L0 because [runner had no test for this pattern], through L1 because [Sentinel checklist lacks this category], through L2 because [Oracle tests were structurally valid but semantically empty for this case]" -- would enable preventive patching of upstream layers.

**2. Resident pathogen accumulation.** The system does not track which latent conditions are accumulating across tasks. If three consecutive tasks all have AQS findings that escaped L1 because the drift-detector does not check for temporal coupling violations, that is a resident pathogen in the L1 layer. The calibration protocol (L6) checks detection rates but does not aggregate *which layer's holes* are consistently aligned.

**3. Production vs. protection erosion.** The error budget policy defines three states (healthy/warning/depleted) but does not track the *direction* of drift between them. A system that oscillates between healthy and warning is different from one that has been healthy for 20 consecutive tasks. Reason would predict that extended "healthy" periods breed complacency -- the protection layers (AQS, Oracle) are still running but the Conductor may be unconsciously routing more work to "Clear" classification to avoid the cost of full adversarial engagement.

**4. Organizational influences on bead decomposition.** Reason's four-level model places "organizational influences" at the top. In the SDLC-OS, the Conductor's decomposition decisions are the organizational level. If the Conductor consistently creates beads that are too large (to minimize agent invocations) or too granular (to avoid complex integration), those decomposition patterns create latent conditions that propagate through all downstream layers. No current mechanism audits the *quality of decomposition itself*.

## 1.4 Concrete Embedding Mechanisms

**Mechanism R1: Latent Condition Trace (extends AQS report)**

Every accepted/sustained AQS finding gains a `## Latent Condition Trace` section:

```
## Latent Condition Trace: Finding F-{id}
| Layer | Hole | Why It Missed | Fix Category |
|-------|------|--------------|-------------|
| L0 (Runner) | No self-test for this pattern | Runner metric command does not cover temporal coupling | Add pattern to bead acceptance criteria |
| L1 (Sentinel) | Drift-detector checks DRY/SoC but not temporal coupling | Detection category gap | Add temporal coupling to drift-detector checklist |
| L2 (Oracle) | Tests passed but did not exercise the specific interaction | Test coverage gap (semantic, not line-based) | Oracle should flag untested state transitions |
```

**Mechanism R2: Resident Pathogen Registry (new reference file)**

A running tally of which defensive layers have been penetrated, by which finding categories, across tasks:

```
## Resident Pathogen Registry
| Pathogen ID | Layer Penetrated | Category | Tasks Observed | Status |
|---|---|---|---|---|
| RP-001 | L1 | Temporal coupling not checked | Tasks 5, 8, 12 | OPEN -- drift-detector enhancement needed |
| RP-002 | L2 | Vacuous assertion patterns | Tasks 3, 7 | RESOLVED -- Oracle prompt updated |
```

**Mechanism R3: Protection Erosion Monitor (extends calibration protocol)**

Track not just SLO compliance but the *trajectory* of protection engagement:

```
## Protection Engagement Trend
| Metric | 5-task rolling average | Direction | Signal |
|---|---|---|---|
| % beads classified Clear | 62% | UP from 45% | WARNING: possible normalization |
| % beads receiving full AQS | 28% | DOWN from 40% | WARNING: protection erosion |
| Mean AQS findings per bead | 1.2 | STABLE | OK |
| L1 correction rate | 8% | DOWN from 15% | AMBIGUOUS: could be quality improvement OR detection decay |
```

**Mechanism R4: Safety Culture Mapping**

Map Reason's five culture components to concrete SDLC-OS mechanisms:

| Culture Component | Current Mechanism | Gap |
|---|---|---|
| **Informed** | Quality SLOs, calibration protocol, LOSA observer | No aggregated cross-task dashboard; data is per-task |
| **Reporting** | Correction signal format, naked escalation prohibition | Agents cannot "report" concerns outside their loop -- a runner that notices something wrong in a *different* bead has no channel to report it |
| **Just** | Three error categories implicit; no explicit discipline model | No formal distinction between runner errors (console), prompt gaps (coach), and adversarial manipulation (discipline) |
| **Learning** | Code Constitution, precedent system | Learning is rule-based (new rules) but not structural (upstream layer patching) |
| **Flexible** | Cynefin-based scaling, error budget state transitions | System scales scrutiny levels but does not restructure authority -- Conductor always conducts, even when the problem might benefit from a different coordination pattern |

## 1.5 How Reason Complements Dekker and Leveson

**What Reason catches that Dekker misses:** Reason provides a concrete structural model (layered defenses with identifiable holes) that can be audited mechanically. Dekker's drift model explains *why* holes grow but does not provide a framework for *counting* them or *locating* them at specific layers. The SDLC-OS needs both: Dekker to explain why the holes are growing, Reason to identify where they are right now.

**What Reason catches that Leveson misses:** Reason's GEMS classification (skill/rule/knowledge errors) maps directly to the different cognitive modes of LLM agents. Leveson's STAMP treats all unsafe control actions uniformly -- it does not distinguish between an agent that "slipped" (produced wrong output despite correct reasoning) and one that "mistook" (applied the wrong reasoning entirely). The error type matters for correction strategy: slips need better metrics, mistakes need better prompts, knowledge failures need better training data or model capabilities.

**What Reason misses that the others catch:** Reason's model is fundamentally *linear* -- the trajectory of opportunity passes through layers in sequence. It does not capture emergent failures that arise from interactions between components that are each individually safe (Leveson's domain) or the social dynamics that cause defensive layers to decay over time (Dekker's domain).

---

# Part II: Sidney Dekker -- Drift, Local Rationality, and Safety-II

## 2.1 The Complete Model

### From "Drift Into Failure" (2011)

Dekker's central thesis: complex systems do not fail because a component breaks. They drift toward catastrophe through an accumulation of locally rational decisions, each of which is a small, sensible adaptation to immediate pressures. The five properties of drift:

1. **Scarcity and competition** -- Organizations face resource constraints and competitive pressure that create incentives to cut corners. Each cut is small and saves real resources. The accumulated effect is invisible until the accident.

2. **Decrementalism** -- The drift happens in tiny increments. Each step is only a small deviation from the previously accepted norm. No single step crosses a bright line. The normalization of deviance is gradual: yesterday's exception is today's standard practice and tomorrow's minimum.

3. **Sensitive dependence on initial conditions** -- Small early decisions constrain all future decisions. Path dependency means that once the system has drifted in a direction, returning to the original state becomes increasingly expensive. The system is locked into its drift trajectory.

4. **Unruly technology** -- Complex systems behave in ways that are not fully predictable or understandable, even by their designers. The technology itself generates surprises that force local adaptations, which feed back into the drift cycle.

5. **Contribution of the protective structure** -- The very mechanisms designed to protect against failure can contribute to drift. Safety reviews become ritualistic. Checklists become tick-box exercises. Compliance becomes a performance rather than a practice. The protective structure creates an *illusion* of safety that enables further drift.

**Practical drift** (from Snook, 2000, cited extensively by Dekker): The slow, steady uncoupling of practice from written procedure. Behavior that is acquired in practice and "works" becomes legitimized through unremarkable repetition. Over time, the gap between work-as-imagined and work-as-done widens silently.

### From "The Field Guide to Understanding Human Error" (2014)

**The Old View vs. The New View:**

| Dimension | Old View | New View |
|---|---|---|
| Human error is... | A cause of failure | A symptom of deeper trouble |
| Response to error | Find and fix the bad apple | Understand the system conditions |
| Investigation | Who is responsible? | What is responsible? |
| Accountability | Blame and punishment | Learning and improvement |

**Local rationality principle:** People did not come to work to do a bad job. Their actions made sense to them at the time, given their knowledge, goals, pressures, and focus of attention. Hindsight makes their actions look negligent only because we know the outcome. Explaining why people did what they did requires reconstructing the situation as it appeared to them, not as it appears to the post-accident investigator who knows how it ended.

**Hindsight bias:** Knowing the outcome changes our assessment of the decisions that led to it. Actions that seemed reasonable before the outcome are judged as negligent after the outcome. The solution is to bracket the outcome: examine the decision as it was made, with only the information available at the time.

**The "bad apple" theory:** The belief that the system is basically safe if it were not for those few unreliable people in it. This leads to a focus on finding and removing bad individuals rather than fixing the system that made their errors possible, predictable, and inevitable.

### From "Just Culture" (2007, 2012, 2016)

Dekker's just culture model provides a response framework calibrated to three categories of behavior:

| Category | Definition | Appropriate Response |
|---|---|---|
| **Honest error** | Unintentional action or decision; the person was trying to do the right thing | Console. Learn from the system conditions that made the error possible. Fix the system. |
| **At-risk behavior** | Conscious decision to take a shortcut or deviation, believing the risk is justified or minimal; the person did not intend harm | Coach. Help the person understand the risk they underestimated. Fix the incentive structure that made the shortcut attractive. |
| **Reckless behavior** | Deliberate, conscious disregard for a substantial and unjustifiable risk; the person knew the risk and chose to ignore it | Discipline. This is the only category where individual accountability is appropriate. |

**Forward-looking accountability vs. backward-looking blame:** Backward-looking accountability asks "who is responsible for this outcome?" Forward-looking accountability asks "who is responsible for making things better going forward?" The former produces punishment; the latter produces learning.

### Safety-II (Dekker/Hollnagel)

Traditional safety (Safety-I) focuses on why things go wrong. Safety-II focuses on why things usually go right.

**Core principles:**

- Everyday performance variability is the source of both success and failure. The same adaptations that normally produce good outcomes occasionally produce bad ones. You cannot eliminate the variability that causes failure without also eliminating the variability that creates success.
- Success is not the absence of failure. Success requires active adaptation, adjustment, and anticipation. Studying only failures gives a distorted picture of how the system actually works.
- Resilience is not "bouncing back" from failure -- it is the ability to adjust before, during, and after disturbances. Four capacities of resilience: anticipate, monitor, respond, learn.

## 2.2 Mapping to the SDLC-OS Loop Hierarchy

### Where Drift Happens in the System

| Drift Vector | SDLC-OS Manifestation | Loop Level Affected |
|---|---|---|
| **Scarcity/competition → corner-cutting** | Conductor classifies more beads as "Clear" to save agent invocations. Error budget stays "healthy" because fewer beads are scrutinized, so fewer findings emerge -- a self-reinforcing cycle. | L3-L5 (bead/phase/task management) |
| **Decrementalism → normalization of deviance** | Each accepted residual risk in AQS (bead exits L2.5 with `hardened + residual risk documented`) slightly lowers the threshold for what residual risk is acceptable. Over many tasks, the definition of "acceptable residual risk" has migrated substantially from its starting point. | L2.5 (AQS) |
| **Sensitive dependence on initial conditions → path lock-in** | The Code Constitution and precedent system accumulate rules and verdicts that constrain future decisions. An early arbiter verdict on a borderline case becomes binding precedent that shapes all subsequent rulings in that domain. If the early verdict was wrong, the entire precedent chain is contaminated. | L2.5 (Arbiter/precedent system) |
| **Unruly technology → LLM unpredictability** | LLM agents produce surprising outputs that force local adaptations. When a runner produces an unexpected but functional solution, the Sentinel may accept it because it passes the metric, even though it deviates from conventions. This "works" repeatedly until it does not. | L0-L1 (Runner/Sentinel) |
| **Protective structure → ritualistic compliance** | The Sentinel verifies against a checklist. Over time, the checklist becomes a ritual: items are checked because they are on the list, not because they are meaningful for this specific bead. The drift-detector runs its multi-layer detection process, but its categories become stale as the codebase evolves. | L1 (Sentinel) |

### Just Culture Mapping for Agent Errors

| Dekker Category | Agent Analogue | System Response |
|---|---|---|
| **Honest error** | Runner produces incorrect output despite correctly following its prompt. The prompt was adequate; the model's reasoning simply failed on this particular input. | Console: accept the error, fix via L0 self-correction or L1 sentinel correction. No prompt changes needed. The error is in the stochastic nature of the model, not the system. |
| **At-risk behavior** | Runner takes a shortcut (skips metric command, produces superficial tests, uses a known anti-pattern because it is faster). The runner's prompt tells it not to, but the model's training distribution makes the shortcut attractive. | Coach: fix the incentive structure. Strengthen the metric command (make it harder to skip). Add the anti-pattern to the drift-detector's watchlist. The correction targets the system, not the model. |
| **Reckless behavior** | An agent prompt is written in a way that actively encourages unsafe behavior (e.g., "prioritize speed over correctness" or "skip tests for simple changes"). This is a design choice, not a model failure. | Discipline: the prompt must be changed. This is the *only* case where the fix is at the prompt/design level rather than the system level. Reckless behavior in a multi-agent system is always a design problem, never an agent problem -- agents do what their prompts and training tell them to do. |

### Safety-II: Studying Success in the System

The LOSA observer currently focuses on finding errors in completed work. Dekker's Safety-II says this is necessary but insufficient. The LOSA observer should also capture **successful adaptations**:

- Cases where a runner correctly handled ambiguous requirements without escalation
- Cases where the Sentinel caught a real issue that would have caused problems downstream
- Cases where AQS red team found a genuine vulnerability that would have reached production
- Cases where the Conductor's bead decomposition was unusually effective

These "success stories" build a reference library of what good performance looks like in this system, enabling the Conductor to recognize and reinforce effective patterns rather than only correcting ineffective ones.

## 2.3 Failure Modes Dekker Predicts That the System Does Not Currently Catch

**1. Normalization of deviance in Cynefin classification.** The Conductor's Cynefin classification determines how much scrutiny a bead receives. If the Conductor trends toward "Clear" classification (whether due to genuine simplicity or unconscious optimization), the system progressively reduces its own protection without any single decision being objectively wrong. No current mechanism tracks the *distribution* of Cynefin classifications over time.

**2. Ritualistic Sentinel compliance.** The Sentinel verifies against criteria, but there is no mechanism to detect whether the verification is *substantive* (the Sentinel genuinely engaged with the bead's specific risks) or *ritualistic* (the Sentinel checked boxes because the format was correct). Dekker would predict that over repeated invocations, the Sentinel's verification becomes increasingly formulaic.

**3. Precedent lock-in without periodic review.** The precedent system accumulates arbiter verdicts that constrain future decisions. Dekker's concept of path dependency predicts that early precedents will have outsized influence because they constrain the space of possible future verdicts. No mechanism exists to periodically review whether established precedents are still appropriate or whether they have locked the system into a suboptimal trajectory.

**4. Invisible work-as-done vs. work-as-imagined gap.** The SDLC-OS has extensive documentation of how the system *should* work (the SKILL.md files, agent prompts, loop definitions). But there is no systematic comparison of how work is *actually done* against these specifications. Over time, actual practice drifts from documented procedure. The gap is invisible because no one is measuring it.

**5. Success-induced complacency.** Extended periods of "healthy" error budget status may indicate genuine quality improvement or may indicate that the system has drifted into a state where it is no longer detecting problems it should detect. The system cannot distinguish between these two states without an external reference (the calibration bead addresses this partially, but only for code defects, not for process drift).

## 2.4 Concrete Embedding Mechanisms

**Mechanism D1: Deviance Normalization Detector (extends calibration protocol)**

Track the following drift indicators across tasks:

```
## Deviance Normalization Monitor
| Indicator | Baseline | Current (5-task avg) | Direction | Alert |
|---|---|---|---|---|
| % beads classified Clear | {first-task value} | {current} | {UP/DOWN/STABLE} | >15% above baseline: INVESTIGATE |
| Mean residual risk accepted per task | {first-task value} | {current} | {UP/DOWN/STABLE} | Upward trend over 3+ tasks: INVESTIGATE |
| AQS skip rate (trivial beads) | {first-task value} | {current} | {UP/DOWN/STABLE} | >20% above baseline: INVESTIGATE |
| Convention violations accepted (not corrected) | {first-task value} | {current} | {UP/DOWN/STABLE} | Upward trend: INVESTIGATE |
| Precedent age without review | N/A | {oldest unreviewed} | N/A | >10 tasks since review: MANDATORY REVIEW |
```

**Mechanism D2: Substantive Verification Audit (extends LOSA observer)**

The LOSA observer adds a "verification depth" assessment to its existing TEM framework:

```
### Verification Depth Assessment
- Did the Sentinel's findings reference specific file:line locations in THIS bead? (vs generic boilerplate)
- Did the Oracle's test audit identify specific test gaps in THIS bead? (vs repeating standard VORP checklist)
- Did the AQS recon guppies find bead-specific signals? (vs domain-generic observations)
**Verification depth score:** SUBSTANTIVE | FORMULAIC | MIXED
```

**Mechanism D3: Precedent Sunset Protocol (extends precedent system)**

Every precedent carries a "review-by" task count. After that count, the Conductor must either:
- Reaffirm the precedent (with fresh reasoning, not just "still valid")
- Retire the precedent (with documented reason)
- Modify the precedent (with documented delta)

Stale precedents that have not been reviewed are flagged as `STALE` and carry reduced weight in arbiter decisions until reaffirmed.

**Mechanism D4: Work-as-Done Audit (new periodic check)**

Every 10th task, sample 3 completed beads and compare actual agent behavior against documented procedure:
- Did the runner actually run its metric command? (check for evidence in output)
- Did the Sentinel produce bead-specific findings? (vs boilerplate)
- Did the Oracle audit actual test behavior? (vs structural test format)
- Did the AQS recon burst actually fire 8 guppies? (vs shortcutting)

This is the multi-agent analogue of Dekker's "work-as-done vs. work-as-imagined" comparison.

**Mechanism D5: Safety-II Success Library (extends LOSA observer)**

```
### Successful Adaptation Observed
**What happened:** Runner encountered ambiguous requirement in bead B-{id}, correctly inferred intent from surrounding code patterns, and produced a solution that passed all review layers without correction.
**Why this matters:** Demonstrates effective autonomous disambiguation -- a capability to reinforce.
**Pattern tag:** autonomous-disambiguation
```

These are accumulated and reviewed during L6 calibration. Patterns that appear repeatedly become documented best practices in agent prompts.

## 2.5 How Dekker Complements Reason and Leveson

**What Dekker catches that Reason misses:** Reason's model is a snapshot -- it shows where the holes are right now. Dekker explains *how the holes got there* and *why they will keep growing*. The SDLC-OS needs both: Reason to locate current defensive gaps, Dekker to predict how those gaps will evolve over time. Specifically, Dekker catches the social/organizational dynamics (production pressure, normalization, ritualistic compliance) that silently erode Reason's defensive layers.

**What Dekker catches that Leveson misses:** Leveson's STAMP model assumes that the control structure is known and can be analyzed. Dekker observes that the *actual* control structure drifts from the *documented* control structure over time. In the SDLC-OS, the documented loop hierarchy (L0-L6) is the "work-as-imagined" control structure. The actual behavior of agents within those loops may diverge without anyone noticing. Dekker provides the framework for detecting and measuring this divergence.

**What Dekker misses that the others catch:** Dekker's model is primarily *descriptive* -- it explains how drift happens but does not provide a systematic method for *preventing* it prospectively. Leveson's STPA provides proactive hazard identification. Reason's layered defense model provides concrete architectural guidance. Dekker tells you where to look; the others tell you what to build.

---

# Part III: Nancy Leveson -- Safety as a Control Problem

## 3.1 The Complete Model

### STAMP: Systems-Theoretic Accident Model and Processes

Leveson's fundamental reframing: Safety is not a failure problem; it is a **control problem**. Accidents do not occur because components fail. They occur because the control structure that enforces safety constraints is inadequate. Components can be functioning perfectly and an accident can still occur if the control actions are wrong, missing, mistimed, or applied for the wrong duration.

**Core elements of a safety control structure:**

```
                    ┌─────────────┐
                    │  Controller  │
                    │ (process     │
                    │  model)      │
                    └──┬───────┬──┘
           Control     │       │  Feedback
           actions     │       │  (sensors)
                    ┌──▼───────▼──┐
                    │  Controlled  │
                    │  Process     │
                    └─────────────┘
```

Every controller -- human or automated -- maintains a **process model**: its understanding of the current state of the controlled process. Accidents frequently result from inconsistencies between the controller's process model and the actual process state. This can happen because:

- The process model was wrong from the start (flawed design)
- The process model was correct but has become stale (missing feedback)
- The feedback channel is delayed, filtered, or broken
- The controller received feedback but misinterpreted it
- The controller's model updated correctly but the control action was wrong

**Safety constraints vs. safety requirements:** Reason and traditional safety focus on preventing specific failure events. Leveson focuses on enforcing constraints on system behavior. A constraint says "the system must never enter state X" rather than "component Y must not fail." This is more powerful because it covers emergent failures that arise from interactions between non-failed components.

### STPA: System-Theoretic Process Analysis

STPA is Leveson's proactive hazard analysis method. It identifies hazards by systematically analyzing the control structure:

**Step 1: Define purpose, losses, and system-level hazards**
- Losses: unacceptable outcomes (data breach, corrupt state, service outage)
- Hazards: system states that can lead to losses

**Step 2: Model the safety control structure**
- Identify all controllers, control actions, feedback channels, and controlled processes
- Include human controllers, automated controllers, and organizational controllers

**Step 3: Identify Unsafe Control Actions (UCAs)**

For every control action in the system, systematically enumerate four types of unsafe control actions:

| UCA Type | Description | Multi-Agent Example |
|---|---|---|
| **Not provided** | A required control action is not issued when needed | Sentinel does not issue a correction directive when the runner's output violates a convention |
| **Provided unsafely** | A control action is issued that creates a hazard | Conductor issues a bead decomposition that splits a security-critical transaction across two beads, breaking atomicity |
| **Wrong timing/order** | A control action is issued too early, too late, or out of sequence | Oracle audit fires before Sentinel has completed L1 verification, so Oracle audits unverified code |
| **Stopped too soon / applied too long** | A continuous control action is discontinued prematurely or continues beyond its safe window | Runner self-correction loop exhausts its budget (3 attempts) and submits STUCK status, but the real issue is that the metric command itself is wrong -- more attempts would not help; the *metric* needs changing |

**Step 4: Identify loss scenarios (causal factors)**

For each UCA, trace backward through the control structure to identify *why* the unsafe control action could occur:

- Controller received incorrect feedback
- Controller's process model is inconsistent with actual process
- Control action was correctly issued but not executed by the actuator
- Control action was executed but the controlled process did not respond as expected
- Feedback delay caused the controller to act on stale state

### CAST: Causal Analysis using STAMP

CAST is the post-accident investigation analogue of STPA. Given an accident that has already occurred, CAST:

1. Identifies the system hazard(s) that were inadequately controlled
2. Models the safety control structure that should have prevented the accident
3. For each controller in the structure, identifies what control actions were taken and why they were inadequate
4. Identifies the flawed process models that led to inadequate control
5. Recommends changes to the control structure (not just the component that "failed")

### Safety Constraints as a Design Principle

Leveson argues that safety constraints are more fundamental than safety requirements. A requirement says "the system shall do X." A constraint says "the system shall never enter state Y." Constraints are more robust because:

- They are stated negatively (what must not happen) rather than positively (what must happen)
- They can be verified by monitoring: you can detect a constraint violation in real time
- They survive design changes: even if the implementation changes, the constraint remains valid
- They compose: multiple constraints can be enforced simultaneously without conflict

## 3.2 Mapping to the SDLC-OS Loop Hierarchy

### The SDLC-OS as a STAMP Control Structure

```
┌─────────────────────────────────────────────────────────────┐
│ L5: USER (ultimate controller)                               │
│   Process model: task requirements, quality expectations      │
│   Control action: task specification, accept/reject delivery  │
│   Feedback: delivered artifacts, gap reports                  │
├─────────────────────────────────────────────────────────────┤
│ L5/L4/L3: CONDUCTOR (Opus — primary automated controller)    │
│   Process model: task state, bead statuses, quality budget    │
│   Control actions: decompose, dispatch, escalate, re-route    │
│   Feedback: bead outputs, sentinel reports, oracle audits,    │
│            AQS findings, LOSA observations                    │
├─────────────────────────────────────────────────────────────┤
│ L2.5: AQS (red/blue/arbiter — adversarial controller)        │
│   Process model: code under test, domain attack vectors       │
│   Control actions: find/rebut/arbitrate/fix                   │
│   Feedback: test results, code traces, evidence bundles       │
├─────────────────────────────────────────────────────────────┤
│ L2: ORACLE (test integrity controller)                        │
│   Process model: VORP standard, test quality criteria         │
│   Control actions: audit tests, flag deficiencies             │
│   Feedback: test execution results, coverage data             │
├─────────────────────────────────────────────────────────────┤
│ L1: SENTINEL (verification controller)                        │
│   Process model: bead acceptance criteria, conventions        │
│   Control actions: verify, correct, flag drift                │
│   Feedback: runner output, drift-detector report, convention  │
│            enforcer report                                    │
├─────────────────────────────────────────────────────────────┤
│ L0: RUNNER (Sonnet — lowest-level controller/actuator)        │
│   Process model: bead spec, metric command                    │
│   Control actions: write code, run tests, self-correct        │
│   Feedback: metric command output (lint, typecheck, tests)    │
├─────────────────────────────────────────────────────────────┤
│ CONTROLLED PROCESS: the target codebase                       │
│   State: files, tests, types, conventions                     │
└─────────────────────────────────────────────────────────────┘
```

### STPA Analysis of the SDLC-OS

**Losses defined for the multi-agent SDLC:**
- L-1: Defective code shipped to user (functional, security, reliability defects)
- L-2: Correct code rejected (false positive findings waste resources, frustrate user)
- L-3: System loses calibration without detection (silent quality degradation)
- L-4: Excessive resource consumption without proportional quality gain

**System-level hazards:**
- H-1: Code with undetected defects reaches "merged" status (leads to L-1)
- H-2: Valid code is blocked by false/irrelevant findings (leads to L-2)
- H-3: Defensive layers stop detecting defect categories they previously caught (leads to L-3)
- H-4: Full AQS engagement on trivial beads; trivial engagement on complex beads (leads to L-4)

**Unsafe Control Actions (systematic enumeration):**

| Controller | Control Action | Not Provided | Provided Unsafely | Wrong Timing | Stopped Too Soon / Too Long |
|---|---|---|---|---|---|
| **Conductor** | Bead decomposition | Critical functionality is not decomposed into beads (omitted from task) | Bead boundaries split an atomic operation, breaking transactional integrity | Beads dispatched before Scout phase has adequate codebase context | Conductor stops decomposing when there are "enough" beads rather than when all functionality is covered |
| **Conductor** | Cynefin classification | Bead is not classified (defaults to complicated) | Complex bead classified as Clear, skipping AQS entirely | Classification occurs before recon signals are available | N/A |
| **Conductor** | Escalation | Conductor does not escalate a stuck bead to the user | Conductor escalates prematurely, before inner loops have exhausted their budgets | Escalation happens after so many failed cycles that the correction history is too long for the user to parse | Conductor escalates once but does not follow up on user response |
| **Runner** | Code generation | Runner does not produce code for part of the bead spec | Runner produces code that introduces a vulnerability or breaks an invariant | Runner runs metric command before the code is in a testable state | Runner stops self-correction after 1 attempt (budget is 3) when the approach was close to working |
| **Sentinel** | Verification | Sentinel does not check a critical acceptance criterion | Sentinel approves code that violates a convention not on its checklist | Sentinel verifies before drift-detector has completed its analysis | Sentinel issues correction after only checking 1 of 5 criteria, missing the remaining 4 |
| **Oracle** | Test audit | Oracle does not audit tests for a proven bead (skipped) | Oracle approves vacuous tests that pass but prove nothing | Oracle audits before the runner's test suite has been fully written | Oracle stops after Layer 1 (static) without running Layer 2 (runtime) |
| **AQS Red** | Attack | Red team does not attack a relevant domain | Red team attacks code that is out of bead scope, producing irrelevant findings | Red team attacks before blue team's code is in final state | Red team stops probing after first finding, missing deeper vulnerabilities |
| **AQS Blue** | Defense | Blue team does not respond to a valid finding | Blue team "fixes" a finding by suppressing the symptom rather than the cause | Blue team response arrives after arbiter has already ruled on the dispute | Blue team marks finding as "disputed" without providing rebuttal evidence |
| **Arbiter** | Verdict | Arbiter does not rule on a disputed finding (deadlock) | Arbiter issues a ruling based on precedent that no longer applies | Verdict issued before the test designed in Step 3 has been executed | Arbiter stops after one inconclusive round without running the permitted follow-up |

### Process Model Flaws (the deepest failure mode)

In STAMP, the most dangerous failures occur when a controller's **process model** diverges from reality. In the SDLC-OS:

| Controller | Process Model Contains | Flaw: Model Diverges When... |
|---|---|---|
| **Conductor** | Task requirements, bead statuses, quality budget, convention map | The convention map is stale (project has evolved since last normalize). The quality budget uses SLI readings from tasks with different characteristics. |
| **Sentinel** | Bead acceptance criteria, convention checklist | The acceptance criteria were written by the Conductor based on a flawed understanding of the requirement. The convention checklist does not cover patterns introduced by recent beads. |
| **Oracle** | VORP standard, what constitutes a "meaningful" test | The definition of "meaningful" has not been updated for new testing patterns. Tests that were vacuous for one framework are appropriate for another. |
| **AQS Red** | Domain attack libraries, scaling heuristics | Attack libraries do not cover emerging vulnerability classes. The heuristic for domain selection is anchored to historical patterns that no longer reflect the codebase's risk profile. |
| **Arbiter** | Precedent database, arbitration protocol | Precedents were established under different codebase conditions. The arbitration protocol's fairness criteria do not account for asymmetric information between red and blue teams. |

## 3.3 Failure Modes Leveson Predicts That the System Does Not Currently Catch

**1. Inter-controller process model inconsistency.** The Conductor, Sentinel, Oracle, and AQS all maintain separate process models of the controlled process (the codebase). There is no mechanism to verify that these models are consistent. The Conductor might believe a bead is "Clear" while the Oracle's understanding of the test landscape would classify it as "Complicated." The Sentinel might accept a convention that the drift-detector would flag. These inconsistencies are latent hazards.

**2. Feedback channel degradation.** Leveson emphasizes that feedback is the critical link between the controlled process and the controller. In the SDLC-OS, feedback flows through specific channels (metric commands, verification checklists, AQS reports). If a feedback channel degrades -- for example, if the metric command produces misleading results (tests pass but coverage is low) or the drift-detector's semantic search index is stale -- the controller acts on incorrect feedback and issues inappropriate control actions. No mechanism monitors the *health of feedback channels themselves*.

**3. Control action gaps at bead boundaries.** When the Conductor decomposes a task into beads, interactions between beads fall into a control gap. Bead A might produce output that Bead B depends on, but neither bead's acceptance criteria verify the correctness of the interface. The Sentinel checks each bead independently. The Oracle audits each bead's tests independently. No controller is responsible for the *interactions* between beads.

**4. Safety constraint violations vs. safety requirement violations.** The current system checks requirements (does the bead meet its acceptance criteria?) but does not enforce constraints (does the bead violate any system-level invariants?). A bead can satisfy all its requirements and still violate a constraint -- for example, a bead that correctly implements a feature but introduces a state where two beads' outputs conflict when composed.

**5. Actuator failure.** In STAMP, an actuator is the mechanism that executes a control action. In the SDLC-OS, the primary actuators are the agent dispatch mechanisms (subagent tool, guppy swarm). If the actuator fails -- for example, an agent dispatch silently drops context, or a guppy receives a truncated directive -- the controller believes it has acted but the action was not executed. No mechanism verifies that dispatched agents actually received and understood their full directives.

## 3.4 Concrete Embedding Mechanisms

**Mechanism L1: STPA-Informed Bead Decomposition (extends Conductor Phase 3)**

During Phase 3 (Architect), after initial bead decomposition, the Conductor performs a lightweight STPA analysis:

```
## STPA Check: Task {id} Bead Decomposition
For each state transition or control action in the task:
1. Which bead owns this control action?
2. Are there control actions that span bead boundaries? → Flag as integration risk
3. For each control action, enumerate UCAs:
   - What if this action is not taken? → Is there a bead that tests the negative case?
   - What if this action is taken incorrectly? → Is there a bead that validates the action?
   - What if this action is mistimed? → Is there a bead that tests sequencing?
4. For each UCA, identify which defensive layer (L1/L2/L2.5) will catch it
5. UCAs with no defensive layer → create additional acceptance criteria or additional beads
```

**Mechanism L2: Process Model Consistency Check (new periodic check)**

Every 5th task (aligned with L6 calibration cadence), verify that the process models of different controllers are consistent:

```
## Process Model Consistency Audit
1. Ask the Sentinel: "What are the current conventions for {domain}?"
2. Ask the drift-detector: "What patterns exist in {domain}?"
3. Compare: do they agree on naming, structure, patterns?
4. Ask the Oracle: "What constitutes a meaningful test for {domain}?"
5. Ask the AQS red team: "What are the primary attack vectors for {domain}?"
6. Compare: do the red team's attack vectors align with the Oracle's test criteria?
Inconsistencies → flag to Conductor for model synchronization
```

**Mechanism L3: Feedback Channel Health Monitor (extends quality SLOs)**

Add feedback channel health as a new SLI category:

```
## Feedback Channel Health
| Channel | From | To | Health Check | Status |
|---|---|---|---|---|
| Metric command | Controlled process | Runner (L0) | Does the metric command cover >80% of bead acceptance criteria? | {OK/DEGRADED} |
| Sentinel checklist | Sentinel DB | Sentinel | Does the checklist include categories for findings from the last 5 tasks? | {OK/DEGRADED} |
| Drift-detector index | Pinecone | Drift-detector | Is the semantic search index less than 3 tasks old? | {OK/DEGRADED} |
| AQS attack library | Attack DB | Red team | Do attack vectors cover vulnerability classes from the last 3 CVE reports relevant to the stack? | {OK/DEGRADED} |
| Convention map | Project docs | All agents | Was the convention map updated within the last 3 tasks? | {OK/DEGRADED} |
```

**Mechanism L4: Bead Boundary Integration Constraints (extends bead format)**

Every bead that produces or consumes output from another bead gains an `## Integration Constraints` section:

```
## Integration Constraints
| Constraint | Verified By | Verification Timing |
|---|---|---|
| This bead's output must be compatible with Bead B's input schema | Phase 5 integration test | After both beads reach merged |
| This bead must not modify state that Bead C reads | Drift-detector cross-bead check | After this bead's L1 cycle |
| The combined state after this bead and Bead D must satisfy invariant X | Conductor during Phase 5 Synthesize | After all beads merged |
```

**Mechanism L5: Safety Constraints Registry (new reference file)**

Distinct from the Code Constitution (which captures reusable *principles*), a Safety Constraints Registry captures *invariants* that must never be violated:

```
## Safety Constraints Registry
| ID | Constraint | Scope | Verification Method | Last Verified |
|---|---|---|---|---|
| SC-001 | No bead may introduce a state where two concurrent operations can corrupt shared data | All beads touching shared state | Fitness function: check for unprotected concurrent access patterns | Task 12 |
| SC-002 | Authentication checks must not be split across bead boundaries | All beads touching auth | STPA bead boundary analysis | Task 10 |
| SC-003 | Error handling must not swallow exceptions that would be visible to the user | All beads | Oracle test audit: check for empty catch blocks | Task 11 |
```

## 3.5 How Leveson Complements Reason and Dekker

**What Leveson catches that Reason misses:** Reason's model assumes that accidents require component failures -- the "holes" in the Swiss cheese are failures. Leveson demonstrates that accidents can occur with zero component failures, purely through unsafe interactions between functioning components. In the SDLC-OS, every agent can work correctly in isolation and the result can still be defective because the *interactions* between agents are unsafe. Leveson provides the framework for analyzing these interaction hazards.

**What Leveson catches that Dekker misses:** Dekker explains that drift is the result of locally rational decisions, but he does not provide a systematic method for *identifying which decisions are unsafe before the accident*. Leveson's STPA provides exactly this: a systematic enumeration of unsafe control actions and their causal scenarios, performed *before* the system is deployed. In the SDLC-OS, STPA-informed bead decomposition identifies integration risks and control gaps during Phase 3, before any runner is dispatched.

**What Leveson misses that the others catch:** Leveson's model assumes that the control structure can be fully described and analyzed. In practice, the actual control structure is more complex than any model of it (Dekker's point) and includes latent conditions that are invisible to analysis (Reason's point). Leveson provides the engineering framework; the others provide the organizational and cognitive wisdom to know where the framework will be incomplete.

---

# Part IV: The Unified Safety Architecture

## 4.1 What Each Framework Catches That the Others Miss

```
                    ┌──────────────────────────────────┐
                    │         THE TRIFECTA              │
                    │                                    │
    ┌───────────────┤  Reason: WHERE are the holes?     │
    │               │  Dekker: WHY are they growing?     │
    │               │  Leveson: WHAT controls are missing?│
    │               └──────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     COVERAGE MATRIX                              │
├──────────────────────┬─────────┬─────────┬─────────────────────┤
│ Failure Mode         │ Reason  │ Dekker  │ Leveson             │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Component failure    │ YES     │ partial │ YES (but reframed   │
│                      │         │         │  as control failure) │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Emergent interaction │ NO      │ partial │ YES                 │
│ failure              │ (linear)│ (drift) │ (systematic)        │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Latent conditions    │ YES     │ YES     │ YES (process model  │
│                      │ (named) │ (why)   │  inconsistency)     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Organizational drift │ partial │ YES     │ partial             │
│                      │ (prod   │ (full   │ (control structure  │
│                      │  vs     │  model) │  degradation)       │
│                      │  prot)  │         │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Classification of    │ YES     │ NO      │ NO                  │
│ error types (GEMS)   │ (skill/ │         │                     │
│                      │  rule/  │         │                     │
│                      │  know)  │         │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Social dynamics of   │ partial │ YES     │ NO                  │
│ safety erosion       │ (culture│ (full   │                     │
│                      │  model) │  model) │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Proactive hazard     │ NO      │ NO      │ YES (STPA)          │
│ identification       │(reactive│(descript│                     │
│                      │  model) │  -ive)  │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Accountability       │ partial │ YES     │ NO                  │
│ framework            │(just    │(just    │                     │
│                      │ culture)│ culture │                     │
│                      │         │  full)  │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Studying success     │ NO      │ YES     │ NO                  │
│ (Safety-II)          │         │(Safety  │                     │
│                      │         │  -II)   │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Feedback channel     │ NO      │ NO      │ YES (core of STAMP) │
│ analysis             │         │         │                     │
├──────────────────────┼─────────┼─────────┼─────────────────────┤
│ Cross-boundary       │ NO      │ NO      │ YES (UCA at         │
│ interaction hazards  │         │         │  controller          │
│                      │         │         │  interfaces)         │
└──────────────────────┴─────────┴─────────┴─────────────────────┘
```

## 4.2 The Integrated Safety Architecture for SDLC-OS

The three frameworks map to three complementary safety functions that should operate continuously:

### Function 1: Defense Integrity Monitoring (Reason)

**Purpose:** Continuously verify that each defensive layer (L0-L6) is effective at catching the defect categories it is responsible for.

**Operates:** During L6 calibration and continuously via the Resident Pathogen Registry.

**Core questions:**
- Which layers have been penetrated recently? (Layer hole tracking)
- What defect categories are accumulating resident pathogens? (Cross-task pattern)
- Is the production/protection balance drifting? (Error budget trajectory)
- Does the system have a functioning safety culture? (Reporting, learning, just culture indicators)

**New artifacts:**
- Resident Pathogen Registry (R2)
- Protection Erosion Monitor (R3)
- Latent Condition Trace on every AQS finding (R1)

### Function 2: Drift Surveillance (Dekker)

**Purpose:** Detect when the system's actual behavior is diverging from its designed behavior, before the divergence causes an accident.

**Operates:** Continuously via deviance normalization indicators; periodically via work-as-done audits.

**Core questions:**
- Is the Conductor normalizing reduced scrutiny? (Cynefin classification drift)
- Are defensive checks becoming ritualistic? (Verification depth scoring)
- Are precedents locking the system into suboptimal trajectories? (Precedent review protocol)
- What does the system do well, and is it reinforcing those behaviors? (Safety-II success library)

**New artifacts:**
- Deviance Normalization Monitor (D1)
- Verification Depth Assessment in LOSA (D2)
- Precedent Sunset Protocol (D3)
- Work-as-Done Audit (D4)
- Safety-II Success Library (D5)

### Function 3: Control Structure Analysis (Leveson)

**Purpose:** Proactively identify unsafe control actions and interaction hazards before they manifest as defects.

**Operates:** During Phase 3 (STPA-informed decomposition); periodically via process model consistency checks.

**Core questions:**
- Are there control actions that span bead boundaries? (Integration risk)
- Are controllers' process models consistent with each other? (Model sync)
- Are feedback channels delivering accurate, timely information? (Channel health)
- What safety constraints must the system never violate? (Constraints registry)
- For each control action, what are the four types of UCA? (Systematic enumeration)

**New artifacts:**
- STPA Check during bead decomposition (L1)
- Process Model Consistency Audit (L2)
- Feedback Channel Health Monitor (L3)
- Bead Boundary Integration Constraints (L4)
- Safety Constraints Registry (L5)

## 4.3 Integration Points: Where the Three Functions Interact

The three functions are not independent; they feed each other:

```
Defense Integrity (Reason)
    │
    │ "L1 has been penetrated 3 times by temporal coupling violations"
    │
    ├──► Drift Surveillance (Dekker)
    │    "Is this because the drift-detector checklist is stale (drift)
    │     or because temporal coupling is inherently hard (system)?"
    │
    └──► Control Structure Analysis (Leveson)
         "Is there a feedback channel that should be delivering temporal
          coupling information to the Sentinel? If so, is it healthy?"
```

```
Drift Surveillance (Dekker)
    │
    │ "Conductor is classifying 20% more beads as Clear than baseline"
    │
    ├──► Defense Integrity (Reason)
    │    "Has this caused holes in downstream layers? Check L2.5 skip
    │     rate and finding rate for beads that were classified Clear."
    │
    └──► Control Structure Analysis (Leveson)
         "Is the Conductor's process model of bead complexity consistent
          with the Oracle's and AQS's? Run a process model consistency check."
```

```
Control Structure Analysis (Leveson)
    │
    │ "Bead A and Bead B have an integration constraint that no layer verifies"
    │
    ├──► Defense Integrity (Reason)
    │    "Which layer SHOULD verify this? Add it to that layer's checklist.
    │     Track as a newly identified latent condition."
    │
    └──► Drift Surveillance (Dekker)
         "How long has this gap existed? Was it present from the start
          (design flaw) or did it emerge through drift (was it once verified
          but the verification was dropped)?"
```

## 4.4 The Unified Loop-Level Safety Map

| Loop Level | Reason Function | Dekker Function | Leveson Function |
|---|---|---|---|
| **L0: Runner** | GEMS error classification: is this a slip (metric catches it), rule mistake (wrong pattern), or knowledge failure (novel problem)? | Local rationality: the runner's "mistakes" make sense given its prompt and context. Fix the context, not the runner. | UCA analysis: what if the runner does not act? Acts incorrectly? Acts at wrong time? |
| **L1: Sentinel** | Defense layer hole tracking: what categories does L1 miss? | Verification depth: is the Sentinel substantive or ritualistic? | Process model check: is the Sentinel's convention model consistent with actual conventions? |
| **L2: Oracle** | Defense layer hole tracking: what test deficiency types does L2 miss? | VORP ritualism: is the Oracle checking VORP because it is meaningful or because it is the checklist? | Feedback health: are the Oracle's test quality signals accurate and timely? |
| **L2.5: AQS** | Defense layer hole tracking: what attack categories does red team miss? | Decrementalism: is "acceptable residual risk" drifting upward? | UCA at bead boundaries: do red team probes cover cross-bead interactions? |
| **L3-L4: Bead/Phase** | Latent condition trace: where did the defect enter the pipeline? | Normalization of deviance: are beads getting larger? Is scrutiny decreasing? | STPA decomposition: are bead boundaries safe? Are integration constraints explicit? |
| **L5: Task** | Production vs. protection: is the Conductor prioritizing throughput over quality? | Path dependency: are early decisions locking the task into suboptimal trajectories? | System-level constraints: does the completed task violate any invariants? |
| **L6: Calibration** | Resident pathogen registry: which pathogens are accumulating? | Deviance normalization monitor: are drift indicators trending? | Process model consistency: are controllers' models synchronized? |

## 4.5 Implementation Priority

The mechanisms from all three frameworks, ordered by impact and implementation difficulty:

| Priority | Mechanism | Framework | Implementation Effort | Impact |
|---|---|---|---|---|
| 1 | Latent Condition Trace on AQS findings (R1) | Reason | Low (extends existing report format) | High (enables upstream layer patching) |
| 2 | Deviance Normalization Monitor (D1) | Dekker | Low (new metrics in calibration protocol) | High (catches process drift before accident) |
| 3 | STPA Check during bead decomposition (L1) | Leveson | Medium (new step in Phase 3) | High (catches integration hazards proactively) |
| 4 | Safety Constraints Registry (L5) | Leveson | Low (new reference file) | High (makes invariants explicit and verifiable) |
| 5 | Feedback Channel Health Monitor (L3) | Leveson | Medium (new SLI category) | High (catches feedback degradation) |
| 6 | Resident Pathogen Registry (R2) | Reason | Low (new reference file with cross-task tracking) | Medium (catches accumulating layer holes) |
| 7 | Bead Boundary Integration Constraints (L4) | Leveson | Medium (extends bead format) | Medium (prevents cross-bead interaction failures) |
| 8 | Verification Depth Assessment (D2) | Dekker | Low (extends LOSA report) | Medium (detects ritualistic compliance) |
| 9 | Safety-II Success Library (D5) | Dekker | Low (extends LOSA report) | Medium (enables positive reinforcement) |
| 10 | Protection Erosion Monitor (R3) | Reason | Low (extends calibration protocol) | Medium (catches production/protection imbalance) |
| 11 | Just Culture Mapping for agents (R4) | Reason | Medium (new classification system) | Medium (improves correction strategies) |
| 12 | Precedent Sunset Protocol (D3) | Dekker | Low (extends precedent system) | Medium (prevents path lock-in) |
| 13 | Process Model Consistency Audit (L2) | Leveson | High (requires cross-controller comparison) | Medium (catches model divergence) |
| 14 | Work-as-Done Audit (D4) | Dekker | Medium (new periodic check) | Medium (catches procedural drift) |

---

## Sources

### Sidney Dekker
- [Drift Into Failure notes - Engineering Ideas Substack](https://engineeringideas.substack.com/p/drift-into-failure-by-sidney-dekker)
- [Drift Into Failure notes - Lorin Hochstein on GitHub](https://github.com/lorin/booknotes/blob/master/Drift-Into-Failure.md)
- [Rasmussen and Practical Drift - Risk Engineering](https://risk-engineering.org/concept/Rasmussen-practical-drift)
- [Just Culture - Sidney Dekker official site](https://sidneydekker.com/just-culture)
- [Just Culture summary - Mind the Risk](https://www.mindtherisk.com/literature/18-just-culture-by-sidney-dekker-a-summary)
- [Just Culture three behaviors - NewWin](https://newwin.ch/en/blog/understanding-just-culture-the-three-behaviors-and-the-system-view-foundation-for-effective-patient-safety-and-successful-error-management-part-2/)
- [Field Guide to Understanding Human Error - Routledge](https://www.routledge.com/The-Field-Guide-to-Understanding-Human-Error/Dekker/p/book/9781472439055)
- [Sidney Dekker - Safety Differently](https://sidneydekker.com/)
- [Safety-II professionals - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0951832018309864)

### James Reason
- [Swiss Cheese Model - Wikipedia](https://en.wikipedia.org/wiki/Swiss_cheese_model)
- [Swiss Cheese Model - Psych Safety](https://psychsafety.com/the-swiss-cheese-model/)
- [Swiss Cheese Model comprehensive review - ResearchGate](https://www.researchgate.net/publication/374471149_A_comprehensive_review_of_the_Swiss_cheese_model_in_risk_management)
- [GEMS - SKYbrary](https://skybrary.aero/articles/generic-error-modelling-system-gems)
- [Skill, Rule, Knowledge classification - Human Reliability](https://mail.humanreliability.com/articles/Understanding%20Human%20Behaviour%20and%20Error.pdf)
- [Human Error overview - UC Berkeley](http://roc.cs.berkeley.edu/294fall01/slides/human-error.pdf)
- [Remembering James Reason - IOSH](https://www.ioshmagazine.com/2025/02/21/remembering-james-reason-household-name-human-error)
- [Safety Culture five components - ResearchGate](https://www.researchgate.net/figure/Components-of-safety-culture-based-on-Professor-James-Reasons-A-roadmap-to-a-just_fig1_341338807)
- [Building a Safety Culture: Informed Culture - ASQS](https://asqs.net/blog/safety-culture-components-informed-culture/)
- [Just Culture - Wikipedia](https://en.wikipedia.org/wiki/Just_culture)

### Nancy Leveson
- [Introduction to STAMP - Functional Safety Engineer](https://functionalsafetyengineer.com/introduction-to-stamp/)
- [STAMP, STPA, and CAST overview - UL SIS](https://www.ul.com/sis/blog/introduction-to-stamp-stpa-and-cast)
- [STPA Handbook - Leveson & Thomas (2018)](http://www.flighttestsafety.org/images/STPA_Handbook.pdf)
- [A New Accident Model for Engineering Safer Systems - Leveson](http://sunnyday.mit.edu/accidents/safetyscience-single.pdf)
- [CAST Handbook - Leveson](http://sunnyday.mit.edu/CAST-Handbook.pdf)
- [STAMP applied to AI risks - Medium](https://medium.com/@eayvali/systems-theoretic-process-analysis-uncovering-systemic-ai-risks-6d99ed3de9f7)
- [Tools to understand complexity - Leveson/STAMP - Medium](https://medium.com/10x-curiosity/tools-to-understand-and-manage-complexity-nancy-leveson-and-stamp-f224b0002df9)
- [Applying STAMP in Accident Analysis - NASA](https://shemesh.larc.nasa.gov/iria03/p13-leveson.pdf)

### Synthesis / Comparative
- [Safety III: A Systems Approach - Leveson (MIT)](http://sunnyday.mit.edu/safety-3.pdf)
- [Leveson and Dekker on Reason - ANU Open Research](https://openresearch-repository.anu.edu.au/server/api/core/bitstreams/a78e8201-7615-4d57-aa95-dade4c7b3b91/content)
- [Swiss Cheese Model and its Critics - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0925753520300576)
- [STAMP scoping review - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0925753521004082)
