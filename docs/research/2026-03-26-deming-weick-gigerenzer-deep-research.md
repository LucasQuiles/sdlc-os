# Deep Research: Deming, Weick, Gigerenzer
## Foundational Frameworks for Multi-Agent SDLC Quality, Reliability, and Decision Architecture

Date: 2026-03-26

---

# PART I: W. EDWARDS DEMING -- Complete System of Profound Knowledge

Sources: "Out of the Crisis" (1986), "The New Economics" (1993)

## 1. System of Profound Knowledge (SoPK)

Deming's meta-framework. The four components are inseparable -- they interact and must be viewed together as a single lens on organizational reality.

### 1A. Appreciation for a System

A system is a network of interdependent components that work together to accomplish an aim. Action in one part has effects in other parts -- often "unintended consequences." You cannot optimize the whole by optimizing each part independently; local optimization destroys global optimization.

**Multi-agent SDLC mapping:** The Conductor, specialist agents, AQS pipeline, calibration protocol, and quality budget are a *system*. Optimizing one agent's prompt in isolation can degrade the whole. The Conductor must manage the system's aim, not individual agent "performance." The system includes the user, the codebase, and the feedback loops connecting them -- not just the agents.

### 1B. Knowledge of Variation

Everything measured consists of both "normal" variation (common cause, inherent to the system, ~85% of problems) and "special cause" variation (attributable to specific assignable factors, ~15%). The most costly management mistake is reacting to common cause variation as though it were special cause -- Deming called this **tampering**. The inverse mistake (failing to detect a special cause) also exists but is less common. Control charts are the primary tool for distinguishing the two.

**Common cause variation:** Inherent to the system. Can only be reduced by redesigning the system itself (prompts, rubrics, temperature settings, tool chains). Examples: normal variation in LLM outputs, token-sampling randomness, model capability boundaries.

**Special cause variation:** External assignable cause. Find and address the specific thing that changed. Examples: a model API change, a corrupted context window, a malformed tool response, a dependency breaking.

**Multi-agent SDLC mapping:** The noise audit must classify every deviation as common-cause or special-cause *before* taking corrective action. If noise is common-cause (inherent LLM sampling), you fix the *system* (prompts, rubrics, temperature). If it is special-cause (one agent consistently off due to a specific factor), you fix that factor. Control-chart logic should gate all recalibration decisions -- only sustained, statistically verified drift warrants intervention. Single-point anomalies are not actionable.

### 1C. Theory of Knowledge

"How do you know what you know?" Management in any form requires prediction, and prediction must be based on theory. "A statement, if it conveys knowledge, predicts future outcome, with risk of being wrong, and it fits without failure observations of the past." Knowledge comes from theory -- without theory, there is nothing to revise. The PDSA cycle (below) is the mechanism for building knowledge.

**Multi-agent SDLC mapping:** Every system change (prompt edit, rubric adjustment, workflow restructuring) must be framed as a testable prediction: "We predict that changing X will produce outcome Y, measurable by Z." Without this, you cannot learn from outcomes -- you can only react. The calibration protocol's planted-defect beads are theory tests. The precedent system accumulates knowledge only if precedents carry the *theory* behind them (why this pattern works), not just the pattern itself.

### 1D. Psychology

Understanding people, their interactions, and what motivates them. Deming rejected Taylorism and extrinsic motivation. People are born with intrinsic motivation, curiosity, dignity, and joy in learning. Management systems that rely on extrinsic motivation (rankings, merit ratings, numerical targets) destroy intrinsic motivation. "Innovation comes from people who take joy in their work."

**Multi-agent SDLC mapping:** Agents do not have psychology in Deming's sense, but the *humans interacting with the system* do. The system must not create fear in developers -- fear of the system overriding their judgment, fear of quality gates blocking legitimate work, fear of being "caught" by audits. The system should feel like a collaborator, not a surveillance apparatus. Prompt design for agents should also consider the user's emotional response to agent outputs -- agents that explain their reasoning invite trust; agents that deliver verdicts invite fear.

---

## 2. The 14 Points for Management

Each point with its multi-agent SDLC mapping:

**Point 1: Create constancy of purpose toward improvement.**
Mapping: The system needs a declared, stable aim that persists across sessions, tasks, and agent invocations. The Code Constitution serves this role. Constancy of purpose means the Constitution does not change reactively from task to task -- it evolves through deliberate PDSA cycles at L6.

**Point 2: Adopt the new philosophy.**
Mapping: The shift from "inspect quality in" to "build quality in" must be the system's operating philosophy. Quality is not a phase (the AQS check); quality is the entire workflow design.

**Point 3: Cease dependence on inspection to achieve quality.**
Mapping: The AQS pipeline should not be the primary quality mechanism. Quality must be built into the *process* -- clear specifications (Phase 2), correct decomposition (Phase 3), precise operational definitions in rubrics, well-designed prompts. AQS becomes a *verification* of an already-good process, not a *filter* that catches bad work. If AQS is routinely catching defects, the system is broken upstream.

**Point 4: End the practice of awarding business on price tag alone.**
Mapping: Do not select agent models solely on cost/speed. Select for total system cost including rework, debugging, and trust erosion. A cheaper model that produces more rework is more expensive than a more capable model that gets it right.

**Point 5: Improve constantly and forever.**
Mapping: Every L6 calibration cycle, every noise audit, every retrospective is an improvement opportunity. Improvement is not a project; it is the permanent state. The PDSA cycle (below) is the mechanism.

**Point 6: Institute training on the job.**
Mapping: Agent prompts are "training." They must be continuously refined based on observed outcomes, not written once and forgotten. New agents must be onboarded with calibration beads before entering production work.

**Point 7: Institute leadership.**
Mapping: The Conductor is a leader, not a supervisor. The Conductor's job is to help agents succeed -- providing clear context, removing barriers, ensuring the right information reaches the right agent at the right time. Not to rank, rate, or punish agents.

**Point 8: Drive out fear.**
Mapping: Agents that fear "punishment" (prompt degradation, removal from workflow) for honest error reporting will hide errors. The system must structurally separate error detection from error punishment. The AQS blue team's structural independence partially implements this. The system should explicitly reward agents that surface uncertainty ("I am not confident in this section because...") rather than penalizing them.

