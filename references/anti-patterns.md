# Anti-Patterns Reference

Named anti-patterns that the FFT Decision Architecture guards against. Each FFT explicitly targets one or more anti-patterns. Sourced from the thinkers-lab research index.

---

## Tampering
**Source:** W. Edwards Deming (Funnel Experiment)
**Mechanism:** Reacting to common-cause variation as if it were special-cause, adjusting a stable process in response to normal noise. Every well-intentioned correction compounds the previous error.
**FFT guard:** FFT-06 (AQS Convergence) — Cue 3 invokes Deming Rule 1: stable process, do not adjust.
**Detect it:** Process adjustments after every bad outcome without checking whether the defect was a statistical outlier or a genuine shift.
**What to do instead:** Use control charts. Only intervene when signals appear outside control limits.

## Normalization of Deviance
**Source:** Sidney Dekker (Drift Into Failure)
**Mechanism:** Gradual acceptance of degraded standards because repeated departures from protocol have not yet caused disaster. Each small deviation is rationalized as acceptable.
**FFT guard:** Evolve profile deviance normalization check — trend analysis on Clear classification rate, fast-track rate, scrutiny skip rate.
**Detect it:** "That's just how it works here." Undocumented workarounds everyone knows about. Procedures on paper that aren't followed.
**What to do instead:** Periodically compare current practice against original design standards, not against recent practice. Use fresh eyes.

## Oversimplification
**Source:** Karl Weick (Managing the Unexpected)
**Mechanism:** Premature categorization that closes off further inquiry and channels response down a single track.
**FFT guard:** FFT-02 (Cynefin) forces explicit classification with documented cue traversal. The decision trace makes the classification auditable.
**Detect it:** Issue labeled within minutes without challenge. Investigation stopped at first plausible explanation.
**What to do instead:** Keep multiple hypotheses alive. Seek diverse interpretations before converging.

## Parameter Obsession
**Source:** Donella Meadows (Thinking in Systems)
**Mechanism:** Concentrating change efforts on numerical parameters while leaving underlying structure unchanged. Parameters are the lowest-leverage intervention.
**FFT guard:** FFT-03 (AQS Domains) uses binary activation. FFT-10 (Complexity Source) routes essential vs accidental differently rather than tuning scrutiny levels.
**Detect it:** Third iteration of tuning the same thresholds. Running debate about parameter values for months.
**What to do instead:** Map the leverage hierarchy. Ask: is there a structural change that would make this parameter irrelevant?

## Over-Engineering for Safety
**Source:** Nassim Nicholas Taleb (Antifragile)
**Mechanism:** System so thoroughly insulated from stressors that it loses adaptive capacity. Protection becomes a source of brittleness.
**FFT guard:** FFT-05 (Loop Depth) and FFT-09 (Hardening Skip) allow Clear beads to skip deep verification. Not everything needs maximum scrutiny.
**Detect it:** System has never experienced a failure. All variance designed out. Chaos engineering rejected as "too risky."
**What to do instead:** Apply hormetic stress — controlled, graduated exposure to stressors.

## Analysis Paralysis
**Source:** Gerd Gigerenzer (Risk Savvy)
**Mechanism:** Search for more information exceeds the point of diminishing returns. Complex models overfit to noise in uncertain environments.
**FFT guard:** FFT-01 (Task Profile) and FFT-04 (Phase Config) skip unnecessary phases. Investigate and Repair profiles don't analyze what doesn't need analyzing.
**Detect it:** Meetings end with requests for more data. Deadlines pass while analysis continues.
**What to do instead:** Match decision strategy to environment. Use fast-and-frugal heuristics under uncertainty.

## Narrative Fallacy
**Source:** Nassim Nicholas Taleb (The Black Swan)
**Mechanism:** Constructing post-hoc causal stories that make random or multi-causal events appear inevitable. The story crowds out genuine understanding.
**FFT guard:** FFT-07 (Escalation) checks for systemic patterns (Cue 1: same error 3+ times) before constructing a single-cause narrative.
**Detect it:** Post-incident review produces a linear causal chain ending in a single root cause. Everyone feels the situation is fully understood.
**What to do instead:** Accept that complex failures are multi-causal. Use contributing factor analysis, not root cause analysis.

## Garbage In, Gospel Out
**Source:** John Sterman (Business Dynamics)
**Mechanism:** Model outputs treated as authoritative truth without scrutinizing assumptions and data feeding the model.
**FFT guard:** FFT-08 (Check Routing) routes deterministic questions to deterministic tools. Don't ask an LLM whether types pass — run the type checker.
**Detect it:** Decisions justified by "the model says" without discussing assumptions. Sensitivity analysis absent.
**What to do instead:** Treat model outputs as structured hypotheses. Run sensitivity analysis. Surface boundary conditions.
