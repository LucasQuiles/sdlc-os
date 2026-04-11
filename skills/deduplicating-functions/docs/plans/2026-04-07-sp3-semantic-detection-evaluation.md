# SP3: Semantic Detection + Evaluation Harness

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Program Dependency Graph (PDG) based Type 4 semantic clone detection, Code2Vec-lite embeddings, and a BigCloneBench-style evaluation harness with synthetic test corpus — completing research-grade coverage of all 4 clone types with measurable precision/recall.

**Architecture:** `detect-pdg-semantic.py` builds control-flow + def-use graphs per function via Python `ast`, hashes k-hop neighborhoods for subgraph comparison. `detect-code-embedding.py` builds bag-of-AST-paths vectors (Code2Vec-lite, no GPU) for embedding similarity. `evaluate.py` runs precision/recall/F1 evaluation against a synthetic corpus of known clone pairs at each type. `generate-corpus.py` creates the synthetic evaluation corpus with ground truth.

**Tech Stack:** Python 3.12, `ast` (PDG), `collections` (embeddings), `json` (evaluation), existing `lib/`

**Working directory:** `/home/q/LAB/skills/finding-duplicate-functions`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/detect-pdg-semantic.py` | Create | PDG-based semantic clone detection (Type 4) |
| `scripts/detect-code-embedding.py` | Create | Code2Vec-lite AST path embeddings |
| `scripts/evaluate.py` | Create | Precision/recall/F1 evaluation harness |
| `scripts/generate-corpus.py` | Create | Synthetic test corpus with ground truth |
| `scripts/merge-signals.py` | Modify | Add 2 new strategy weights |
| `scripts/orchestrate.sh` | Modify | Wire 2 new detectors, add --evaluate flag |
| `tests/test_pdg.py` | Create | Tests for PDG detector |
| `tests/test_embedding.py` | Create | Tests for embedding detector |
| `tests/test_evaluation.py` | Create | Tests for evaluation harness |
| `tests/fixtures/eval-corpus.json` | Create | Small synthetic corpus for tests |

---

### Task 1: Build PDG-Based Semantic Detector

**Files:**
- Create: `scripts/detect-pdg-semantic.py`
- Create: `tests/test_pdg.py`

The PDG detector builds lightweight control-flow + data-flow graphs from Python AST and compares via subgraph hashing.

Algorithm:
1. Parse function body into AST
2. Build control flow: sequence of statement types with branching structure
3. Build def-use chains: for each variable, track where it's defined and used
4. Hash k-hop neighborhoods (k=2) around each statement node
5. Compare functions by Jaccard on their sets of neighborhood hashes
6. Functions with same data-flow patterns but different syntax score high

Key functions:
- `build_cfg_nodes(func_ast) -> list[CFGNode]`: Control flow graph nodes
- `build_def_use_chains(func_ast) -> dict[str, list[tuple]]`: Variable def-use chains  
- `hash_neighborhood(node, k=2) -> int`: Hash k-hop neighborhood
- `compute_pdg_fingerprint(func) -> set[int]`: Set of neighborhood hashes
- `detect_pdg_duplicates(catalog, threshold=0.4) -> list[dict]`
- `main()`: CLI with `--threshold`, `-o`

For functions without raw source (only token_sequence), use the token sequence to approximate control flow by extracting statement-boundary tokens.

Output: `{"strategy": "pdg_semantic", "scores": {"pdg_jaccard": N}, "final_score": N, ...}`

Tests should cover:
- Two functions with same logic different variable names → high score
- Two functions with completely different logic → low score
- Function with reordered independent statements → moderate score
- Empty/trivial functions handled gracefully
- Output format correct

---

### Task 2: Build Code2Vec-Lite Embedding Detector

**Files:**
- Create: `scripts/detect-code-embedding.py`
- Create: `tests/test_embedding.py`

Code2Vec-lite: extract AST paths (leaf-to-leaf through common ancestor), build bag-of-paths vectors, compare via cosine similarity. No GPU or training required — pure structural embedding.

Algorithm:
1. For each function, get token_sequence (AST node types)
2. Extract "paths": subsequences of length 3-5 from token sequence (simulating leaf-ancestor-leaf)
3. Build Counter of path patterns (this is the "embedding")
4. Compare embeddings via cosine similarity

Key functions:
- `extract_ast_paths(token_sequence, min_len=3, max_len=5) -> list[tuple]`
- `build_embedding(func) -> Counter[tuple]`: Bag-of-paths embedding
- `embedding_cosine(a: Counter, b: Counter) -> float`
- `detect_embedding_duplicates(catalog, threshold=0.5) -> list[dict]`
- `main()`: CLI with `--threshold`, `-o`

Output: `{"strategy": "code_embedding", "scores": {"path_cosine": N}, "final_score": N, ...}`

Tests: identical functions=1.0, disjoint=0.0, partial overlap intermediate, empty handled, output format.

---

### Task 3: Build Synthetic Corpus Generator + Evaluation Harness

**Files:**
- Create: `scripts/generate-corpus.py`
- Create: `scripts/evaluate.py`
- Create: `tests/test_evaluation.py`
- Create: `tests/fixtures/eval-corpus.json`

The corpus generator creates synthetic function pairs at each clone type with ground truth labels. The evaluator runs the full pipeline against the corpus and computes precision/recall/F1 per clone type.

#### generate-corpus.py
Generates a JSON file with functions and ground truth clone pairs:
```json
{
  "functions": [...],
  "ground_truth": [
    {"func_a": "...", "func_b": "...", "clone_type": 1, "is_clone": true},
    {"func_a": "...", "func_b": "...", "clone_type": null, "is_clone": false}
  ]
}
```

Synthetic generation strategies:
- Type 1: Copy function, change whitespace/comments only
- Type 2: Copy function, rename all variables systematically
- Type 3: Copy function, add/remove 1-2 statements
- Type 4: Write functionally equivalent code with different structure (imperative vs functional, loop vs recursion)
- Non-clones: Randomly pair unrelated functions

CLI: `./generate-corpus.py -o corpus.json [--num-pairs 50] [--seed 42]`

#### evaluate.py
Takes pipeline output + ground truth, computes metrics:
- Per-clone-type: precision, recall, F1
- Overall: precision, recall, F1
- Confusion matrix: TP, FP, TN, FN per type

CLI: `./evaluate.py --results merged-results.json --corpus corpus.json [-o eval-report.json]`

Output: JSON report + human-readable summary to stderr.

#### tests/fixtures/eval-corpus.json
Small (10 functions, 15 ground truth pairs) fixture for unit tests.

Tests: evaluator correctly computes P/R/F1 for perfect results, for all-wrong results, for partial results. Generator produces valid corpus. Fixture is valid.

---

### Task 4: Wire PDG + Embedding Into Pipeline

**Files:**
- Modify: `scripts/merge-signals.py`
- Modify: `scripts/orchestrate.sh`

Add to STRATEGY_WEIGHTS:
```python
"pdg_semantic": 0.80,     # PDG subgraph similarity — strong Type 4 signal
"code_embedding": 0.72,   # Code2Vec-lite AST path embeddings
```

Add to orchestrate.sh phase_detect after LSH block, before the wait loop.

Renumber LLM step.

---

### Task 5: Integration Test + Evaluation Run

Run full pipeline on bricklab/hooks, verify all 11 strategies active, run evaluation against generated corpus, report P/R/F1 per clone type.

Steps:
1. Generate corpus: `python3 scripts/generate-corpus.py -o /tmp/eval-corpus.json --seed 42`
2. Run pipeline on corpus functions: extract from corpus, detect, merge
3. Evaluate: `python3 scripts/evaluate.py --results merged.json --corpus /tmp/eval-corpus.json`
4. Run full pipeline on bricklab/hooks, verify 11 strategies in merge
5. Run ALL tests
