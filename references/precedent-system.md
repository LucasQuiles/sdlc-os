# Precedent System (Stare Decisis)

The precedent database records reusable rulings from arbiter verdicts. Its purpose is threefold:

1. **Consistency** — Similar issues must receive similar rulings across beads and sessions
2. **Efficiency** — Previously decided issues can be resolved by citation rather than re-litigation
3. **Institutional memory** — The system accumulates judgment over time

---

## How Precedent Works

### For the Arbiter (Step 0 — before dispute contract lock)

Before locking the dispute contract, search this database:

1. **Match criteria:** domain + finding type + core disagreement type
2. **If match found:**
   - **Follow precedent** — Apply the same ruling, cite the prior verdict ID. No test needed. Resolve in the verdict format with: `**Precedent applied:** {verdict-id} — {rule established}`
   - **Distinguish** — If the current case differs materially, state what is different and why the prior ruling doesn't apply. Then proceed with the full Kahneman protocol.
3. **If no match found:** Proceed with the full protocol.

### For the Conductor (Phase 6 — after every arbiter verdict)

After every arbiter verdict, extract the rule and append a precedent entry below. This is mandatory, not optional.

### For the Pretrial Filter (Phase 2.5)

Recon signals matching a DISMISSED precedent on the same code path are precluded from re-litigation (res judicata). Exception: if the code has materially changed since the precedent was established, the preclusion does not apply.

---

## Precedent Decay

Precedents are living guidance, not eternal law:

- **Strong precedent** — Issued within the current project context, code unchanged. Follow unless distinguishable.
- **Weak precedent** — Issued before a major architectural change, or code has been substantially modified. Treat as guidance, not binding.
- **Superseded** — A later verdict on the same finding type reached a different conclusion. The later ruling controls.

---

## Precedent Database

<!-- Entries are appended by the Conductor after each arbiter verdict -->
<!-- Format: one entry per verdict, chronological order -->

_No precedents recorded yet. The database grows through adversarial engagement._
