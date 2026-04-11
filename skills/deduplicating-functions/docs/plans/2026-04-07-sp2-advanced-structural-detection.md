# SP2: Advanced Structural Detection

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three advanced structural detection strategies — Bag-of-AST-Nodes cosine similarity (Type 3, 86% precision), Winnowing fingerprints for partial clone detection, and LSH on AST feature vectors for sub-linear scaling — bringing coverage to BigCloneBench-competitive levels.

**Architecture:** Three new detectors join the existing 6. `detect-bag-of-ast.py` converts functions to sparse AST node-type count vectors and compares via cosine similarity. `detect-winnowing.py` implements the Moss/Winnowing algorithm for positional substring fingerprinting. `detect-lsh-ast.py` uses MinHash locality-sensitive hashing on AST feature vectors for approximate nearest neighbor retrieval. All integrate into the existing merge pipeline with new strategy weights.

**Tech Stack:** Python 3.12, `datasketch` (MinHash/LSH), `math` (cosine), existing `lib/common.py`, `lib/prefilter.py`

**Working directory:** `/home/q/LAB/skills/finding-duplicate-functions`

**Prerequisite:** Install `datasketch`: `pip3 install --break-system-packages datasketch`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/detect-bag-of-ast.py` | Create | Bag-of-AST-nodes cosine similarity detector |
| `scripts/detect-winnowing.py` | Create | Winnowing/fingerprint partial clone detector |
| `scripts/detect-lsh-ast.py` | Create | MinHash LSH approximate nearest neighbor detector |
| `scripts/merge-signals.py` | Modify | Add 3 new strategy weights |
| `scripts/orchestrate.sh` | Modify | Wire 3 new detectors into phase_detect |
| `tests/test_bag_of_ast.py` | Create | Tests for bag-of-AST detector |
| `tests/test_winnowing.py` | Create | Tests for winnowing detector |
| `tests/test_lsh_ast.py` | Create | Tests for LSH detector |

---

### Task 1: Install datasketch and Build Bag-of-AST-Nodes Detector

**Files:**
- Create: `scripts/detect-bag-of-ast.py`
- Create: `tests/test_bag_of_ast.py`

- [ ] **Step 1: Install datasketch**

```bash
pip3 install --break-system-packages datasketch
python3 -c "from datasketch import MinHash; print('datasketch OK')"
```

- [ ] **Step 2: Create `tests/test_bag_of_ast.py`**

The test file should import the module via importlib (hyphenated filename) and test:

1. `ast_node_vector(func)` — converts token_sequence to a Counter of node types
2. `cosine_similarity(vec_a, vec_b)` — computes cosine similarity on sparse vectors
3. `detect_bag_of_ast_duplicates(catalog, threshold)` — full pipeline

Test cases:
- Identical token sequences → cosine = 1.0
- Disjoint token sequences → cosine = 0.0
- Partial overlap → 0 < cosine < 1
- Empty token sequence → handled gracefully (score 0.0)
- Full pipeline finds known duplicates in a synthetic catalog
- Output format has `strategy: "bag_of_ast"`, `func_a`, `func_b`, `final_score`

- [ ] **Step 3: Implement `scripts/detect-bag-of-ast.py`**

Core algorithm:
1. For each function, extract its `token_sequence` (list of AST node type names)
2. Build a `Counter` of node types (bag-of-words on AST nodes)
3. Compute cosine similarity between all pairs (use prefilter to skip impossible pairs)
4. Score = cosine similarity on the node-type count vectors

Key functions:
- `ast_node_vector(func) -> Counter[str]`: Extract token_sequence, count node types
- `cosine_similarity(a: Counter, b: Counter) -> float`: dot(a,b) / (|a| * |b|)
- `detect_bag_of_ast_duplicates(catalog, threshold=0.6) -> list[dict]`
- `main()`: CLI with `--threshold`, `-o`, catalog positional arg

Output format: `{"func_a": func_ref(fa), "func_b": func_ref(fb), "scores": {"cosine": N}, "final_score": N, "strategy": "bag_of_ast"}`

Use `should_compare` from `lib.common` and `should_prefilter_pair` from `lib.prefilter`.

- [ ] **Step 4: Run tests**

```bash
cd /home/q/LAB/skills/finding-duplicate-functions && python3 -m pytest tests/test_bag_of_ast.py -v
```

- [ ] **Step 5: Run ALL tests for regression check**

```bash
python3 -m pytest tests/ -v
```

---

### Task 2: Build Winnowing Fingerprint Detector

**Files:**
- Create: `scripts/detect-winnowing.py`
- Create: `tests/test_winnowing.py`

- [ ] **Step 1: Create `tests/test_winnowing.py`**

Test cases:
1. `kgrams(seq, k)` — generates k-grams from a sequence
2. `winnow(hashes, window_size)` — selects minimum hash from each window (Moss algorithm)
3. `compute_fingerprint(func, k, window)` — produces fingerprint set for a function
4. `fingerprint_similarity(fp_a, fp_b)` — Jaccard on fingerprint sets
5. `detect_winnowing_duplicates(catalog, threshold)` — full pipeline
6. Identical functions → similarity 1.0
7. Completely different functions → similarity ~0.0
8. Partial clone (one function is a subset of another) → high overlap coefficient
9. Output format: `strategy: "winnowing"`

- [ ] **Step 2: Implement `scripts/detect-winnowing.py`**

The Winnowing algorithm (from Moss plagiarism detection):
1. Convert function tokens to k-grams (k=5 default)
2. Hash each k-gram (use Python `hash()` for speed)
3. Slide a window (w=4 default) across hashes, select minimum from each window
4. The selected hashes form the function's "fingerprint"
5. Compare fingerprints between functions using Jaccard similarity
6. Guarantees: any shared substring of length >= k+w-1 tokens will be detected

Key functions:
- `kgrams(seq: list[str], k: int) -> list[tuple[str, ...]]`
- `hash_kgram(kgram: tuple[str, ...]) -> int`: `hash(kgram)`
- `winnow(hashes: list[int], window: int) -> set[int]`: select min per window
- `compute_fingerprint(func: dict, k: int, window: int) -> set[int]`
- `fingerprint_similarity(fp_a: set[int], fp_b: set[int]) -> float`: Jaccard
- `detect_winnowing_duplicates(catalog, threshold=0.4, k=5, window=4) -> list[dict]`
- `main()`: CLI with `--threshold`, `--k`, `--window`, `-o`

Use overlap_coefficient from `lib.common` alongside Jaccard for asymmetric partial clone detection. Final score = max(jaccard, overlap_coefficient) on fingerprint sets.

Output: `{"strategy": "winnowing", "scores": {"jaccard": N, "overlap": N}, "final_score": N, ...}`

- [ ] **Step 3: Run tests**

```bash
python3 -m pytest tests/test_winnowing.py -v
```

- [ ] **Step 4: Run ALL tests**

```bash
python3 -m pytest tests/ -v
```

---

### Task 3: Build LSH on AST Feature Vectors Detector

**Files:**
- Create: `scripts/detect-lsh-ast.py`
- Create: `tests/test_lsh_ast.py`

- [ ] **Step 1: Create `tests/test_lsh_ast.py`**

Test cases:
1. `build_minhash(token_set, num_perm)` — creates MinHash from token set
2. `build_lsh_index(catalog, num_perm, threshold)` — builds LSH index from catalog
3. `query_similar(lsh, minhash, catalog_index)` — retrieves candidates
4. `detect_lsh_duplicates(catalog, threshold, num_perm)` — full pipeline
5. Identical functions should be in same bucket
6. Very different functions should NOT be in same bucket (with high probability)
7. Pipeline finds known duplicates
8. Output format: `strategy: "lsh_ast"`
9. Empty catalog handled gracefully

- [ ] **Step 2: Implement `scripts/detect-lsh-ast.py`**

Uses `datasketch.MinHash` and `datasketch.MinHashLSH`:
1. For each function, extract token_sequence as a set of unique tokens
2. Build a MinHash for each function (num_perm=128)
3. Insert all MinHashes into an LSH index (threshold=0.5)
4. For each function, query the LSH for similar functions
5. Score candidates by exact Jaccard estimation from MinHash

Key functions:
- `build_minhash(token_set: set[str], num_perm: int = 128) -> MinHash`
- `build_lsh_index(catalog, num_perm, threshold) -> tuple[MinHashLSH, list[MinHash]]`
- `detect_lsh_duplicates(catalog, threshold=0.5, num_perm=128) -> list[dict]`
- `main()`: CLI with `--threshold`, `--num-perm`, `-o`

Important: LSH is probabilistic — it retrieves approximate neighbors. Then compute exact Jaccard from MinHash for final scoring.

Output: `{"strategy": "lsh_ast", "scores": {"estimated_jaccard": N}, "final_score": N, ...}`

- [ ] **Step 3: Run tests**

```bash
python3 -m pytest tests/test_lsh_ast.py -v
```

- [ ] **Step 4: Run ALL tests**

```bash
python3 -m pytest tests/ -v
```

---

### Task 4: Wire All Three Detectors Into Pipeline

**Files:**
- Modify: `scripts/merge-signals.py`
- Modify: `scripts/orchestrate.sh`

- [ ] **Step 1: Add strategy weights to merge-signals.py**

In the `STRATEGY_WEIGHTS` dict, add:

```python
"bag_of_ast": 0.70,       # Bag-of-AST-nodes cosine — strong structural signal
"winnowing": 0.65,        # Winnowing fingerprints — partial clone detection
"lsh_ast": 0.70,          # LSH on AST features — approximate but fast
```

- [ ] **Step 2: Add detector phases to orchestrate.sh**

In `phase_detect()`, add after the TF-IDF block:

```bash
    # 1g. Bag-of-AST-nodes cosine
    if [[ -x "$SCRIPT_DIR/detect-bag-of-ast.py" ]]; then
        log "  [1g] Bag-of-AST-nodes cosine..."
        python3 "$SCRIPT_DIR/detect-bag-of-ast.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/bag-of-ast-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1h. Winnowing fingerprints
    if [[ -x "$SCRIPT_DIR/detect-winnowing.py" ]]; then
        log "  [1h] Winnowing fingerprints..."
        python3 "$SCRIPT_DIR/detect-winnowing.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/winnowing-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi

    # 1i. LSH on AST features
    if [[ -x "$SCRIPT_DIR/detect-lsh-ast.py" ]]; then
        log "  [1i] LSH AST features..."
        python3 "$SCRIPT_DIR/detect-lsh-ast.py" "$catalog" \
            -o "$OUTPUT_DIR/detect/lsh-ast-results.json" 2>>"$OUTPUT_DIR/pipeline.log" &
        pids+=($!)
    fi
```

Renumber the LLM step from `[1g]` to `[1j]`.

- [ ] **Step 3: Run full pipeline**

```bash
rm -rf /tmp/sp2-verify && bash scripts/orchestrate.sh /home/q/LAB/bricklab/hooks -o /tmp/sp2-verify --skip-llm 2>&1 | tail -20
```

Verify all 9 strategies appear in merge output.

- [ ] **Step 4: Run ALL tests**

```bash
python3 -m pytest tests/ -v
```

---

### Task 5: Integration Regression Test

- [ ] **Step 1: Run full pipeline on bricklab/hooks**

```bash
rm -rf /tmp/sp2-final && bash scripts/orchestrate.sh /home/q/LAB/bricklab/hooks -o /tmp/sp2-final --skip-llm 2>&1
```

- [ ] **Step 2: Verify merge summary**

```bash
jq '.summary' /tmp/sp2-final/merge/merged-results.json
```

Check:
- `strategies_used` includes all 9 strategies
- `defense_depth_pairs` > 49 (SP1 baseline)
- Known duplicate `generate_action_id` ↔ `generate_enrichment_id` still HIGH

- [ ] **Step 3: Run ALL tests**

```bash
python3 -m pytest tests/ -v
```

All must pass.