**Point 9: Break down barriers between departments.**
Mapping: Agent silos are barriers. The architect, implementer, reviewer, and synthesizer must share context, not throw artifacts over walls. Phase transitions must carry full context, not just outputs. The "memory" layer and bead metadata serve this role -- they must be rich enough that downstream agents understand *why*, not just *what*.

**Point 10: Eliminate slogans, exhortations, and targets for the workforce.**
Mapping: Do not put "produce zero defects" or "be maximally thorough" in agent prompts. These are slogans. Instead, give agents operational definitions (below), clear rubrics, and well-structured inputs. "Be careful" is a slogan. "Check every function call against the type signature in the interface definition" is an operational instruction.

**Point 11: Eliminate numerical quotas and management by objective.**
Mapping: Do not measure agents by "number of issues found" or "lines of code reviewed per minute." These metrics incentivize gaming. Measure system outcomes: does the code work? Is it maintainable? Did the user's intent get realized?

**Point 12: Remove barriers to pride of workmanship.**
Mapping: Give agents sufficient context, clear instructions, and adequate computational resources. An agent forced to work with truncated context, ambiguous instructions, or insufficient tool access cannot take "pride" in its output and will produce poor work regardless of its capability.

**Point 13: Institute a vigorous program of education and self-improvement.**
Mapping: The system must learn. Precedents, calibration results, retrospective findings, and noise audit trends must feed forward into improved prompts, rubrics, and workflows. L6 calibration is the primary learning mechanism.

**Point 14: Put everybody to work on the transformation.**
Mapping: Quality is not the AQS team's job. Every agent in the pipeline -- planner, architect, implementer, reviewer, synthesizer -- is responsible for quality. The system design must make this structural, not aspirational.

---

## 3. PDSA Cycle (Plan-Do-Study-Act)

Deming insisted on PDSA, not PDCA. "Check" asks "Did it work?" (binary). "Study" asks "What did we learn?" (analytical). The difference is fundamental.

**Plan:** Establish the objective and the theory. What change are we testing? What do we predict will happen? How will we measure?

**Do:** Carry out the plan on a small scale. Collect data.

**Study:** Analyze the results. Compare to predictions. What did we learn? Was the theory confirmed, modified, or refuted?

**Act:** Adopt the change if it worked, abandon it if it didn't, or run another cycle with a modified theory.

**Multi-agent SDLC mapping:** Every system change -- prompt edit, rubric adjustment, workflow restructuring, new agent introduction -- should follow PDSA:
- **Plan:** "We predict that adding explicit type-checking instructions to the implementer prompt will reduce type errors by 40%, measurable via AQS domain scores over the next 10 beads."
- **Do:** Deploy the change for a bounded trial (10 beads).
- **Study:** After 10 beads, compare actual type error rates to prediction. What explains the gap? Did the change have unintended effects on other quality domains?
- **Act:** If confirmed, make permanent. If not, revert and theorize differently.

This maps to the L6 calibration cycle. Currently L6 fires every 5th task -- it should explicitly frame each cycle as a PDSA iteration with a recorded theory, prediction, and study conclusion.

---

## 4. The Red Bead Experiment

Setup: A bowl contains 3,200 white beads and 800 red beads (20% red). Workers use a paddle with 50 holes to scoop beads. Red beads are "defects." Workers are instructed to produce zero defects. Supervisors rank workers, praise the best, counsel the worst, and eventually fire the "underperformers."

Lesson: The defect rate is determined by the system (the ratio of red to white beads), not by the workers. No amount of effort, exhortation, or ranking will change the outcome. The only way to reduce defects is to change the system (remove red beads from the bowl).

**Multi-agent SDLC mapping:** If agent A consistently produces outputs with ~15% issues and agent B produces ~12%, the difference may be common-cause variation in the system, not a meaningful difference in agent quality. "Firing" agent A or "rewarding" agent B is tampering. The Conductor must ask: what is the system-level defect rate? Is it stable? If stable, the only way to improve is to change the system (prompts, context, tools, decomposition quality). Control charts applied to agent performance over time reveal whether differences are signal or noise.

---

## 5. The Funnel Experiment and Four Rules of Tampering

Setup: A marble is dropped through a funnel onto paper with a target. The goal is to land the marble as close to the target as possible.

**Rule 1 -- Leave the funnel fixed over the target.** Do not adjust. This produces the smallest variation around the target. This is the correct approach for a stable process.

**Rule 2 -- Compensate: move the funnel opposite to the last error.** If the marble landed 2 units left of target, move the funnel 2 units right. This produces ~40% more variation than Rule 1. This is the most common management mistake -- reacting to every outcome.

**Rule 3 -- Reset to last result: reposition the funnel over where the last marble landed.** This produces a random walk -- the process drifts without bound.

**Rule 4 -- Set to target from last result: always adjust based on the previous position.** This also produces drift without bound, diverging explosively.

**Multi-agent SDLC mapping:**
- **Rule 1 (correct):** If the noise audit shows a stable process, *do not adjust prompts, rubrics, or workflow*. Leave the system alone. The urge to "tweak" after every imperfect outcome is Rule 2 tampering.
- **Rule 2 (common mistake):** "The last bead had a type error, so let's add 'pay extra attention to types' to the implementer prompt." This is compensating for a single data point and will increase variation.
- **Rule 3 (drift):** "Let's base the next task's approach on whatever worked last time." This is chasing the last outcome and produces random drift.
- **Rule 4 (explosion):** Cascading adjustments where each change is relative to the previous change, not to a stable reference point.

The system needs a **tampering detector**: if the Conductor is changing prompts or workflows more frequently than control-chart evidence supports, the system should flag this as potential tampering.

---

## 6. Operational Definitions

An operational definition puts communicable meaning into a concept. It consists of three components:

1. **A specific test** of material or assembly
2. **A criterion** for judgment
3. **A decision:** yes or no, the object did or did not meet the criterion

Without operational definitions, words like "good," "reliable," "clean," "fast," "safe" have no communicable meaning. Deming's famous seminar question: "How many people are in this room?" -- the answer depends entirely on the operational definition (for fire safety? for seating? including people in the hallway?).

**Multi-agent SDLC mapping:** Every AQS rubric item must be an operational definition. Not "Is the code clean?" but:
- **Test:** Run the linter with configuration X on the changed files.
- **Criterion:** Zero warnings at severity level "error" or above.
- **Decision:** Pass/fail.

