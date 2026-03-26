# Bead: B3-enforcer
**Status:** pending
**Type:** implement
**Runner:** unassigned
**Dependencies:** none (convention-dimensions content provided in context)
**Scope:** agents/convention-enforcer.md
**Cynefin domain:** complicated
**Input:** Plan Task 3 content + convention-dimensions.md content (provided by Conductor)
**Output:** Complete agent file at agents/convention-enforcer.md with YAML frontmatter (name, description, model: sonnet) and system prompt covering L1 enforcement, severity classification, Convention Map staleness detection, LSP tooling, output format, relationship to drift-detector. Committed.
**Acceptance:** Frontmatter matches agent pattern. Clearly separates from drift-detector (naming/style vs DRY/SSOT). BLOCKING/WARNING/NOTE severity. Includes CONVENTION_DRIFT signal. Convention Enforcement Report output format with per-dimension scoring.