Not "Is the architecture sound?" but:
- **Test:** Verify that no module imports from a module in a different bounded context without going through the declared public API.
- **Criterion:** Zero cross-boundary direct imports.
- **Decision:** Pass/fail.

Every quality domain in the AQS must be decomposed into operational definitions. If a domain cannot be operationally defined, it cannot be reliably measured, and the AQS is performing theater, not quality assurance.

---

## 7. "A Bad System Beats a Good Person Every Time"

Deming's core insight: 85% of problems are system-caused, not worker-caused. "Put a good person in a bad system and the bad system wins, no contest." The focus must be on system design, not individual performance.

**Multi-agent SDLC mapping:** The most capable model (GPT-4, Claude Opus, etc.) in a badly designed workflow will produce poor results. A well-designed workflow with a less capable model will often outperform. System design -- decomposition strategy, context management, prompt architecture, feedback loops, quality gates -- matters more than raw model capability. Investment should flow to system design, not to "upgrading the model."

---

## 8. Joy in Work / Intrinsic Motivation

"Innovation comes from people who take joy in their work." "We must preserve the power of intrinsic motivation, dignity, cooperation, curiosity, joy in learning, that people are born with." Extrinsic motivation (bonuses, rankings, fear of punishment) gradually destroys intrinsic motivation.

**Multi-agent SDLC mapping (human side):** The system must not make developers feel surveilled, judged, or overridden. Quality gates should feel like a safety net, not a gauntlet. The system should explain *why* it flagged something, invite dialogue, and defer to human judgment when the human has context the system lacks. The experience should produce confidence, not anxiety.

---

---

# PART II: KARL WEICK -- Complete HRO and Sensemaking Framework

Sources: "Managing the Unexpected" (2001/2015, with Kathleen Sutcliffe), "Sensemaking in Organizations" (1995), "The Social Psychology of Organizing" (1979)

## 1. Five Principles of High Reliability Organizations (HROs)

HROs operate in high-risk environments (nuclear power, aircraft carriers, emergency medicine) where failure has catastrophic consequences. Despite this, they achieve extraordinary safety records. Weick and Sutcliffe identified five principles, which taken together produce **organizational mindfulness**.

### 1A. Preoccupation with Failure

HROs treat every failure -- no matter how minor -- as a symptom of a potentially larger problem. They encourage the reporting of near-misses, anomalies, and deviations. They do not explain away small problems; they investigate them. "Looking for early heralds of failure" is not pessimism but vigilance.

At the organizational level: leadership actively seeks "bad news" as a positive indicator. Environments where staff can report problems without fear of being accused of disloyalty. When problems surface, solutions spread organization-wide, building "common language and grammar."

**Multi-agent SDLC mapping:** The system must treat every anomaly -- unexpected test failure, unusual output pattern, context window overflow, tool timeout -- as a signal worth investigating, not as noise to be suppressed. Near-misses (AQS scores that barely pass, ambiguous results that could have gone either way) should be logged and analyzed with the same rigor as actual failures. The premortem step (Phase 4.5, Step 0) embodies this principle. The system should maintain a **near-miss registry** alongside the defect log.

### 1B. Reluctance to Simplify

HROs resist easy explanations and simple categories. They conduct root cause analysis rather than accepting the first plausible explanation. They acknowledge inherent complexity and challenge assumptions about root causes.

**Multi-agent SDLC mapping:** When a bead fails AQS, the system must resist "the implementer got it wrong" as the explanation. Was the specification ambiguous? Was the decomposition poorly scoped? Was the context insufficient? Was the rubric unreasonable? The quality retrospective (L5) must systematically consider multiple causal hypotheses, not jump to the simplest one. The Cynefin classification (already in the system) supports this -- complex and chaotic domains require multiple hypotheses by definition.

### 1C. Sensitivity to Operations

HROs understand that the best picture of current conditions comes from the front line, not from dashboards or reports. Systems are dynamic and nonlinear. Leaders practice "Management by Walking Around" -- genuine engagement, not symbolic presence.

**Multi-agent SDLC mapping:** The Conductor must maintain real-time awareness of what is actually happening in the current bead, not just what the plan says should be happening. Agent outputs, intermediate artifacts, tool responses, and error messages are the "front line." The Conductor should monitor leading indicators during execution (partial outputs, tool call patterns, error rates) rather than waiting for the final artifact to judge quality. This maps to L0 (real-time monitoring within a single agent invocation).

### 1D. Commitment to Resilience

Resilience is not just preventing failure; it is the ability to recover, improvise, and adapt when unexpected things happen. HROs build the capacity to anticipate trouble spots and improvise solutions in real time. This involves cross-functional collaboration, institutional memory, and training for managing crises.

**Multi-agent SDLC mapping:** The system must have graceful degradation paths. If the primary implementation approach fails, there must be fallback strategies. If an agent produces unusable output, the system should be able to reroute, retry with different parameters, or escalate to a human -- not just fail. The bead retry logic and the Conductor's ability to re-scope mid-execution embody this. The system should also maintain a **playbook** of previously successful recovery strategies, indexed by failure type.

### 1E. Deference to Expertise

Decisions migrate to the person with the most relevant expertise, regardless of rank or authority. In a crisis, the most knowledgeable person leads, not the most senior person.

**Multi-agent SDLC mapping:** Different agents have different strengths. The system should route decisions to the agent with the most relevant capability, not to a fixed hierarchy. If a bead involves complex database migration, the Conductor should weight the database-specialized agent's assessment more heavily, even if the "default" reviewer has a different opinion. More importantly: when a human developer has domain expertise that exceeds any agent's capability, the system must defer to the human, not insist on its own assessment.

---

## 2. Seven Properties of Sensemaking

Sensemaking is "the process through which people give meaning to experience." It is distinct from decision-making: decision-making assumes a defined problem and seeks a solution; sensemaking asks "what is the problem?" and "what is going on here?"

### 2A. Grounded in Identity Construction

"Who people think they are in their context shapes what they enact and how they interpret events." Sensemaking begins with the sensemaker -- their role, their identity, their position shapes what they notice and how they interpret it.

**Mapping:** Each agent has an identity defined by its system prompt. This identity determines what the agent notices and how it interprets inputs. A "security reviewer" agent will see the same code differently than a "performance optimizer" agent. Identity is not a bias to be eliminated; it is a necessary frame. The system should deliberately construct diverse identities to get diverse sensemaking.

### 2B. Retrospective

Sensemaking is retrospective -- we make sense of what has already happened. "We can only know what we have done after we have done it." The timing of retrospection matters: immediate retrospection captures different things than delayed retrospection.

**Mapping:** The Phase 5 Synthesize step is the primary sensemaking moment. The system makes sense of what was built, what worked, what didn't. The L5 retrospective is delayed retrospection. Both are necessary -- immediate and delayed -- because they capture different signals.

### 2C. Enactive of Environments

"People enact the environments they face." Agents do not passively observe an objective environment; they partly create the environment through their actions and interpretations. "Managers construct, rearrange, single out, and demolish many 'objective' features of their surroundings."

**Mapping:** When the architect agent decomposes a task into beads, it is *enacting* the problem space -- creating the structure that downstream agents will then work within. The decomposition is not a neutral representation of "the problem"; it is a construction that shapes what solutions are possible. The system must recognize that early-phase agents create the environment for later-phase agents. Poor enactment upstream propagates.

### 2D. Social

Sensemaking is a social activity. "Plausible stories are preserved, retained or shared." It happens in interaction, not in isolation. The audience includes the speaker.

**Mapping:** Multi-agent collaboration is inherently social sensemaking. When agents exchange artifacts, they are engaged in collaborative sensemaking. The quality of this sensemaking depends on the quality of the interaction -- rich context transfer enables better sensemaking than thin artifact handoffs.

### 2E. Ongoing

Sensemaking never stops. "Reality is an ongoing accomplishment that emerges from efforts to create order and make retrospective sense." It is not an event; it is a continuous process.

**Mapping:** The system must not treat sensemaking as a phase. Understanding evolves throughout execution. The Conductor should continuously update its understanding of the task, the codebase, and the user's intent -- not "lock in" understanding at Phase 2 and execute blindly.

### 2F. Focused on and by Extracted Cues

People extract specific cues from the environment and use them as seeds for developing a larger sense. "Simple, familiar structures that are seeds from which people develop a larger sense." What counts as a cue depends on context.

**Mapping:** Agents extract cues from code, tests, error messages, user instructions, and prior artifacts. The system should be intentional about which cues are surfaced to which agents. The Conductor's context management is cue extraction -- deciding what information to foreground and what to background for each agent invocation.

### 2G. Driven by Plausibility Rather Than Accuracy

"People favor plausible accounts over accurate ones." In equivocal situations, an obsession with accuracy is "fruitless and not of much practical help." People need a good-enough story that enables action, not a perfect representation.

**Mapping:** Agents should produce plausible, actionable outputs rather than exhaustively accurate ones. A code review that identifies the three most important issues is more useful than one that catalogs every minor deviation. The system should optimize for *actionability* (plausible stories that enable good next actions), not for *completeness* (exhaustive accuracy).

---

## 3. Enactment Theory

Weick's deepest insight: organizations do not simply *react* to their environments; they *enact* (create) their environments and then respond to their own creations.

"Enactment is to organizing as variation is to natural selection." The process has two steps:
1. **Preconceptions select portions of the field for attention.**
2. **People act within those portions in ways that reinforce the preconceptions.**

The environment is not "out there" waiting to be discovered. It is partly constructed by the agent's own actions and interpretations. An enacted environment is "a map of if-then assertions in which actions are related to outcomes."

**Multi-agent SDLC mapping:** When Phase 2 (Clarify) interprets the user's request, it is enacting an environment. When Phase 3 (Architect) decomposes the task, it is enacting a problem structure. These enactments then constrain all downstream work. The system must recognize that upstream enactments are *hypotheses about the environment*, not *descriptions of the environment*. They should be treated as revisable.

This has a direct implication for error: if the Phase 2 interpretation is wrong, everything downstream works in an enacted environment that does not match reality. The system needs mechanisms to detect enacted-environment mismatch -- moments where downstream agents encounter signals that contradict the upstream enactment.

---

## 4. Loose Coupling vs. Tight Coupling

Weick defines loose coupling through five criteria. Components are loosely coupled when one affects another: (1) suddenly rather than continuously, (2) occasionally rather than constantly, (3) negligibly rather than significantly, (4) indirectly rather than directly, (5) eventually rather than immediately.

**Advantages of loose coupling:**
- **Persistence:** Sub-system breakdown does not damage the entire organization
- **Buffering:** Localized crises don't cascade
- **Adaptability:** Units adapt to local contexts independently
- **Inventiveness:** Delayed feedback allows creative problem-solving
- **Psychological safety:** Reduced surveillance intensity

**Disadvantages of loose coupling:**
- Difficult to systematically change
- Slow response times
- Limited direct control
- Goals and procedures don't reliably predict behavior

Weick advocates "ambivalence as the optimal compromise" -- balancing tight coupling of core elements (values, goals) with loose coupling of operational processes.

**Multi-agent SDLC mapping:** The system should be **tightly coupled on principles** (the Code Constitution, quality standards, operational definitions) and **loosely coupled on execution** (individual agent invocations, specific implementation approaches, tool selection). This means:
- The Code Constitution is tightly coupled: all agents follow it, always, immediately.
- The bead execution is loosely coupled: failure of one bead does not cascade to others. Each bead is semi-autonomous. The Conductor can adapt the approach for each bead independently.
- The AQS is moderately coupled: it verifies consistency with tight-coupled principles but does not tightly control execution methods.

---

## 5. Requisite Variety

From Ashby's Law (adopted by Weick): "Only variety can absorb variety." A system's response repertoire must match the complexity of its environment. If the environment has more variety than the system can handle, the system will be overwhelmed.

**Multi-agent SDLC mapping:** The system's repertoire of agent capabilities, tool integrations, workflow patterns, and recovery strategies must match the variety of tasks it encounters. A system with only one implementation agent and one review strategy lacks requisite variety for diverse codebases. The agent catalog, tool library, and Conductor's strategy selection together constitute the system's variety. When a task falls outside existing variety, the system must recognize this and escalate rather than force-fit.

---

## 6. Collapse of Sensemaking (Mann Gulch Disaster)

Weick's analysis of the 1949 Mann Gulch fire that killed 13 smokejumpers. The disaster was produced by the "interrelated collapse of sensemaking and structure." A **cosmology episode** occurs when people "suddenly and deeply feel that the universe is no longer a rational, orderly system" -- when both the sense of what is occurring and the means to rebuild that sense collapse together.

The firefighters encountered behavior that contradicted their expectations. When crew leader Dodge lit an escape fire and ordered tool abandonment, the crew could not make sense of these actions and refused to comply. The organization disintegrated because:
- Role structure collapsed (the crew lost its organizing frame)
- Sensemaking collapsed (members could not understand what was happening)
- These collapses were mutually reinforcing

**Four sources of resilience that forestall disintegration:**
1. **Improvisation and bricolage:** Creative adaptation with available resources (Dodge's escape fire)
2. **Virtual role systems:** Mentally simulating others' roles reduces dependency on any single individual
3. **Attitude of wisdom:** Combining confident action with doubt about one's understanding
4. **Respectful interaction:** Group cohesion through genuine communication (the two survivors stayed together)

**Multi-agent SDLC mapping:** System-level sensemaking collapse occurs when:
- The Conductor encounters a situation that contradicts all its expectations
- Simultaneously, the structural mechanisms for recovery (fallback strategies, escalation paths) are unavailable or unknown
- The system enters a state of "cosmological confusion" -- it cannot determine what is happening or what to do

Prevention requires:
- Maintaining diverse interpretive frames (multiple agents with different perspectives)
- Preserving structural scaffolding even under stress (not abandoning the workflow framework when things go wrong)
- Building in the four resilience sources: improvisation capability, virtual role understanding (agents that can reason about other agents' roles), wisdom (calibrated confidence), and rich inter-agent communication.

---

---

# PART III: GERD GIGERENZER -- Complete Ecological Rationality Framework

Sources: "Simple Heuristics That Make Us Smart" (1999), "Risk Savvy" (2014), "Gut Feelings" (2007)

## 1. The Adaptive Toolbox

The adaptive toolbox is "the stock of strategies available to the organism." Rather than a single general-purpose decision mechanism, the mind contains multiple specialized heuristics. The key is selecting the right heuristic for the right environment. Three selection principles: memory constraints, feedback/reinforcement, and environmental structure.

**Multi-agent SDLC mapping:** The system should maintain a repertoire of decision strategies, not a single "always optimize" approach. Different task types call for different heuristics:
- Simple, well-defined tasks: fast-and-frugal routing (minimal analysis, direct execution)
- Complex, ambiguous tasks: full deliberative pipeline (multi-phase, multi-agent)
- Uncertain, novel tasks: recognition-based routing (match to nearest known pattern)

The Conductor's strategy selection *is* the adaptive toolbox. The richer the toolbox, the more environments the system can handle effectively.

---

## 2. Core Heuristics

### 2A. Take The Best (TTB)

A lexicographic heuristic for paired comparisons:
1. **Search:** Look up cues in order of validity (most valid first)
2. **Stop:** Stop at the first cue that discriminates between the two options
3. **Decide:** Choose the option favored by that cue

TTB searches on average 2.4 cues (out of 7.7 available) and yet achieves higher predictive accuracy than multiple regression across 20 studies. Against neural networks and complex algorithms, TTB outperforms when proper cross-validation is applied.

**When TTB excels:** High dispersion of cue validities (some cues are much more informative than others). Scarce information. Small sample sizes.

**Multi-agent SDLC mapping:** When the Conductor must choose between two implementation approaches, it should not weigh all factors equally. Instead:
1. Order decision factors by validity (track record of predictive success): Does it match a known pattern? Does it align with the codebase's existing architecture? Does the user have a stated preference?
2. Stop at the first factor that discriminates.
3. Choose.

This is dramatically faster than exhaustive multi-criteria analysis and, for many routine decisions, more accurate because it avoids overfitting to noise in low-validity cues.

### 2B. Tallying (Equal-Weight Counting)

Count the number of positive cues for each alternative. Choose the one with the most positive cues. All cues are weighted equally -- no optimization of weights.

Tallying achieved higher predictive accuracy than multiple regression on average across datasets, because regression overfits when estimating weights from limited data.

**When tallying excels:** Cue validities vary little (no single dominant cue). Low redundancy among cues. Limited training data.

**Multi-agent SDLC mapping:** When multiple AQS quality domains are assessed, tallying is the appropriate aggregation strategy. Rather than trying to weight "correctness" at 0.35 and "maintainability" at 0.25 and "security" at 0.20 (which requires calibration data that may not exist), simply count how many domains pass. This is more robust, more transparent, and less susceptible to weight-gaming.

### 2C. Recognition Heuristic

"If one of two objects is recognized and the other is not, infer that the recognized object has the higher value." Operates when recognition validity > 0.5.

Gigerenzer demonstrated that semi-ignorant people (who recognized some tennis players but not all) predicted Wimbledon outcomes as accurately as the ATP Rankings and better than fully informed experts. Systematic forgetting can be beneficial -- a less-is-more effect.

**Multi-agent SDLC mapping:** When the system encounters a new task, the first question should be: "Do we recognize this pattern?" If the precedent system contains a matching pattern, use it. If the task is entirely novel (not recognized), route it through the full deliberative pipeline. The recognition heuristic provides a fast first-pass triage that avoids unnecessary deliberation for familiar tasks.

### 2D. 1/N Equality Rule

Allocate resources equally across N alternatives. Even Harry Markowitz, Nobel laureate for portfolio theory, used 1/N for his own retirement investments.

Testing across 7 investment problems, 1/N "ranked first (out of 15) on certainty equivalent returns" -- outperforming all optimization-based strategies.

**When 1/N excels:** High uncertainty. Many alternatives. Limited predictive information. When the cost of estimating optimal weights exceeds the benefit.

**Multi-agent SDLC mapping:** When allocating effort across quality domains (correctness, maintainability, security, performance, accessibility), default to equal allocation unless strong evidence supports differential weighting. This prevents the system from over-investing in one domain at the expense of others based on noisy or insufficient calibration data.

---

## 3. Fast-and-Frugal Decision Trees

A fast-and-frugal tree (FFT) has m+1 exits with one exit for each of the first m-1 cues and two exits for the last cue. At each node, one answer leads to an exit (triggering a decision) and the other leads to the next question.

**Structure:**
```
Cue 1: Does condition A hold?
  YES --> Exit: Decision X (stop here)
  NO  --> Continue to Cue 2

Cue 2: Does condition B hold?
  YES --> Continue to Cue 3
  NO  --> Exit: Decision Y (stop here)

Cue 3: Does condition C hold?
  YES --> Exit: Decision X
  NO  --> Exit: Decision Y
```

**Key properties:**
- Binary cue structure: one cue, one threshold, one exit per level
- Transparency: every step is auditable and explainable
- Speed: maximum m questions for m cues (usually far fewer)
- Robustness: competitive with logistic regression, CART, random forests, naive Bayes
- Particularly strong with small samples (< 80 observations)

**The coronary care unit example:** A three-cue FFT for triaging heart attack patients:
1. Is there an ST-segment change in the ECG? YES --> coronary care unit (high risk). NO --> continue.
2. Is chest pain the chief complaint? YES --> continue. NO --> regular nursing bed (low risk).
3. Are any of five other factors present? YES --> coronary care unit. NO --> regular nursing bed.

This three-cue tree predicted heart attacks more accurately than a complex logistic regression system and physicians' clinical judgment.

**Multi-agent SDLC mapping:** The Conductor's routing decisions should be structured as FFTs:

```
Task Routing FFT:
1. Does the task match a known precedent with >90% confidence?
   YES --> Execute from precedent (L1 fast path). STOP.
   NO  --> Continue.

2. Does the task involve more than 3 files or cross module boundaries?
   YES --> Continue to full decomposition (Phase 3).
   NO  --> Single-bead execution. STOP.

3. Does the task involve security-critical or data-integrity code?
   YES --> Full pipeline with enhanced AQS. STOP.
   NO  --> Standard pipeline. STOP.
```

Every routing decision in the system can be expressed as an FFT. The advantages are enormous:
- **Transparency:** The user can see exactly why the system chose a particular workflow
- **Auditability:** Every decision is logged as a sequence of binary cue evaluations
- **Robustness:** FFTs are resistant to overfitting, which matters when the system has limited calibration data
- **Speed:** Routing decisions are near-instantaneous

---

## 4. Ecological Rationality

"The rationality of a decision depends on the circumstances in which it takes place." No heuristic is universally superior. A heuristic is "smart" in a specific environment, not universally.

The key question is not "Is this heuristic rational?" but "In what environment does this heuristic perform well, and in what environment does it fail?"

**Conditions favoring simple heuristics (like TTB, tallying, FFTs):**
- High uncertainty (unknown probabilities, unstable distributions)
- Small sample sizes (limited training data)
- High number of cues relative to observations
- Noisy data
- Need for transparency and explainability

**Conditions favoring complex models (like regression, neural nets):**
- Known risk (stable, calculable probabilities)
- Large sample sizes (abundant training data)
- Few cues relative to observations
- Low noise
- Accuracy matters more than transparency

**Multi-agent SDLC mapping:** The SDLC operates mostly under *uncertainty*, not *risk*. Probabilities of defect types, optimal decomposition strategies, and quality-effort tradeoffs are not known with precision. They change with every codebase, every task type, every model update. This means the system is in Gigerenzer's "heuristic zone" -- simple, transparent, robust strategies will generally outperform complex optimization. The system should resist the temptation to build complex scoring models, weighted rubrics, and multi-factor optimization when simple heuristics (FFTs, tallying, recognition) will do as well or better.

---

## 5. Risk vs. Uncertainty

From "Risk Savvy": Gigerenzer uses "risk" for situations where "all alternatives, consequences, and probabilities are known." "Uncertainty" is when "some of these are unknown." Most real-world decisions involve uncertainty, not risk.

"With risk, all you need is calculation. With uncertainty, calculation may help you to some degree, but there is no way to calculate the optimal solution."

**Multi-agent SDLC mapping:** The system must distinguish between:
- **Risk decisions** (known probabilities): "This test suite has a 98% historical pass rate on this type of change." Use calculation.
- **Uncertainty decisions** (unknown probabilities): "We have never seen this type of integration before." Use heuristics.

Most SDLC decisions are uncertainty decisions. The system should not pretend to calculate optimal solutions when probabilities are unknown. Instead, it should use fast-and-frugal heuristics and acknowledge uncertainty explicitly.

---

## 6. Natural Frequencies vs. Conditional Probabilities

Gigerenzer demonstrates that humans (including doctors) systematically misinterpret conditional probabilities but correctly interpret the same information presented as natural frequencies.

Example: "The probability of breast cancer is 1%. If a woman has breast cancer, the probability of a positive mammogram is 90%. If a woman does not have breast cancer, the probability of a positive mammogram is 9%. What is the probability that a woman with a positive mammogram actually has breast cancer?"

Most doctors say 80-90%. The correct answer is ~9%. But reframe in natural frequencies: "10 out of 1,000 women have breast cancer. 9 of those 10 will test positive. 89 of the remaining 990 will also test positive. Of 98 positive tests, 9 actually have cancer." Now the answer is obvious: 9/98 ~ 9%.

**Multi-agent SDLC mapping:** When agents report probabilities, quality scores, or confidence levels, the system should translate these into natural frequencies before presenting to humans. Not "87% confidence this code is correct" but "In 100 similar cases, approximately 87 would be correct and 13 would contain at least one defect." This prevents base-rate neglect and enables better human judgment about whether to accept, review, or reject agent outputs.

---

## 7. The Bias-Variance Tradeoff in Decision-Making

Total prediction error decomposes into: **bias^2 + variance + noise**.

- **Bias:** Systematic error from simplifying assumptions. Simple models have high bias.
- **Variance:** Error from sensitivity to training data fluctuations. Complex models have high variance.
- **Noise:** Irreducible error in the data.

The key insight: "An unbiased algorithm may suffer from high variance," while a biased algorithm that controls variance can achieve superior total accuracy. This is why simple heuristics can outperform complex models -- they trade a small increase in bias for a large decrease in variance.

Three conditions where biased-but-simple wins:
1. **Sparse observations:** Variance dominates when data is limited
2. **High noise:** Simple models are more robust to noise
3. **Many cues:** Complex models overfit when estimating many parameters from limited data

**Multi-agent SDLC mapping:** The system's learning mechanisms (calibration, precedents, noise audits) are inherently limited-sample settings. Complex scoring models that try to estimate many parameters (domain-specific weights, agent-specific biases, task-type-specific thresholds) will overfit. Simple models (tallying, equal weights, FFTs) will generalize better. The system should start simple and only add complexity when there is strong evidence that complexity reduces total error, not just training-set error.

---

## 8. Less-is-More Effects

Situations where less information, less computation, or less knowledge leads to *better* decisions. These are not paradoxes -- they follow directly from the bias-variance tradeoff.

**Examples:**
- Semi-ignorant participants predicted Wimbledon better than experts (recognition heuristic)
- Experienced retail managers using a simple "hiatus heuristic" outpredicted Pareto/NBD models
- 1/N portfolio allocation outperformed optimization with 10 years of training data
- TTB with 2.4 cues outperformed regression with 7.7 cues

**Multi-agent SDLC mapping:** The system should resist the accumulation of complexity. More quality domains, more rubric items, more review passes, more agent perspectives are not always better. There is a point where additional analysis introduces more noise than signal. The system should actively monitor whether adding complexity (more checks, more agents, more review cycles) actually improves outcomes or just increases cost and latency. When in doubt, less is more.

---

---

# PART IV: SYNTHESIS -- Unified Quality-Reliability-Decision Architecture

## What Each Thinker Provides That the Others Cannot

### Deming provides: SYSTEMATIC QUALITY THROUGH VARIATION CONTROL
- The distinction between common-cause and special-cause variation
- The discipline of operational definitions
- The PDSA cycle for building knowledge
- The principle that system design trumps individual capability
- The warning against tampering (adjusting stable processes)

**Without Deming:** The system has no principled basis for deciding when to intervene and when to leave things alone. Every deviation looks like it needs fixing. The system tamperes itself into increasing variation.

### Weick provides: ORGANIZATIONAL RELIABILITY THROUGH MINDFUL OPERATIONS
- The five HRO principles for preventing catastrophic failure
- Sensemaking theory for navigating ambiguity
- Enactment theory (agents create the environments they respond to)
- Loose coupling architecture for resilience
- Understanding of how sensemaking collapses and how to prevent it

**Without Weick:** The system has no framework for operating reliably in ambiguous, novel situations. It can handle routine tasks but is brittle in the face of the unexpected. It does not understand that its own actions shape the environment it is trying to navigate.

### Gigerenzer provides: EFFECTIVE DECISIONS UNDER UNCERTAINTY
- The adaptive toolbox (repertoire of decision strategies)
- Fast-and-frugal trees for transparent, auditable routing
- Ecological rationality (match the strategy to the environment)
- The bias-variance tradeoff (simple beats complex under uncertainty)
- Less-is-more principle (restraint against accumulating complexity)

**Without Gigerenzer:** The system defaults to "more analysis is always better," accumulating complexity that degrades performance. Routing decisions are opaque. The system pretends to optimize when probabilities are unknown. Decision transparency is sacrificed for decision sophistication.

---

## The Integrated Architecture

The three frameworks form a coherent, non-overlapping architecture:

```
                    GIGERENZER
                  (Decision Layer)
              What strategy to use when
              FFTs, adaptive toolbox,
              ecological rationality
                       |
                       v
    DEMING <-----------------------> WEICK
  (Quality Layer)               (Reliability Layer)
  Variation control              Mindful operations
  PDSA learning cycles           Sensemaking under ambiguity
  Operational definitions        HRO principles
  System > individual            Enactment awareness
  Anti-tampering                 Resilience architecture
```

**How they connect:**

1. **Gigerenzer decides how to decide.** The Conductor uses FFTs and ecological rationality to select the appropriate strategy for each task. This is the meta-decision: which workflow, which agents, which level of scrutiny?

2. **Deming governs the stable-state system.** Once a strategy is selected, Deming's framework ensures the process runs with controlled variation, operational definitions, and PDSA-based learning. Control charts detect when the process shifts from stable to unstable.

3. **Weick governs the unstable-state response.** When Deming's control charts signal a process that has gone unstable, or when the system encounters genuinely novel situations, Weick's framework kicks in: sensemaking under ambiguity, HRO principles for preventing catastrophe, loose coupling to prevent cascade, and resilience strategies for recovery.

**The handoff logic:**

```
GIGERENZER FFT: Is this situation familiar?
  |
  YES --> DEMING: Run the standard process.
  |       Monitor with control charts.
  |       Is the process stable?
  |         YES --> Continue. PDSA for improvement.
  |         NO  --> Special cause?
  |                  YES --> Find and fix the cause.
  |                  NO  --> WEICK: We are in unfamiliar territory.
  |
  NO --> WEICK: Activate sensemaking.
         Apply HRO principles.
         Defer to expertise.
         Resist simplification.
         |
         Resolution reached?
           YES --> DEMING: Incorporate learning.
           |       Update precedents.
           |       New PDSA cycle.
           NO  --> Escalate to human.
                   Preserve structure.
                   Prevent cosmology episode.
```

---

## Concrete Integration Points by SDLC Phase

### Phase 1 (Receive Task)
- **Gigerenzer:** Recognition heuristic -- does the system recognize this task type? FFT routing to appropriate workflow.
- **Weick:** Extract cues from the task description. What is ambiguous? What requires sensemaking?
- **Deming:** Is the task specification operationally defined? If not, clarify before proceeding.

### Phase 2 (Clarify / Understand)
- **Weick:** Sensemaking process. The agent is *enacting* an interpretation of the user's intent. Treat the interpretation as a revisable hypothesis, not a fact.
- **Gigerenzer:** Use TTB for disambiguation -- what is the single most discriminating cue for interpreting intent?
- **Deming:** Operational definitions -- translate vague requirements into specific, testable criteria.

### Phase 3 (Architect / Decompose)
- **Weick:** Enactment awareness -- the decomposition *creates* the problem space for downstream agents. This is a high-leverage sensemaking moment.
- **Gigerenzer:** FFT for decomposition strategy selection. Ecological rationality -- match decomposition approach to task structure.
- **Deming:** Appreciation for the system -- consider downstream effects of decomposition choices on the entire pipeline.

### Phase 4 (Implement)
- **Deming:** Standard process execution with built-in quality. Operational definitions in coding standards. Eliminate dependence on post-hoc inspection.
- **Weick:** Sensitivity to operations -- the Conductor monitors execution in real time for early signs of trouble.
- **Gigerenzer:** Simple heuristics for implementation decisions. Avoid over-engineering.

### Phase 4.5 (AQS / Quality Assurance)
- **Deming:** This is verification, not the quality mechanism. Operational definitions for every rubric item. Control charts for tracking quality trends. Common-cause vs. special-cause classification for every defect.
- **Weick:** Preoccupation with failure -- near-miss tracking. Reluctance to simplify -- root cause analysis for every failure, not just surface explanations.
- **Gigerenzer:** Tallying for domain aggregation. FFTs for pass/fail decisions. Resist complex scoring models.

### Phase 5 (Synthesize / Retrospect)
- **Weick:** Retrospective sensemaking. What did we learn? What was the enacted environment versus reality?
- **Deming:** PDSA Study phase. Compare predictions to outcomes. Update theory.
- **Gigerenzer:** Less-is-more -- did additional analysis actually improve outcomes, or just add cost?

### L6 (Calibration / System Learning)
- **Deming:** PDSA Act phase. Adopt, abandon, or modify changes based on Study results. Anti-tampering: only adjust if control charts show genuine shift, not common-cause variation.
- **Weick:** Commitment to resilience -- update playbooks, recovery strategies, and fallback paths.
- **Gigerenzer:** Ecological rationality -- has the environment changed? Does the current adaptive toolbox still match the environment, or do we need new heuristics?

---

## Ten Foundational Design Principles (Derived from Synthesis)

1. **System over agents** (Deming): Design the system right; do not rely on agent excellence to compensate for system deficiency.

2. **Classify before acting** (Deming): Distinguish common-cause from special-cause variation before taking corrective action. Tampering is worse than inaction.

3. **Operationally define everything** (Deming): If it cannot be specified with a test, criterion, and decision, it cannot be reliably measured or improved.

4. **Treat interpretations as enactments** (Weick): Early-phase outputs create the environment for later phases. They are hypotheses, not facts.

5. **Maintain organizational mindfulness** (Weick): Preoccupation with failure, reluctance to simplify, sensitivity to operations, commitment to resilience, deference to expertise -- all five, continuously.

6. **Preserve sensemaking capacity under stress** (Weick): When things go wrong, maintain structure, maintain communication, maintain diverse interpretive frames. Prevent cosmology episodes.

7. **Match strategy to environment** (Gigerenzer): Use the adaptive toolbox. Simple heuristics for uncertain environments; complex models only when justified by data richness and stability.

8. **Default to transparency** (Gigerenzer): Use FFTs for routing decisions. Every decision should be auditable, explainable, and reversible.

9. **Resist complexity accumulation** (Gigerenzer): More checks, more agents, more rubric items are not always better. Monitor whether complexity is improving outcomes or just increasing cost. When in doubt, less is more.

10. **Learn through PDSA** (Deming + Weick + Gigerenzer): Every system change is a theory to be tested. Plan the change, execute it, study the results, act on the learning. This is how the system improves constantly and forever.

---

## Sources

### Deming
- [The Deming System of Profound Knowledge (SoPK) -- Deming Institute](https://deming.org/explore/sopk/)
- [Deming's 14 Points for Management -- Deming Institute](https://deming.org/explore/fourteen-points/)
- [The Funnel Experiment -- Deming Institute](https://deming.org/explore/the-funnel-experiment/)
- [Red Bead Experiment -- Deming Institute](https://deming.org/explore/red-bead-experiment/)
- [Knowledge of Variation -- Deming Institute](https://deming.org/knowledge-of-variation/)
- [A Bad System Will Beat a Good Person Every Time -- Deming Institute](https://deming.org/a-bad-system-will-beat-a-good-person-every-time/)
- [The Insanity of Extrinsic Motivation -- Deming Institute](https://deming.org/the-insanity-of-extrinsic-motivation/)
- [Deming's System of Profound Knowledge -- IT Revolution](https://itrevolution.com/articles/demings-system-of-profound-knowledge/)
- [PDSA Cycle -- Deming Institute](https://deming.org/explore/pdsa/)
- [Operational Definitions -- Digestible Deming](https://digestibledeming.substack.com/p/operational-definitions)
- [Common Cause vs Special Cause Variation -- SixSigma.us](https://www.6sigma.us/six-sigma-in-focus/common-cause-vs-special-cause-variation/)
- [PDCA -- Wikipedia](https://en.wikipedia.org/wiki/PDCA)
- [ASQ: Deming's 14 Points](https://asq.org/quality-resources/total-quality-management/deming-points)

### Weick
- [The Five Principles of Weick & Sutcliffe -- High-Reliability.org](https://www.high-reliability.org/the-five-principles-of-weick-sutcliffe)
- [5 Principles of High Reliability Organizations -- KaiNexus](https://blog.kainexus.com/improvement-disciplines/hro/5-principles)
- [Sensemaking -- Wikipedia](https://en.wikipedia.org/wiki/Sensemaking)
- [Karl E. Weick -- Wikipedia](https://en.wikipedia.org/wiki/Karl_E._Weick)
- [Mann Gulch Disaster Analysis -- AcaWiki](https://acawiki.org/The_collapse_of_sensemaking_in_organizations:_The_Mann_Gulch_disaster)
- [Loose Coupling: Rethinking Control in Organizations -- Leading Sapiens](https://www.leadingsapiens.com/loose-coupling/)
- [Weick and Sutcliffe/Social Psychology -- High-Reliability.org](https://www.high-reliability.org/Weick-Sutcliffe)

### Gigerenzer
- [Homo Heuristicus: Less-is-More Effects -- PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3629675/)
- [Fast-and-Frugal Trees -- Wikipedia](https://en.wikipedia.org/wiki/Fast-and-frugal_trees)
- [Ecological Rationality -- Wikipedia](https://en.wikipedia.org/wiki/Ecological_rationality)
- [Ecological Rationality -- Gerd Gigerenzer](https://www.gerd-gigerenzer.com/ecological-rationality)
- [Gerd Gigerenzer -- Wikipedia](https://en.wikipedia.org/wiki/Gerd_Gigerenzer)
- [Risk Savvy: How to Make Good Decisions -- The Key Point](https://thekeypoint.org/2022/06/12/risk-savvy-how-to-make-good-decisions/)
- [Heuristic Decision Making -- Gigerenzer & Gaissmaier](https://economics.northwestern.edu/docs/events/nemmers/2018/gigerenzer2.pdf)
- [Fast-and-Frugal Heuristics -- Broken Science Initiative](https://brokenscience.org/gigerenzer-heuristic/)
- [Simple Heuristics That Make Algorithms Smart -- Behavioral Scientist](https://behavioralscientist.org/simple-heuristics-that-make-algorithms-smart/)
