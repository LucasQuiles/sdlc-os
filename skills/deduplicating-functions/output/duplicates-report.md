# Duplicate Functions Report

_Multi-Signal Detection with Defense in Depth_

Generated: 2026-08-23 23:13

## Summary

| Metric | Value |
|--------|-------|
| Total duplicate pairs | 11278 |
| HIGH confidence | 3373 |
| MEDIUM confidence | 7866 |
| LOW confidence | 39 |
| Multi-signal pairs (2+) | 4821 |
| Defense depth pairs (3+) | 2018 |
| Detection strategies used | ast_similarity, bag_of_ast, code_embedding, fuzzy_name, lsh_ast, metric_similarity, pdg_semantic, signature_match, tfidf_index, token_clone, winnowing |


### Clone Type Distribution

| Clone Type | Count |
|-----------|-------|
| Type 4 (semantic clone) | 11029 |
| Type 3 (near-miss clone) | 141 |
| Type 2 (renamed clone) | 96 |
| Type 1 (exact clone) | 12 |

### Action Summary

| Action | Count |
|--------|-------|
| INVESTIGATE | 7866 |
| CONSOLIDATE | 3373 |
| REVIEW | 39 |

---

## Actionable Tier

> Type 1 (exact clone) and Type 2 (renamed clone) pairs at HIGH confidence.
> These are the highest-priority consolidation targets.

| Pair | Score | Strategies | File A | File B |
|------|-------|------------|--------|--------|
| `visit_Name` / `visit_Attribute` | 1.0 | 9 | `extract-functions-ast-py.py:54` | `extract-functions-ast-py.py:81` |
| `_unparse_annotation` / `_unparse_default` | 0.985 | 10 | `extract-functions-ast-py.py:168` | `extract-functions-ast-py.py:178` |
| `detect_bag_of_ast_duplicates` / `detect_pdg_duplicates` | 0.984 | 10 | `detect-bag-of-ast.py:87` | `detect-pdg-semantic.py:138` |
| `visit_FunctionDef` / `visit_AsyncFunctionDef` | 0.968 | 10 | `extract-functions-ast-py.py:66` | `extract-functions-ast-py.py:74` |
| `main` / `main` | 0.966 | 11 | `detect-ast-similarity.py:246` | `detect-code-embedding.py:195` |
| `main` / `main` | 0.966 | 11 | `detect-ast-similarity.py:246` | `detect-winnowing.py:259` |
| `main` / `main` | 0.966 | 11 | `detect-bag-of-ast.py:149` | `detect-pdg-semantic.py:203` |
| `main` / `main` | 0.966 | 11 | `detect-bag-of-ast.py:149` | `detect-token-clones.py:210` |
| `main` / `main` | 0.966 | 11 | `detect-code-embedding.py:195` | `detect-winnowing.py:259` |
| `main` / `main` | 0.966 | 11 | `detect-fuzzy-names.py:338` | `detect-signature-match.py:378` |
| `main` / `main` | 0.966 | 11 | `detect-pdg-semantic.py:203` | `detect-token-clones.py:210` |
| `visit_FunctionDef` / `visit_AsyncFunctionDef` | 0.956 | 11 | `extract-functions-ast-py.py:410` | `extract-functions-ast-py.py:417` |
| `main` / `main` | 0.946 | 10 | `detect-ast-similarity.py:246` | `detect-lsh-ast.py:194` |
| `main` / `main` | 0.946 | 10 | `detect-code-embedding.py:195` | `detect-lsh-ast.py:194` |
| `main` / `main` | 0.946 | 10 | `detect-lsh-ast.py:194` | `detect-winnowing.py:259` |
| `main` / `main` | 0.942 | 10 | `detect-bag-of-ast.py:149` | `detect-lsh-ast.py:194` |
| `main` / `main` | 0.942 | 10 | `detect-lsh-ast.py:194` | `detect-pdg-semantic.py:203` |
| `main` / `main` | 0.942 | 10 | `detect-lsh-ast.py:194` | `detect-token-clones.py:210` |
| `main` / `main` | 0.936 | 10 | `detect-ast-similarity.py:246` | `detect-pdg-semantic.py:203` |
| `main` / `main` | 0.936 | 10 | `detect-ast-similarity.py:246` | `detect-token-clones.py:210` |
| `main` / `main` | 0.936 | 10 | `detect-code-embedding.py:195` | `detect-pdg-semantic.py:203` |
| `main` / `main` | 0.936 | 10 | `detect-code-embedding.py:195` | `detect-token-clones.py:210` |
| `main` / `main` | 0.936 | 10 | `detect-pdg-semantic.py:203` | `detect-winnowing.py:259` |
| `main` / `main` | 0.936 | 10 | `detect-token-clones.py:210` | `detect-winnowing.py:259` |
| `main` / `main` | 0.935 | 10 | `detect-ast-similarity.py:246` | `detect-bag-of-ast.py:149` |
| `main` / `main` | 0.935 | 10 | `detect-bag-of-ast.py:149` | `detect-code-embedding.py:195` |
| `main` / `main` | 0.935 | 10 | `detect-bag-of-ast.py:149` | `detect-winnowing.py:259` |
| `get_token_set` / `with_overrides` | 0.934 | 3 | `detect-lsh-ast.py:38` | `lib/resource_policy.py:81` |
| `_placeholder` / `assert_only_trailing_ws` | 0.932 | 3 | `extract-functions-ast-py.py:48` | `lib/jsonstream.py:180` |
| `_func_to_spec` / `visit_Name` | 0.928 | 2 | `evaluate.py:31` | `extract-functions-ast-py.py:54` |
| `_func_to_spec` / `visit_Attribute` | 0.928 | 2 | `evaluate.py:31` | `extract-functions-ast-py.py:81` |
| `tokenize_to_strings` / `to_dict` | 0.927 | 3 | `lib/common.py:125` | `lib/resource_policy.py:101` |
| `_high_entry` / `_medium_entry` | 0.926 | 9 | `generate_report.py:112` | `generate_report.py:132` |
| `build_embedding` / `__init__` | 0.926 | 2 | `detect-code-embedding.py:70` | `extract-functions-ast-py.py:354` |
| `levenshtein_score` / `_decorator_name` | 0.925 | 2 | `detect-fuzzy-names.py:187` | `extract-functions-ast-py.py:270` |
| `abbreviation_boost` / `__init__` | 0.924 | 2 | `detect-fuzzy-names.py:238` | `merge-signals.py:696` |
| `_compute_pair_similarity` / `__init__` | 0.924 | 2 | `detect-metric-similarity.py:184` | `lib/resource_policy.py:180` |
| `tokenize` / `legacy` | 0.923 | 2 | `lib/common.py:84` | `merge-signals.py:716` |
| `ast_node_vector` / `normalize_type` | 0.923 | 2 | `detect-bag-of-ast.py:29` | `detect-signature-match.py:71` |
| `compute_idf` / `load_object_member` | 0.921 | 3 | `detect-tfidf-index.py:62` | `lib/jsonstream.py:278` |
| `arity_match_score` / `load_ground_truth` | 0.921 | 2 | `detect-signature-match.py:158` | `evaluate.py:36` |
| `get_return_type` / `_positive_int` | 0.92 | 3 | `detect-signature-match.py:147` | `merge-signals.py:752` |
| `make_pair_key` / `note_error` | 0.92 | 3 | `evaluate.py:26` | `lib/resource_policy.py:367` |
| `_num_or_zero` / `_decode_next` | 0.918 | 2 | `generate_report.py:58` | `lib/jsonstream.py:49` |
| `_iter_scored` / `legacy` | 0.918 | 2 | `merge-signals.py:681` | `merge-signals.py:716` |
| `_utc_now` / `__init__` | 0.918 | 2 | `lib/resource_policy.py:313` | `lib/resource_policy.py:339` |
| `hash_sequence` / `start` | 0.917 | 2 | `detect-token-clones.py:25` | `lib/resource_policy.py:207` |
| `start` / `_utc_now` | 0.916 | 4 | `lib/resource_policy.py:207` | `lib/resource_policy.py:313` |
| `overlap_coefficient` / `_git_head` | 0.916 | 2 | `lib/common.py:214` | `lib/resource_policy.py:325` |
| `tokenize` / `fill` | 0.915 | 2 | `lib/common.py:84` | `lib/jsonstream.py:73` |
| `fill` / `legacy` | 0.914 | 2 | `lib/jsonstream.py:73` | `merge-signals.py:716` |
| `hash_sequence` / `_utc_now` | 0.911 | 2 | `detect-token-clones.py:25` | `lib/resource_policy.py:313` |
| `_func_to_spec` / `note_phase` | 0.911 | 2 | `evaluate.py:31` | `lib/resource_policy.py:364` |
| `fill` / `_iter_scored` | 0.91 | 3 | `lib/jsonstream.py:73` | `merge-signals.py:681` |
| `main` / `_extract_metrics` | 0.909 | 2 | `detect-ast-similarity.py:246` | `detect-metric-similarity.py:110` |
| `main` / `_extract_metrics` | 0.909 | 2 | `detect-code-embedding.py:195` | `detect-metric-similarity.py:110` |
| `_extract_metrics` / `main` | 0.909 | 2 | `detect-metric-similarity.py:110` | `detect-winnowing.py:259` |
| `_body_lines` / `_strategy_name_from_path` | 0.909 | 2 | `merge-signals.py:49` | `merge-signals.py:492` |
| `_compute_ast_fingerprint` / `tree_rss_bytes_from_table` | 0.908 | 2 | `extract-functions-ast-py.py:94` | `lib/resource_policy.py:144` |
| `visit_arg` / `_resolve_language` | 0.906 | 3 | `extract-functions-ast-py.py:59` | `extract-functions-regex.py:130` |
| `_open_cursor` / `_is_crud_name` | 0.906 | 2 | `lib/jsonstream.py:217` | `merge-signals.py:44` |
| `_get_token_strings` / `_first_line_docstring` | 0.906 | 2 | `detect-winnowing.py:114` | `extract-functions-ast-py.py:333` |
| `_get_token_strings` / `_summary_block` | 0.906 | 2 | `detect-winnowing.py:114` | `generate_report.py:71` |
| `visit_alias` / `expect` | 0.903 | 3 | `extract-functions-ast-py.py:86` | `lib/jsonstream.py:109` |
| `func_ref` / `_positive_int` | 0.903 | 2 | `lib/common.py:270` | `merge-signals.py:752` |
| `retrieve_candidates` / `main` | 0.902 | 2 | `detect-tfidf-index.py:79` | `extract-functions-regex.py:328` |
| `__init__` / `_class_name` | 0.901 | 2 | `extract-functions-ast-py.py:43` | `extract-functions-ast-py.py:363` |
| `load_detected_pairs` / `iter_object_member_array` | 0.9 | 3 | `evaluate.py:84` | `lib/jsonstream.py:246` |
| `iter_object_members` / `convert_llm_results` | 0.899 | 3 | `lib/jsonstream.py:187` | `merge-signals.py:1050` |
| `_compute_metrics` / `_actionable_row` | 0.898 | 2 | `evaluate.py:124` | `generate_report.py:98` |
| `_safe_divide` / `note_error` | 0.897 | 3 | `evaluate.py:119` | `lib/resource_policy.py:367` |
| `expand_abbreviations` / `_decorator_names` | 0.895 | 6 | `detect-fuzzy-names.py:179` | `extract-functions-ast-py.py:278` |
| `build_embedding` / `_is_test_file` | 0.893 | 2 | `detect-code-embedding.py:70` | `extract-functions-ast-py.py:444` |
| `normalize_ast_tokens` / `iter_array` | 0.89 | 3 | `detect-token-clones.py:30` | `lib/jsonstream.py:144` |
| `add_pairs` / `iter_object_members` | 0.89 | 2 | `detect-token-clones.py:168` | `lib/jsonstream.py:187` |
| `visit_FunctionDef` / `skip_value` | 0.885 | 3 | `extract-functions-ast-py.py:410` | `lib/jsonstream.py:171` |
| `visit_AsyncFunctionDef` / `skip_value` | 0.885 | 3 | `extract-functions-ast-py.py:417` | `lib/jsonstream.py:171` |
| `_estimate_nesting_depth` / `_classify_export_type` | 0.883 | 2 | `detect-metric-similarity.py:55` | `extract-functions-ast-py.py:286` |
| `_first_line_docstring` / `_summary_block` | 0.873 | 4 | `extract-functions-ast-py.py:333` | `generate_report.py:71` |
| `detect_metric_clones` / `evaluate` | 0.869 | 3 | `detect-metric-similarity.py:221` | `evaluate.py:139` |
| `skip_value` / `stop` | 0.866 | 3 | `lib/jsonstream.py:171` | `lib/resource_policy.py:211` |
| `hash_sequence` / `__init__` | 0.856 | 4 | `detect-token-clones.py:25` | `lib/resource_policy.py:339` |
| `lcs_similarity` / `overlap_coefficient` | 0.841 | 4 | `detect-ast-similarity.py:100` | `lib/common.py:214` |
| `detect_embedding_duplicates` / `detect_fuzzy_duplicates` | 0.835 | 7 | `detect-code-embedding.py:126` | `detect-fuzzy-names.py:274` |
| `synonym_boost` / `detect_tfidf_duplicates` | 0.828 | 3 | `detect-fuzzy-names.py:197` | `detect-tfidf-index.py:156` |
| `visit_FunctionDef` / `stop` | 0.826 | 4 | `extract-functions-ast-py.py:410` | `lib/resource_policy.py:211` |
| `visit_AsyncFunctionDef` / `stop` | 0.826 | 4 | `extract-functions-ast-py.py:417` | `lib/resource_policy.py:211` |
| `visit_Name` / `note_phase` | 0.82 | 4 | `extract-functions-ast-py.py:54` | `lib/resource_policy.py:364` |
| `visit_Attribute` / `note_phase` | 0.82 | 4 | `extract-functions-ast-py.py:81` | `lib/resource_policy.py:364` |
| `start` / `__init__` | 0.817 | 5 | `lib/resource_policy.py:207` | `lib/resource_policy.py:339` |
| `make_pair_key` / `_safe_divide` | 0.809 | 4 | `evaluate.py:26` | `evaluate.py:119` |
| `get_return_type` / `func_ref` | 0.805 | 3 | `detect-signature-match.py:147` | `lib/common.py:270` |
| `_build_params` / `generate_type4_pair` | 0.8 | 4 | `extract-functions-ast-py.py:188` | `generate-corpus.py:177` |
| `add_pairs` / `convert_llm_results` | 0.789 | 3 | `detect-token-clones.py:168` | `merge-signals.py:1050` |
| `load_strategy_results` / `_refusal` | 0.768 | 4 | `merge-signals.py:171` | `merge-signals.py:804` |
| `extract_params` / `_open_scratch_db` | 0.747 | 5 | `detect-signature-match.py:105` | `merge-signals.py:554` |


---

## HIGH Confidence Duplicates

> These pairs were flagged by multiple independent detection strategies.
> Consolidate them — the evidence is strong.

### visit_Name ↔ visit_Attribute

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Name` | `visit_Attribute` |
| **File** | `extract-functions-ast-py.py:54` | `extract-functions-ast-py.py:81` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 1.0 from 9 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- lsh_ast: 1.0
- metric_similarity: 1.0
- pdg_semantic: 1.0
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 9 independent strategies

---

### _unparse_annotation ↔ _unparse_default

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_unparse_annotation` | `_unparse_default` |
| **File** | `extract-functions-ast-py.py:168` | `extract-functions-ast-py.py:178` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.985 from 10 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- lsh_ast: 1.0
- metric_similarity: 1.0
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 10 independent strategies

---

### detect_bag_of_ast_duplicates ↔ detect_pdg_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_bag_of_ast_duplicates` | `detect_pdg_duplicates` |
| **File** | `detect-bag-of-ast.py:87` | `detect-pdg-semantic.py:138` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.984 from 10 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- lsh_ast: 1.0
- metric_similarity: 0.992
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 10 independent strategies

---

### visit_FunctionDef ↔ visit_AsyncFunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_FunctionDef` | `visit_AsyncFunctionDef` |
| **File** | `extract-functions-ast-py.py:66` | `extract-functions-ast-py.py:74` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.968 from 10 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.561
- lsh_ast: 1.0
- metric_similarity: 0.979
- pdg_semantic: 1.0
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 10 independent strategies

---

### _strategy_name_from_path ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_strategy_name_from_path` | `_positive_int` |
| **File** | `merge-signals.py:492` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.968 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- metric_similarity: 0.977

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### skip_value ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `skip_value` | `_strategy_name_from_path` |
| **File** | `lib/jsonstream.py:171` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.967 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- metric_similarity: 0.957

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-ast-similarity.py:246` | `detect-code-embedding.py:195` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.998
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-ast-similarity.py:246` | `detect-winnowing.py:259` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.998
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-bag-of-ast.py:149` | `detect-pdg-semantic.py:203` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.991
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-bag-of-ast.py:149` | `detect-token-clones.py:210` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.991
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-code-embedding.py:195` | `detect-winnowing.py:259` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 1.0
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-fuzzy-names.py:338` | `detect-signature-match.py:378` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.997
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-pdg-semantic.py:203` | `detect-token-clones.py:210` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.966 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 1.0
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### detect_tfidf_duplicates ↔ _build_signature

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `_build_signature` |
| **File** | `detect-tfidf-index.py:156` | `extract-functions-ast-py.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.963 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- metric_similarity: 0.944

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ _signals_lines

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `_signals_lines` |
| **File** | `detect-ast-similarity.py:63` | `generate_report.py:105` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.962 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.953
- metric_similarity: 0.976

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### token_jaccard_score ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `token_jaccard_score` | `make_pair_key` |
| **File** | `detect-fuzzy-names.py:192` | `evaluate.py:26` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.961 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- metric_similarity: 0.946

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_values ↔ cosine_similarity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_values` | `cosine_similarity` |
| **File** | `detect-ast-similarity.py:33` | `detect-bag-of-ast.py:57` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.96 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- metric_similarity: 0.938

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _loop ↔ _discover_inputs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_loop` | `_discover_inputs` |
| **File** | `lib/resource_policy.py:220` | `merge-signals.py:501` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.959 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- metric_similarity: 0.934

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _sha256_file ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_sha256_file` | `_iter_scored` |
| **File** | `lib/resource_policy.py:317` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.959 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- metric_similarity: 0.945

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### decode_value ↔ _load_catalog_index

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `decode_value` | `_load_catalog_index` |
| **File** | `lib/jsonstream.py:116` | `merge-signals.py:536` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.958 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- metric_similarity: 0.928

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_idf ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_idf` | `skip_ws` |
| **File** | `detect-tfidf-index.py:62` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.957 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.981
- metric_similarity: 0.919

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _strategy_name_from_path ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_strategy_name_from_path` | `_iter_scored` |
| **File** | `merge-signals.py:492` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.957 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.98
- metric_similarity: 0.923

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_FunctionDef ↔ visit_AsyncFunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_FunctionDef` | `visit_AsyncFunctionDef` |
| **File** | `extract-functions-ast-py.py:410` | `extract-functions-ast-py.py:417` |

**Clone Type:** Type 1 (exact clone)

**Composite Score:** 0.956 from 11 strategies

**Detection Signals:**

- ast_similarity: 1.0
- bag_of_ast: 1.0
- code_embedding: 1.0
- fuzzy_name: 0.561
- lsh_ast: 1.0
- metric_similarity: 0.976
- pdg_semantic: 1.0
- signature_match: 0.82
- tfidf_index: 1.0
- token_clone: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 11 independent strategies

---

### levenshtein_score ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `_open_cursor` |
| **File** | `detect-fuzzy-names.py:187` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.955 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- metric_similarity: 0.943

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### tokenize_to_strings ↔ _decode_next

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize_to_strings` | `_decode_next` |
| **File** | `lib/common.py:125` | `lib/jsonstream.py:49` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.954 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- metric_similarity: 0.935

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### build_embedding ↔ abbreviation_boost

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `build_embedding` | `abbreviation_boost` |
| **File** | `detect-code-embedding.py:70` | `detect-fuzzy-names.py:238` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.953 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.985
- metric_similarity: 0.902

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _sample_table ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_sample_table` | `load_strategy_results` |
| **File** | `lib/resource_policy.py:109` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.953 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- metric_similarity: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_jsonl ↔ _load_catalog_index

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_jsonl` | `_load_catalog_index` |
| **File** | `lib/jsonstream.py:301` | `merge-signals.py:536` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.953 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- metric_similarity: 0.929

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get ↔ skip_value

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get` | `skip_value` |
| **File** | `generate_report.py:50` | `lib/jsonstream.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.953 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- metric_similarity: 0.943

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### skip_value ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `skip_value` | `_positive_int` |
| **File** | `lib/jsonstream.py:171` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.953 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.957
- metric_similarity: 0.946

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _open_cursor ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_open_cursor` | `__init__` |
| **File** | `lib/jsonstream.py:217` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.953 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.952
- metric_similarity: 0.955

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `tree_rss_bytes_from_table` |
| **File** | `detect-ast-similarity.py:63` | `lib/resource_policy.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.979
- metric_similarity: 0.91

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_values ↔ embedding_cosine

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_values` | `embedding_cosine` |
| **File** | `detect-ast-similarity.py:33` | `detect-code-embedding.py:91` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- metric_similarity: 0.912

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `iter_json_array` |
| **File** | `extract-functions-ast-py.py:246` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- metric_similarity: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ast_node_vector ↔ load_object_member

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ast_node_vector` | `load_object_member` |
| **File** | `detect-bag-of-ast.py:29` | `lib/jsonstream.py:278` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.969
- metric_similarity: 0.927

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `_open_cursor` |
| **File** | `evaluate.py:26` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- metric_similarity: 0.933

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ visit_Name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `visit_Name` |
| **File** | `extract-functions-ast-py.py:43` | `extract-functions-ast-py.py:54` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.95
- metric_similarity: 0.955

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ visit_Attribute

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `visit_Attribute` |
| **File** | `extract-functions-ast-py.py:43` | `extract-functions-ast-py.py:81` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.952 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.95
- metric_similarity: 0.955

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ _sample_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `_sample_table` |
| **File** | `extract-functions-ast-py.py:246` | `lib/resource_policy.py:109` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.951 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- metric_similarity: 0.913

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ compute_pdg_fingerprint

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `compute_pdg_fingerprint` |
| **File** | `detect-metric-similarity.py:332` | `detect-pdg-semantic.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.951 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.953
- metric_similarity: 0.947

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _placeholder ↔ expect

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_placeholder` | `expect` |
| **File** | `extract-functions-ast-py.py:48` | `lib/jsonstream.py:109` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.951 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.948
- metric_similarity: 0.955

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_object_member ↔ _discover_inputs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_object_member` | `_discover_inputs` |
| **File** | `lib/jsonstream.py:278` | `merge-signals.py:501` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.95 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- metric_similarity: 0.921

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_object_member ↔ _loop

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_object_member` | `_loop` |
| **File** | `lib/jsonstream.py:278` | `lib/resource_policy.py:220` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.95 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.951
- metric_similarity: 0.95

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### build_inverted_index ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `build_inverted_index` | `load_strategy_results` |
| **File** | `detect-tfidf-index.py:48` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.949 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- metric_similarity: 0.921

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `descendants_from_table` |
| **File** | `extract-functions-ast-py.py:246` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.949 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.952
- metric_similarity: 0.946

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### winnow ↔ _score_all

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `winnow` | `_score_all` |
| **File** | `detect-winnowing.py:65` | `merge-signals.py:635` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.948 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- metric_similarity: 0.909

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _sha256_file ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_sha256_file` | `_positive_int` |
| **File** | `lib/resource_policy.py:317` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.948 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.953
- metric_similarity: 0.94

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expect ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expect` | `tree_rss_bytes_from_table` |
| **File** | `lib/jsonstream.py:109` | `lib/resource_policy.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.948 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.938
- metric_similarity: 0.963

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### with_overrides ↔ _load_catalog_index

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `with_overrides` | `_load_catalog_index` |
| **File** | `lib/resource_policy.py:81` | `merge-signals.py:536` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.947 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- metric_similarity: 0.917

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-ast-similarity.py:246` | `detect-lsh-ast.py:194` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.946 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.986
- bag_of_ast: 1.0
- code_embedding: 0.997
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.957
- pdg_semantic: 0.917
- signature_match: 0.82
- tfidf_index: 0.998
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-code-embedding.py:195` | `detect-lsh-ast.py:194` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.946 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.986
- bag_of_ast: 1.0
- code_embedding: 0.997
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.955
- pdg_semantic: 0.917
- signature_match: 0.82
- tfidf_index: 0.998
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-lsh-ast.py:194` | `detect-winnowing.py:259` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.946 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.986
- bag_of_ast: 1.0
- code_embedding: 0.997
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.955
- pdg_semantic: 0.917
- signature_match: 0.82
- tfidf_index: 0.998
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### _cyclomatic_complexity ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_cyclomatic_complexity` | `iter_json_array` |
| **File** | `extract-functions-ast-py.py:143` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.946 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- metric_similarity: 0.901

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_idf ↔ write

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_idf` | `write` |
| **File** | `detect-tfidf-index.py:62` | `lib/resource_policy.py:404` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.945 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.947
- metric_similarity: 0.94

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ _extract_token_sequence

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `_extract_token_sequence` |
| **File** | `extract-functions-ast-py.py:43` | `extract-functions-ast-py.py:109` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.944 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- metric_similarity: 0.901

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-bag-of-ast.py:149` | `detect-lsh-ast.py:194` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.942 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.985
- bag_of_ast: 0.999
- code_embedding: 0.995
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.971
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.996
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-lsh-ast.py:194` | `detect-pdg-semantic.py:203` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.942 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.985
- bag_of_ast: 0.999
- code_embedding: 0.995
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.979
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.996
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-lsh-ast.py:194` | `detect-token-clones.py:210` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.942 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.985
- bag_of_ast: 0.999
- code_embedding: 0.995
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.979
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.996
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### detect_clones ↔ add_pairs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_clones` | `add_pairs` |
| **File** | `detect-token-clones.py:119` | `detect-token-clones.py:168` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.942 from 4 strategies

**Detection Signals:**

- bag_of_ast: 0.993
- code_embedding: 0.908
- tfidf_index: 0.877
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 4 independent detection strategies

---

### arity_match_score ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `arity_match_score` | `iter_json_array` |
| **File** | `detect-signature-match.py:158` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.942 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- metric_similarity: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `_strategy_name_from_path` |
| **File** | `detect-token-clones.py:67` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.942 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- metric_similarity: 0.912

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### hash_sequence ↔ _num_or_zero

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `hash_sequence` | `_num_or_zero` |
| **File** | `detect-token-clones.py:25` | `generate_report.py:58` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.942 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.946
- metric_similarity: 0.936

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _class_name ↔ _get

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_class_name` | `_get` |
| **File** | `extract-functions-ast-py.py:363` | `generate_report.py:50` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.942 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.944
- metric_similarity: 0.939

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `__init__` |
| **File** | `evaluate.py:26` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.942 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- metric_similarity: 0.941

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_bag_of_ast_duplicates ↔ _resolve_input

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_bag_of_ast_duplicates` | `_resolve_input` |
| **File** | `detect-bag-of-ast.py:87` | `generate_report.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.941 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- metric_similarity: 0.901

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _iter_scored ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_iter_scored` | `_positive_int` |
| **File** | `merge-signals.py:681` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.941 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- metric_similarity: 0.902

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get` | `_strategy_name_from_path` |
| **File** | `generate_report.py:50` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.941 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- metric_similarity: 0.905

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _placeholder ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_placeholder` | `tree_rss_bytes_from_table` |
| **File** | `extract-functions-ast-py.py:48` | `lib/resource_policy.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.941 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.953
- metric_similarity: 0.923

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_Name ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Name` | `__init__` |
| **File** | `extract-functions-ast-py.py:54` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.941 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- metric_similarity: 0.938

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_Attribute ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Attribute` | `__init__` |
| **File** | `extract-functions-ast-py.py:81` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.941 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- metric_similarity: 0.938

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### retrieve_candidates ↔ _resolve_input

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `retrieve_candidates` | `_resolve_input` |
| **File** | `detect-tfidf-index.py:79` | `generate_report.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.94 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.95
- metric_similarity: 0.924

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `__init__` |
| **File** | `detect-fuzzy-names.py:187` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.94 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.944
- metric_similarity: 0.933

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _compute_metrics ↔ _low_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_metrics` | `_low_entry` |
| **File** | `evaluate.py:124` | `generate_report.py:147` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.94 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.938
- metric_similarity: 0.945

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### token_jaccard_score ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `token_jaccard_score` | `__init__` |
| **File** | `detect-fuzzy-names.py:192` | `extract-functions-ast-py.py:43` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.94 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.934
- metric_similarity: 0.948

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _iter_result_pairs ↔ load_object_member

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_iter_result_pairs` | `load_object_member` |
| **File** | `evaluate.py:61` | `lib/jsonstream.py:278` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.94 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.93
- metric_similarity: 0.955

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `_open_cursor` |
| **File** | `extract-functions-ast-py.py:43` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.94 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.926
- metric_similarity: 0.963

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### build_inverted_index ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `build_inverted_index` | `_iter_records` |
| **File** | `detect-tfidf-index.py:48` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.939 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.95
- metric_similarity: 0.923

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_ground_truth ↔ _open_scratch_db

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_ground_truth` | `_open_scratch_db` |
| **File** | `evaluate.py:36` | `merge-signals.py:554` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.939 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- metric_similarity: 0.934

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ _write_legacy_json

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `_write_legacy_json` |
| **File** | `extract-functions-ast-py.py:246` | `merge-signals.py:728` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.939 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.924
- metric_similarity: 0.962

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get ↔ _sha256_file

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get` | `_sha256_file` |
| **File** | `generate_report.py:50` | `lib/resource_policy.py:317` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.938 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.948
- metric_similarity: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ visit_Name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `visit_Name` |
| **File** | `evaluate.py:26` | `extract-functions-ast-py.py:54` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.938 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.93
- metric_similarity: 0.951

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ visit_Attribute

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `visit_Attribute` |
| **File** | `evaluate.py:26` | `extract-functions-ast-py.py:81` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.938 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.93
- metric_similarity: 0.951

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_json_array ↔ _sample_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_json_array` | `_sample_table` |
| **File** | `lib/jsonstream.py:222` | `lib/resource_policy.py:109` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.959
- metric_similarity: 0.903

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_jsonl ↔ _loop

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_jsonl` | `_loop` |
| **File** | `lib/jsonstream.py:301` | `lib/resource_policy.py:220` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.954
- metric_similarity: 0.91

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_Name ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Name` | `_utc_now` |
| **File** | `extract-functions-ast-py.py:54` | `lib/resource_policy.py:313` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.953
- tfidf_index: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_Attribute ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Attribute` | `_utc_now` |
| **File** | `extract-functions-ast-py.py:81` | `lib/resource_policy.py:313` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.953
- tfidf_index: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ _num_or_zero

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `_num_or_zero` |
| **File** | `detect-fuzzy-names.py:187` | `generate_report.py:58` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.948
- metric_similarity: 0.919

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `_positive_int` |
| **File** | `detect-token-clones.py:67` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.946
- metric_similarity: 0.923

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _signals_lines ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_signals_lines` | `tree_rss_bytes_from_table` |
| **File** | `generate_report.py:105` | `lib/resource_policy.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.937 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.939
- metric_similarity: 0.933

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-ast-similarity.py:246` | `detect-pdg-semantic.py:203` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.936 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.938
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-ast-similarity.py:246` | `detect-token-clones.py:210` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.936 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.938
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-code-embedding.py:195` | `detect-pdg-semantic.py:203` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.936 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.937
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-code-embedding.py:195` | `detect-token-clones.py:210` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.936 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.937
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-pdg-semantic.py:203` | `detect-winnowing.py:259` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.936 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.937
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-token-clones.py:210` | `detect-winnowing.py:259` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.936 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.937
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### detect_bag_of_ast_duplicates ↔ detect_embedding_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_bag_of_ast_duplicates` | `detect_embedding_duplicates` |
| **File** | `detect-bag-of-ast.py:87` | `detect-code-embedding.py:126` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.936 from 9 strategies

**Detection Signals:**

- ast_similarity: 0.944
- bag_of_ast: 1.0
- code_embedding: 0.989
- lsh_ast: 1.0
- metric_similarity: 0.974
- pdg_semantic: 0.75
- signature_match: 0.82
- tfidf_index: 0.991
- winnowing: 0.975

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 9 independent detection strategies

---

### detect_embedding_duplicates ↔ detect_pdg_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_embedding_duplicates` | `detect_pdg_duplicates` |
| **File** | `detect-code-embedding.py:126` | `detect-pdg-semantic.py:138` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.936 from 9 strategies

**Detection Signals:**

- ast_similarity: 0.944
- bag_of_ast: 1.0
- code_embedding: 0.989
- lsh_ast: 1.0
- metric_similarity: 0.981
- pdg_semantic: 0.75
- signature_match: 0.82
- tfidf_index: 0.991
- winnowing: 0.975

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 9 independent detection strategies

---

### _summary_block ↔ start

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_summary_block` | `start` |
| **File** | `generate_report.py:71` | `lib/resource_policy.py:343` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.936 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.951
- metric_similarity: 0.912

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _num_or_zero ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_num_or_zero` | `__init__` |
| **File** | `generate_report.py:58` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.936 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.904
- metric_similarity: 0.985

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-ast-similarity.py:246` | `detect-bag-of-ast.py:149` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.935 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.932
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-bag-of-ast.py:149` | `detect-code-embedding.py:195` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.935 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.93
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### main ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `main` |
| **File** | `detect-bag-of-ast.py:149` | `detect-winnowing.py:259` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.935 from 10 strategies

**Detection Signals:**

- ast_similarity: 0.971
- bag_of_ast: 0.998
- code_embedding: 0.984
- fuzzy_name: 0.7
- lsh_ast: 1.0
- metric_similarity: 0.93
- pdg_semantic: 0.875
- signature_match: 0.82
- tfidf_index: 0.989
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 10 independent detection strategies

---

### _safe_divide ↔ _num_or_zero

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_safe_divide` | `_num_or_zero` |
| **File** | `evaluate.py:119` | `generate_report.py:58` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.935 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.956
- metric_similarity: 0.903

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `__init__` |
| **File** | `evaluate.py:26` | `extract-functions-ast-py.py:43` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.935 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.944
- metric_similarity: 0.921

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _class_name ↔ skip_value

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_class_name` | `skip_value` |
| **File** | `extract-functions-ast-py.py:363` | `lib/jsonstream.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.935 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.94
- metric_similarity: 0.926

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `main` |
| **File** | `detect-tfidf-index.py:156` | `detect-tfidf-index.py:185` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.935 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.935
- metric_similarity: 0.934

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_set ↔ with_overrides

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_set` | `with_overrides` |
| **File** | `detect-lsh-ast.py:38` | `lib/resource_policy.py:81` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.934 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- metric_similarity: 0.948
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### get_param_count ↔ _is_crud_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `_is_crud_name` |
| **File** | `detect-signature-match.py:132` | `merge-signals.py:44` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.934 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- tfidf_index: 0.907

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _compute_pair_similarity ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_pair_similarity` | `main` |
| **File** | `detect-metric-similarity.py:184` | `extract-functions-ast-py.py:537` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.934 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.938
- metric_similarity: 0.927

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### cosine_similarity ↔ embedding_cosine

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `cosine_similarity` | `embedding_cosine` |
| **File** | `detect-bag-of-ast.py:57` | `detect-code-embedding.py:91` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.933 from 9 strategies

**Detection Signals:**

- ast_similarity: 0.903
- bag_of_ast: 0.997
- code_embedding: 0.929
- lsh_ast: 1.0
- metric_similarity: 0.963
- pdg_semantic: 0.867
- signature_match: 0.82
- tfidf_index: 0.996
- winnowing: 0.932

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 9 independent detection strategies

---

### visit_alias ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_alias` | `_utc_now` |
| **File** | `extract-functions-ast-py.py:86` | `lib/resource_policy.py:313` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.933 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.957
- tfidf_index: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### hash_sequence ↔ _empty_summary

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `hash_sequence` | `_empty_summary` |
| **File** | `detect-token-clones.py:25` | `merge-signals.py:689` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.933 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.95
- metric_similarity: 0.905

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_object_member_array ↔ atomic_write_text

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_object_member_array` | `atomic_write_text` |
| **File** | `lib/jsonstream.py:246` | `lib/jsonstream.py:344` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.933 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.945
- metric_similarity: 0.914

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### fill ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `fill` | `_strategy_name_from_path` |
| **File** | `lib/jsonstream.py:73` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.933 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.939
- metric_similarity: 0.924

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### token_jaccard_score ↔ hash_sequence

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `token_jaccard_score` | `hash_sequence` |
| **File** | `detect-fuzzy-names.py:192` | `detect-token-clones.py:25` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.932 from 8 strategies

**Detection Signals:**

- ast_similarity: 0.804
- bag_of_ast: 0.995
- code_embedding: 0.935
- lsh_ast: 1.0
- metric_similarity: 0.941
- signature_match: 0.82
- tfidf_index: 0.979
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 8 independent detection strategies

---

### _placeholder ↔ assert_only_trailing_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_placeholder` | `assert_only_trailing_ws` |
| **File** | `extract-functions-ast-py.py:48` | `lib/jsonstream.py:180` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.932 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.958
- metric_similarity: 0.96
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### func_ref ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `func_ref` | `make_pair_key` |
| **File** | `lib/common.py:270` | `merge-signals.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.932 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.947
- metric_similarity: 0.91

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_embedding_duplicates ↔ _extract_metrics

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_embedding_duplicates` | `_extract_metrics` |
| **File** | `detect-code-embedding.py:126` | `detect-metric-similarity.py:110` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.932 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- metric_similarity: 0.915

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_FunctionDef ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_FunctionDef` | `__init__` |
| **File** | `extract-functions-ast-py.py:66` | `merge-signals.py:696` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.931 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.95
- metric_similarity: 0.902

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_similarity ↔ expect

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_similarity` | `expect` |
| **File** | `detect-ast-similarity.py:100` | `lib/jsonstream.py:109` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.931 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.941
- metric_similarity: 0.916

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `__init__` |
| **File** | `detect-fuzzy-names.py:187` | `extract-functions-ast-py.py:43` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.931 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.932
- metric_similarity: 0.929

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _safe_divide ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_safe_divide` | `_open_cursor` |
| **File** | `evaluate.py:119` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.931 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.928
- metric_similarity: 0.934

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_Name ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Name` | `_open_cursor` |
| **File** | `extract-functions-ast-py.py:54` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.931 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.898
- metric_similarity: 0.982

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_Attribute ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_Attribute` | `_open_cursor` |
| **File** | `extract-functions-ast-py.py:81` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.931 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.898
- metric_similarity: 0.982

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _extract_metrics ↔ detect_pdg_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_extract_metrics` | `detect_pdg_duplicates` |
| **File** | `detect-metric-similarity.py:110` | `detect-pdg-semantic.py:138` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.93 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.942
- metric_similarity: 0.913

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_params ↔ arity_match_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_params` | `arity_match_score` |
| **File** | `detect-signature-match.py:105` | `detect-signature-match.py:158` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.93 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.933
- metric_similarity: 0.925

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _normalized_distance ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `__init__` |
| **File** | `detect-metric-similarity.py:179` | `extract-functions-ast-py.py:43` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.93 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.91
- metric_similarity: 0.962

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _normalized_distance ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `__init__` |
| **File** | `detect-metric-similarity.py:179` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.929 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.928
- metric_similarity: 0.929

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_arg ↔ visit_AsyncFunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `visit_AsyncFunctionDef` |
| **File** | `extract-functions-ast-py.py:59` | `extract-functions-ast-py.py:74` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.928 from 8 strategies

**Detection Signals:**

- ast_similarity: 0.897
- bag_of_ast: 0.997
- code_embedding: 0.969
- lsh_ast: 0.938
- metric_similarity: 0.964
- pdg_semantic: 0.833
- tfidf_index: 0.866
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 8 independent detection strategies

---

### detect_bag_of_ast_duplicates ↔ _extract_metrics

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_bag_of_ast_duplicates` | `_extract_metrics` |
| **File** | `detect-bag-of-ast.py:87` | `detect-metric-similarity.py:110` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.928 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.942
- metric_similarity: 0.906

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### elapsed ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `elapsed` | `_utc_now` |
| **File** | `lib/resource_policy.py:216` | `lib/resource_policy.py:313` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.928 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.927
- metric_similarity: 0.929

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _func_to_spec ↔ visit_Name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_func_to_spec` | `visit_Name` |
| **File** | `evaluate.py:31` | `extract-functions-ast-py.py:54` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.928 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.986
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _func_to_spec ↔ visit_Attribute

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_func_to_spec` | `visit_Attribute` |
| **File** | `evaluate.py:31` | `extract-functions-ast-py.py:81` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.928 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.986
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### tokenize_to_strings ↔ to_dict

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize_to_strings` | `to_dict` |
| **File** | `lib/common.py:125` | `lib/resource_policy.py:101` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.927 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.939
- metric_similarity: 0.966
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### _open_cursor ↔ note_phase

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_open_cursor` | `note_phase` |
| **File** | `lib/jsonstream.py:217` | `lib/resource_policy.py:364` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.927 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.925
- metric_similarity: 0.929

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### start ↔ elapsed

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `start` | `elapsed` |
| **File** | `lib/resource_policy.py:207` | `lib/resource_policy.py:216` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.927 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.913
- metric_similarity: 0.947

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _high_entry ↔ _medium_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_high_entry` | `_medium_entry` |
| **File** | `generate_report.py:112` | `generate_report.py:132` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.926 from 9 strategies

**Detection Signals:**

- ast_similarity: 0.989
- bag_of_ast: 1.0
- code_embedding: 1.0
- lsh_ast: 1.0
- metric_similarity: 0.95
- pdg_semantic: 0.6
- signature_match: 0.82
- tfidf_index: 1.0
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 9 independent detection strategies

---

### visit_arg ↔ visit_FunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `visit_FunctionDef` |
| **File** | `extract-functions-ast-py.py:59` | `extract-functions-ast-py.py:66` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.926 from 8 strategies

**Detection Signals:**

- ast_similarity: 0.897
- bag_of_ast: 0.997
- code_embedding: 0.969
- lsh_ast: 0.938
- metric_similarity: 0.943
- pdg_semantic: 0.833
- tfidf_index: 0.866
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 8 independent detection strategies

---

### build_embedding ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `build_embedding` | `__init__` |
| **File** | `detect-code-embedding.py:70` | `extract-functions-ast-py.py:354` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.926 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### detect_fuzzy_duplicates ↔ detect_signature_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_fuzzy_duplicates` | `detect_signature_duplicates` |
| **File** | `detect-fuzzy-names.py:274` | `detect-signature-match.py:329` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.925 from 7 strategies

**Detection Signals:**

- ast_similarity: 0.797
- bag_of_ast: 0.995
- code_embedding: 0.964
- lsh_ast: 1.0
- signature_match: 0.82
- tfidf_index: 0.971
- winnowing: 0.94

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 7 independent detection strategies

---

### levenshtein_score ↔ _decorator_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `_decorator_name` |
| **File** | `detect-fuzzy-names.py:187` | `extract-functions-ast-py.py:270` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.925 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### main ↔ winnow

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `winnow` |
| **File** | `detect-metric-similarity.py:332` | `detect-winnowing.py:65` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.925 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.935
- metric_similarity: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### assert_only_trailing_ws ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `assert_only_trailing_ws` | `tree_rss_bytes_from_table` |
| **File** | `lib/jsonstream.py:180` | `lib/resource_policy.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.925 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.921
- metric_similarity: 0.93

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### abbreviation_boost ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `abbreviation_boost` | `__init__` |
| **File** | `detect-fuzzy-names.py:238` | `merge-signals.py:696` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.924 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.958
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _compute_pair_similarity ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_pair_similarity` | `__init__` |
| **File** | `detect-metric-similarity.py:184` | `lib/resource_policy.py:180` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.924 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.956
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### token_jaccard_score ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `token_jaccard_score` | `__init__` |
| **File** | `detect-fuzzy-names.py:192` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.924 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.932
- metric_similarity: 0.912

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ winnow

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `winnow` |
| **File** | `detect-signature-match.py:378` | `detect-winnowing.py:65` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.924 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.926
- metric_similarity: 0.92

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### tokenize ↔ legacy

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize` | `legacy` |
| **File** | `lib/common.py:84` | `merge-signals.py:716` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.923 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.955
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### ast_node_vector ↔ normalize_type

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ast_node_vector` | `normalize_type` |
| **File** | `detect-bag-of-ast.py:29` | `detect-signature-match.py:71` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.923 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.954
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### main ↔ winnow

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `winnow` |
| **File** | `detect-fuzzy-names.py:338` | `detect-winnowing.py:65` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.923 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.926
- metric_similarity: 0.917

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ visit_Name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `visit_Name` |
| **File** | `detect-fuzzy-names.py:187` | `extract-functions-ast-py.py:54` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.923 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.917
- metric_similarity: 0.932

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ visit_Attribute

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `visit_Attribute` |
| **File** | `detect-fuzzy-names.py:187` | `extract-functions-ast-py.py:81` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.923 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.917
- metric_similarity: 0.932

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ _body_lines

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `_body_lines` |
| **File** | `detect-signature-match.py:147` | `merge-signals.py:49` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.923 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.912
- metric_similarity: 0.94

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ _should_skip_test_file

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `_should_skip_test_file` |
| **File** | `detect-signature-match.py:132` | `extract-functions-regex.py:142` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.922 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- tfidf_index: 0.881

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### note_phase ↔ note_error

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `note_phase` | `note_error` |
| **File** | `lib/resource_policy.py:364` | `lib/resource_policy.py:367` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.921 from 5 strategies

**Detection Signals:**

- bag_of_ast: 0.946
- lsh_ast: 0.969
- metric_similarity: 0.937
- signature_match: 0.82
- tfidf_index: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 5 independent detection strategies

---

### compute_idf ↔ load_object_member

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_idf` | `load_object_member` |
| **File** | `detect-tfidf-index.py:62` | `lib/jsonstream.py:278` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.921 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- metric_similarity: 0.905
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### arity_match_score ↔ load_ground_truth

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `arity_match_score` | `load_ground_truth` |
| **File** | `detect-signature-match.py:158` | `evaluate.py:36` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.921 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.949
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _compute_metrics ↔ _medium_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_metrics` | `_medium_entry` |
| **File** | `evaluate.py:124` | `generate_report.py:132` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.921 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.928
- metric_similarity: 0.91

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ _write_legacy_json

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `_write_legacy_json` |
| **File** | `detect-tfidf-index.py:156` | `merge-signals.py:728` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.921 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.904
- metric_similarity: 0.948

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `_positive_int` |
| **File** | `detect-signature-match.py:147` | `merge-signals.py:752` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.92 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.958
- metric_similarity: 0.901
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### make_pair_key ↔ note_error

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `note_error` |
| **File** | `evaluate.py:26` | `lib/resource_policy.py:367` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.92 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.939
- metric_similarity: 0.933
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### to_dict ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `to_dict` | `__init__` |
| **File** | `lib/resource_policy.py:101` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.92 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- tfidf_index: 0.88

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ note_error

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `note_error` |
| **File** | `detect-fuzzy-names.py:187` | `lib/resource_policy.py:367` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.92 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.925
- metric_similarity: 0.913

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ winnow

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `winnow` |
| **File** | `detect-bag-of-ast.py:149` | `detect-winnowing.py:65` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.92 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- metric_similarity: 0.917

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_ast_similarity ↔ add_pairs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_ast_similarity` | `add_pairs` |
| **File** | `detect-ast-similarity.py:112` | `detect-token-clones.py:168` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.919 from 4 strategies

**Detection Signals:**

- bag_of_ast: 0.991
- code_embedding: 0.91
- tfidf_index: 0.909
- winnowing: 0.862

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 4 independent detection strategies

---

### _actionable_row ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_actionable_row` | `make_pair_key` |
| **File** | `generate_report.py:98` | `merge-signals.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.919 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82
- tfidf_index: 0.954

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### elapsed ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `elapsed` | `__init__` |
| **File** | `lib/resource_policy.py:216` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.919 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.9
- metric_similarity: 0.947

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### generate_type1_pair ↔ generate_type2_pair

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `generate_type1_pair` | `generate_type2_pair` |
| **File** | `generate-corpus.py:99` | `generate-corpus.py:119` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.918 from 9 strategies

**Detection Signals:**

- ast_similarity: 0.919
- bag_of_ast: 1.0
- code_embedding: 0.979
- lsh_ast: 0.945
- metric_similarity: 0.976
- pdg_semantic: 0.667
- signature_match: 0.82
- tfidf_index: 0.998
- winnowing: 1.0

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 9 independent detection strategies

---

### _num_or_zero ↔ _decode_next

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_num_or_zero` | `_decode_next` |
| **File** | `generate_report.py:58` | `lib/jsonstream.py:49` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.918 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _iter_scored ↔ legacy

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_iter_scored` | `legacy` |
| **File** | `merge-signals.py:681` | `merge-signals.py:716` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.918 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.942
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### tokenize_to_strings ↔ _empty_summary

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize_to_strings` | `_empty_summary` |
| **File** | `lib/common.py:125` | `merge-signals.py:689` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.918 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.924
- metric_similarity: 0.909

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _utc_now ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_utc_now` | `__init__` |
| **File** | `lib/resource_policy.py:313` | `lib/resource_policy.py:339` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.918 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.955
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### main ↔ winnow

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `winnow` |
| **File** | `detect-pdg-semantic.py:203` | `detect-winnowing.py:65` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.917 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- metric_similarity: 0.909

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ winnow

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `winnow` |
| **File** | `detect-token-clones.py:210` | `detect-winnowing.py:65` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.917 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- metric_similarity: 0.909

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _compute_metrics ↔ _compute_ast_fingerprint

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_metrics` | `_compute_ast_fingerprint` |
| **File** | `evaluate.py:124` | `extract-functions-ast-py.py:94` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.917 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- metric_similarity: 0.909

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### fill ↔ _sha256_file

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `fill` | `_sha256_file` |
| **File** | `lib/jsonstream.py:73` | `lib/resource_policy.py:317` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.917 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.911
- metric_similarity: 0.925

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### hash_sequence ↔ start

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `hash_sequence` | `start` |
| **File** | `detect-token-clones.py:25` | `lib/resource_policy.py:207` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.917 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.952
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### start ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `start` | `_utc_now` |
| **File** | `lib/resource_policy.py:207` | `lib/resource_policy.py:313` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.916 from 4 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- metric_similarity: 0.955
- tfidf_index: 0.87
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 4 independent strategies

---

### token_jaccard_score ↔ _normalized_distance

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `token_jaccard_score` | `_normalized_distance` |
| **File** | `detect-fuzzy-names.py:192` | `detect-metric-similarity.py:179` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.916 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- metric_similarity: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### visit_arg ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `_utc_now` |
| **File** | `extract-functions-ast-py.py:59` | `lib/resource_policy.py:313` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.916 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.949
- tfidf_index: 0.886

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_alias ↔ _decorator_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_alias` | `_decorator_name` |
| **File** | `extract-functions-ast-py.py:86` | `extract-functions-ast-py.py:270` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.916 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.921
- metric_similarity: 0.908

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_fingerprint ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_fingerprint` | `__init__` |
| **File** | `detect-winnowing.py:133` | `lib/jsonstream.py:61` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.916 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.915
- metric_similarity: 0.916

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_json_array ↔ _write_legacy_json

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_json_array` | `_write_legacy_json` |
| **File** | `lib/jsonstream.py:222` | `merge-signals.py:728` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.916 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.913
- metric_similarity: 0.92

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ func_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `func_key` |
| **File** | `extract-functions-ast-py.py:43` | `lib/common.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.916 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.912
- metric_similarity: 0.921

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### overlap_coefficient ↔ _git_head

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `overlap_coefficient` | `_git_head` |
| **File** | `lib/common.py:214` | `lib/resource_policy.py:325` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.916 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.949
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### detect_ast_similarity ↔ detect_bag_of_ast_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_ast_similarity` | `detect_bag_of_ast_duplicates` |
| **File** | `detect-ast-similarity.py:112` | `detect-bag-of-ast.py:87` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 6 strategies

**Detection Signals:**

- bag_of_ast: 0.998
- code_embedding: 0.959
- lsh_ast: 0.852
- signature_match: 0.82
- tfidf_index: 0.952
- winnowing: 0.889

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 6 independent detection strategies

---

### detect_ast_similarity ↔ detect_pdg_duplicates

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_ast_similarity` | `detect_pdg_duplicates` |
| **File** | `detect-ast-similarity.py:112` | `detect-pdg-semantic.py:138` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 6 strategies

**Detection Signals:**

- bag_of_ast: 0.998
- code_embedding: 0.959
- lsh_ast: 0.852
- signature_match: 0.82
- tfidf_index: 0.952
- winnowing: 0.889

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 6 independent detection strategies

---

### _medium_entry ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_medium_entry` | `make_pair_key` |
| **File** | `generate_report.py:132` | `merge-signals.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82
- tfidf_index: 0.95

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### _high_entry ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_high_entry` | `make_pair_key` |
| **File** | `generate_report.py:112` | `merge-signals.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.959
- signature_match: 0.82
- tfidf_index: 0.95

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### func_key ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `func_key` | `__init__` |
| **File** | `lib/common.py:261` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.904
- metric_similarity: 0.92
- tfidf_index: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### tokenize ↔ fill

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize` | `fill` |
| **File** | `lib/common.py:84` | `lib/jsonstream.py:73` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.915 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.934
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _compute_metrics ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_metrics` | `__init__` |
| **File** | `evaluate.py:124` | `extract-functions-ast-py.py:354` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.923
- metric_similarity: 0.903

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ _is_crud_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `_is_crud_name` |
| **File** | `extract-functions-ast-py.py:43` | `merge-signals.py:44` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- metric_similarity: 0.903

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### assert_only_trailing_ws ↔ _body_lines

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `assert_only_trailing_ws` | `_body_lines` |
| **File** | `lib/jsonstream.py:180` | `merge-signals.py:49` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.915 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.917
- metric_similarity: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### fill ↔ legacy

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `fill` | `legacy` |
| **File** | `lib/jsonstream.py:73` | `merge-signals.py:716` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.914 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.933
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### synonym_boost ↔ normalize_ast_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `synonym_boost` | `normalize_ast_tokens` |
| **File** | `detect-fuzzy-names.py:197` | `detect-token-clones.py:30` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.914 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.923
- metric_similarity: 0.902

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _normalized_distance ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `__init__` |
| **File** | `detect-metric-similarity.py:179` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.914 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- metric_similarity: 0.901

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### abbreviation_boost ↔ start

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `abbreviation_boost` | `start` |
| **File** | `detect-fuzzy-names.py:238` | `lib/resource_policy.py:343` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.914 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.89
- metric_similarity: 0.95

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _low_entry ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_low_entry` | `make_pair_key` |
| **File** | `generate_report.py:147` | `merge-signals.py:160` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.913 from 4 strategies

**Detection Signals:**

- bag_of_ast: 0.957
- metric_similarity: 0.916
- signature_match: 0.82
- tfidf_index: 0.945

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 4 independent detection strategies

---

### iter_object_members ↔ _load_catalog_index

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_object_members` | `_load_catalog_index` |
| **File** | `lib/jsonstream.py:187` | `merge-signals.py:536` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.913 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.916
- metric_similarity: 0.908

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _normalized_distance ↔ visit_Name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `visit_Name` |
| **File** | `detect-metric-similarity.py:179` | `extract-functions-ast-py.py:54` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.913 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.881
- metric_similarity: 0.964

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _normalized_distance ↔ visit_Attribute

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `visit_Attribute` |
| **File** | `detect-metric-similarity.py:179` | `extract-functions-ast-py.py:81` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.913 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.881
- metric_similarity: 0.964

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### func_ref ↔ legacy

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `func_ref` | `legacy` |
| **File** | `lib/common.py:270` | `merge-signals.py:716` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.912 from 5 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- lsh_ast: 0.938
- metric_similarity: 0.944
- signature_match: 0.82
- tfidf_index: 0.896

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 5 independent detection strategies

---

### levenshtein_score ↔ hash_sequence

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `hash_sequence` |
| **File** | `detect-fuzzy-names.py:187` | `detect-token-clones.py:25` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.912 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- metric_similarity: 0.952
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### _normalized_distance ↔ note_phase

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `note_phase` |
| **File** | `detect-metric-similarity.py:179` | `lib/resource_policy.py:364` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.912 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.913
- metric_similarity: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ generate_non_clone_pair

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `generate_non_clone_pair` |
| **File** | `extract-functions-ast-py.py:537` | `generate-corpus.py:207` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.912 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.908
- metric_similarity: 0.918

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_arg ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `_open_cursor` |
| **File** | `extract-functions-ast-py.py:59` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.911 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.897
- metric_similarity: 0.933

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### hash_sequence ↔ _utc_now

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `hash_sequence` | `_utc_now` |
| **File** | `detect-token-clones.py:25` | `lib/resource_policy.py:313` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.911 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.933
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _func_to_spec ↔ note_phase

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_func_to_spec` | `note_phase` |
| **File** | `evaluate.py:31` | `lib/resource_policy.py:364` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.911 from 2 strategies

**Detection Signals:**

- metric_similarity: 0.933
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _medium_entry ↔ _low_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_medium_entry` | `_low_entry` |
| **File** | `generate_report.py:132` | `generate_report.py:147` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.91 from 8 strategies

**Detection Signals:**

- ast_similarity: 0.728
- bag_of_ast: 0.999
- code_embedding: 0.983
- lsh_ast: 1.0
- metric_similarity: 0.912
- signature_match: 0.82
- tfidf_index: 0.999
- winnowing: 0.85

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 8 independent detection strategies

---

### fill ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `fill` | `_iter_scored` |
| **File** | `lib/jsonstream.py:73` | `merge-signals.py:681` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.91 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.927
- metric_similarity: 0.904
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### get_param_count ↔ tokenize

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `tokenize` |
| **File** | `detect-signature-match.py:132` | `lib/common.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.91 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.987
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_length ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `main` |
| **File** | `detect-ast-similarity.py:70` | `detect-bag-of-ast.py:149` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.91 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.91
- metric_similarity: 0.91

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _unparse_annotation ↔ skip_value

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_unparse_annotation` | `skip_value` |
| **File** | `extract-functions-ast-py.py:168` | `lib/jsonstream.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.91 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.878
- metric_similarity: 0.961

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _unparse_default ↔ skip_value

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_unparse_default` | `skip_value` |
| **File** | `extract-functions-ast-py.py:178` | `lib/jsonstream.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.91 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.878
- metric_similarity: 0.961

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_strategy_results ↔ _discover_inputs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_strategy_results` | `_discover_inputs` |
| **File** | `merge-signals.py:171` | `merge-signals.py:501` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.909 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.985
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ _extract_metrics

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_extract_metrics` |
| **File** | `detect-ast-similarity.py:246` | `detect-metric-similarity.py:110` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.909 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### main ↔ _extract_metrics

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_extract_metrics` |
| **File** | `detect-code-embedding.py:195` | `detect-metric-similarity.py:110` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.909 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _extract_metrics ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_extract_metrics` | `main` |
| **File** | `detect-metric-similarity.py:110` | `detect-winnowing.py:259` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.909 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.922
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _body_lines ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_body_lines` | `_strategy_name_from_path` |
| **File** | `merge-signals.py:49` | `merge-signals.py:492` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.909 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.921
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _high_entry ↔ _low_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_high_entry` | `_low_entry` |
| **File** | `generate_report.py:112` | `generate_report.py:147` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.908 from 7 strategies

**Detection Signals:**

- ast_similarity: 0.718
- bag_of_ast: 0.999
- code_embedding: 0.984
- lsh_ast: 1.0
- signature_match: 0.82
- tfidf_index: 0.999
- winnowing: 0.85

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 7 independent detection strategies

---

### ngrams ↔ raw_token_values

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `raw_token_values` |
| **File** | `detect-ast-similarity.py:63` | `detect-token-clones.py:67` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.984
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_params ↔ tokenize

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_params` | `tokenize` |
| **File** | `extract-functions-ast-py.py:188` | `lib/common.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.984
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `load_strategy_results` |
| **File** | `detect-tfidf-index.py:34` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.983
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _compute_ast_fingerprint ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_ast_fingerprint` | `tree_rss_bytes_from_table` |
| **File** | `extract-functions-ast-py.py:94` | `lib/resource_policy.py:144` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.919
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### lcs_length ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `main` |
| **File** | `detect-ast-similarity.py:70` | `detect-pdg-semantic.py:203` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.91
- metric_similarity: 0.905

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_length ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `main` |
| **File** | `detect-ast-similarity.py:70` | `detect-token-clones.py:210` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.91
- metric_similarity: 0.905

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_length ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `main` |
| **File** | `detect-ast-similarity.py:70` | `detect-signature-match.py:378` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.909
- metric_similarity: 0.906

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### fill ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `fill` | `_positive_int` |
| **File** | `lib/jsonstream.py:73` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.908 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.89
- metric_similarity: 0.935

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_strategy_results ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_strategy_results` | `_iter_records` |
| **File** | `merge-signals.py:171` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- metric_similarity: 0.921
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### iter_json_array ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_json_array` | `_iter_scored` |
| **File** | `lib/jsonstream.py:222` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.983
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### arity_match_score ↔ score_pair_tfidf

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `arity_match_score` | `score_pair_tfidf` |
| **File** | `detect-signature-match.py:158` | `detect-tfidf-index.py:121` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.982
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `load_strategy_results` |
| **File** | `detect-tfidf-index.py:156` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.982
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_function_name ↔ peek_ws_or_eof

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_function_name` | `peek_ws_or_eof` |
| **File** | `extract-functions-regex.py:212` | `lib/jsonstream.py:96` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.981
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_length ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `main` |
| **File** | `detect-ast-similarity.py:70` | `detect-fuzzy-names.py:338` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.909
- metric_similarity: 0.905

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _compute_pair_similarity ↔ generate_non_clone_pair

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_pair_similarity` | `generate_non_clone_pair` |
| **File** | `detect-metric-similarity.py:184` | `generate-corpus.py:207` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.908
- metric_similarity: 0.905

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _safe_divide ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_safe_divide` | `__init__` |
| **File** | `evaluate.py:119` | `lib/resource_policy.py:339` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.907 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.901
- metric_similarity: 0.915

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _normalized_distance ↔ hash_sequence

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_normalized_distance` | `hash_sequence` |
| **File** | `detect-metric-similarity.py:179` | `detect-token-clones.py:25` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- metric_similarity: 0.92
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### visit_arg ↔ visit_FunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `visit_FunctionDef` |
| **File** | `extract-functions-ast-py.py:59` | `extract-functions-ast-py.py:410` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.956
- metric_similarity: 0.965
- tfidf_index: 0.824

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### visit_arg ↔ _resolve_language

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `_resolve_language` |
| **File** | `extract-functions-ast-py.py:59` | `extract-functions-regex.py:130` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.906 from 3 strategies

**Detection Signals:**

- lsh_ast: 0.906
- metric_similarity: 0.918
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### cosine_similarity ↔ _cyclomatic_complexity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `cosine_similarity` | `_cyclomatic_complexity` |
| **File** | `detect-bag-of-ast.py:57` | `extract-functions-ast-py.py:143` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.98
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `kgrams` |
| **File** | `detect-token-clones.py:67` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.98
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_params ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_params` | `load_strategy_results` |
| **File** | `detect-signature-match.py:105` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.98
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `kgrams` |
| **File** | `detect-tfidf-index.py:156` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.98
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ _get_token_strings

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `_get_token_strings` |
| **File** | `detect-ast-similarity.py:63` | `detect-winnowing.py:114` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.979
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _open_cursor ↔ _is_crud_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_open_cursor` | `_is_crud_name` |
| **File** | `lib/jsonstream.py:217` | `merge-signals.py:44` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.915
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _get_token_strings ↔ _first_line_docstring

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `_first_line_docstring` |
| **File** | `detect-winnowing.py:114` | `extract-functions-ast-py.py:333` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.915
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _get_token_strings ↔ _summary_block

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `_summary_block` |
| **File** | `detect-winnowing.py:114` | `generate_report.py:71` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.915
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### ast_node_vector ↔ iter_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ast_node_vector` | `iter_array` |
| **File** | `detect-bag-of-ast.py:29` | `lib/jsonstream.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.906 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.904
- metric_similarity: 0.909

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `stable_hash` |
| **File** | `extract-functions-ast-py.py:537` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.979
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_function_name ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_function_name` | `skip_ws` |
| **File** | `extract-functions-regex.py:212` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.979
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### cosine_similarity ↔ arity_match_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `cosine_similarity` | `arity_match_score` |
| **File** | `detect-bag-of-ast.py:57` | `detect-signature-match.py:158` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.979
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ expand_abbreviations

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `expand_abbreviations` |
| **File** | `detect-ast-similarity.py:63` | `detect-fuzzy-names.py:179` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### embedding_cosine ↔ _cyclomatic_complexity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `embedding_cosine` | `_cyclomatic_complexity` |
| **File** | `detect-code-embedding.py:91` | `extract-functions-ast-py.py:143` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expand_abbreviations ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `kgrams` |
| **File** | `detect-fuzzy-names.py:179` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _discover_inputs ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_discover_inputs` | `_iter_scored` |
| **File** | `merge-signals.py:501` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expand_abbreviations ↔ tokenize_to_typed

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `tokenize_to_typed` |
| **File** | `detect-fuzzy-names.py:179` | `lib/common.py:110` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `validate_corpus` |
| **File** | `detect-signature-match.py:132` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.978
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _sample_table ↔ generate_summary

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_sample_table` | `generate_summary` |
| **File** | `lib/resource_policy.py:109` | `merge-signals.py:445` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ get_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `get_tokens` |
| **File** | `detect-ast-similarity.py:63` | `detect-tfidf-index.py:34` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_set ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_set` | `_iter_records` |
| **File** | `detect-lsh-ast.py:38` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ legacy

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `legacy` |
| **File** | `merge-signals.py:160` | `merge-signals.py:716` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.905 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.904
- metric_similarity: 0.906

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _summary_block ↔ _actionable_row

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_summary_block` | `_actionable_row` |
| **File** | `generate_report.py:71` | `generate_report.py:98` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 5 strategies

**Detection Signals:**

- bag_of_ast: 0.993
- code_embedding: 0.898
- signature_match: 0.82
- tfidf_index: 0.897
- winnowing: 0.9

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 5 independent detection strategies

---

### func_ref ↔ start

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `func_ref` | `start` |
| **File** | `lib/common.py:270` | `lib/resource_policy.py:343` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.99
- tfidf_index: 0.824

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_function_name ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_function_name` | `_strategy_name_from_path` |
| **File** | `extract-functions-regex.py:212` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### embedding_cosine ↔ param_name_similarity_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `embedding_cosine` | `param_name_similarity_score` |
| **File** | `detect-code-embedding.py:91` | `detect-signature-match.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### embedding_cosine ↔ jaccard

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `embedding_cosine` | `jaccard` |
| **File** | `detect-code-embedding.py:91` | `lib/common.py:194` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### cosine_similarity ↔ param_name_similarity_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `cosine_similarity` | `param_name_similarity_score` |
| **File** | `detect-bag-of-ast.py:57` | `detect-signature-match.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### peek_ws_or_eof ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `peek_ws_or_eof` | `_strategy_name_from_path` |
| **File** | `lib/jsonstream.py:96` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _discover_inputs ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_discover_inputs` | `_iter_records` |
| **File** | `merge-signals.py:501` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `iter_json_array` |
| **File** | `detect-signature-match.py:132` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.976
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `kgrams` |
| **File** | `detect-tfidf-index.py:34` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.976
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ tokenize

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `tokenize` |
| **File** | `detect-tfidf-index.py:156` | `lib/common.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.976
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_jsonl ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_jsonl` | `_iter_scored` |
| **File** | `lib/jsonstream.py:301` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.976
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### winnow ↔ suppress_noise_patterns

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `winnow` | `suppress_noise_patterns` |
| **File** | `detect-winnowing.py:65` | `merge-signals.py:88` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.976
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ _discover_inputs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `_discover_inputs` |
| **File** | `detect-winnowing.py:48` | `merge-signals.py:501` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.976
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ get_token_set

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `get_token_set` |
| **File** | `detect-ast-similarity.py:63` | `detect-lsh-ast.py:38` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_signature_duplicates ↔ _tokenize_core

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_signature_duplicates` | `_tokenize_core` |
| **File** | `detect-signature-match.py:329` | `lib/common.py:134` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### stable_hash ↔ atomic_write_text

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `stable_hash` | `atomic_write_text` |
| **File** | `lib/common.py:15` | `lib/jsonstream.py:344` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `_iter_scored` |
| **File** | `detect-signature-match.py:132` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### tokenize ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize` | `iter_json_array` |
| **File** | `lib/common.py:84` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### visit_arg ↔ visit_ClassDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `visit_ClassDef` |
| **File** | `extract-functions-ast-py.py:59` | `extract-functions-ast-py.py:423` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- tfidf_index: 0.849

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ fill

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `fill` |
| **File** | `detect-token-clones.py:67` | `lib/jsonstream.py:73` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.9
- metric_similarity: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _unparse_annotation ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_unparse_annotation` | `_positive_int` |
| **File** | `extract-functions-ast-py.py:168` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.879
- metric_similarity: 0.943

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _unparse_default ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_unparse_default` | `_positive_int` |
| **File** | `extract-functions-ast-py.py:178` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.904 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.879
- metric_similarity: 0.943

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### levenshtein_score ↔ token_jaccard_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `levenshtein_score` | `token_jaccard_score` |
| **File** | `detect-fuzzy-names.py:187` | `detect-fuzzy-names.py:192` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.958
- metric_similarity: 0.928
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### _func_to_spec ↔ _medium_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_func_to_spec` | `_medium_entry` |
| **File** | `evaluate.py:31` | `generate_report.py:132` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.918
- signature_match: 0.82
- tfidf_index: 0.956

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### visit_alias ↔ expect

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_alias` | `expect` |
| **File** | `extract-functions-ast-py.py:86` | `lib/jsonstream.py:109` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.903 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.895
- metric_similarity: 0.924
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### winnow ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `winnow` | `iter_json_array` |
| **File** | `detect-winnowing.py:65` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `stable_hash` |
| **File** | `detect-metric-similarity.py:332` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_values ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_values` | `kgrams` |
| **File** | `detect-ast-similarity.py:33` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_for_language ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_for_language` | `iter_object_member_array` |
| **File** | `extract-functions-regex.py:260` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.975
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### skip_ws ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `skip_ws` | `_strategy_name_from_path` |
| **File** | `lib/jsonstream.py:83` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _param_names_from_template ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_param_names_from_template` | `load_strategy_results` |
| **File** | `generate-corpus.py:93` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_strategy_results ↔ merge_pair_signals

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_strategy_results` | `merge_pair_signals` |
| **File** | `merge-signals.py:171` | `merge-signals.py:185` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ merge_pair_signals

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `merge_pair_signals` |
| **File** | `detect-winnowing.py:48` | `merge-signals.py:185` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _cyclomatic_complexity ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_cyclomatic_complexity` | `stable_hash` |
| **File** | `extract-functions-ast-py.py:143` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.974
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `iter_jsonl` |
| **File** | `detect-signature-match.py:132` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### func_ref ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `func_ref` | `_positive_int` |
| **File** | `lib/common.py:270` | `merge-signals.py:752` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.906
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### build_embedding ↔ _summary_block

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `build_embedding` | `_summary_block` |
| **File** | `detect-code-embedding.py:70` | `generate_report.py:71` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.89
- metric_similarity: 0.923

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### make_pair_key ↔ start

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `start` |
| **File** | `evaluate.py:26` | `lib/resource_policy.py:207` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.903 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.879
- metric_similarity: 0.941

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ note_phase

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `note_phase` |
| **File** | `extract-functions-ast-py.py:354` | `lib/resource_policy.py:364` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ _build_params

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `_build_params` |
| **File** | `detect-token-clones.py:78` | `extract-functions-ast-py.py:188` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _param_names_from_template ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_param_names_from_template` | `descendants_from_table` |
| **File** | `generate-corpus.py:93` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### validate_corpus ↔ suppress_noise_patterns

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `validate_corpus` | `suppress_noise_patterns` |
| **File** | `generate-corpus.py:316` | `merge-signals.py:88` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### skip_value ↔ _loop

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `skip_value` | `_loop` |
| **File** | `lib/jsonstream.py:171` | `lib/resource_policy.py:220` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_jsonl ↔ _discover_inputs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_jsonl` | `_discover_inputs` |
| **File** | `lib/jsonstream.py:301` | `merge-signals.py:501` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.973
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `_strategy_name_from_path` |
| **File** | `detect-signature-match.py:147` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### generate_type2_pair ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `generate_type2_pair` | `_iter_scored` |
| **File** | `generate-corpus.py:119` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### descendants_from_table ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `descendants_from_table` | `load_strategy_results` |
| **File** | `lib/resource_policy.py:126` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_params ↔ suppress_noise_patterns

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_params` | `suppress_noise_patterns` |
| **File** | `extract-functions-ast-py.py:188` | `merge-signals.py:88` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get_token_strings ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `_iter_records` |
| **File** | `detect-winnowing.py:114` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_jsonl ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_jsonl` | `_iter_records` |
| **File** | `lib/jsonstream.py:301` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ _decorator_names

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `_decorator_names` |
| **File** | `detect-token-clones.py:67` | `extract-functions-ast-py.py:278` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.972
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get_token_strings ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `descendants_from_table` |
| **File** | `detect-winnowing.py:114` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### retrieve_candidates ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `retrieve_candidates` | `main` |
| **File** | `detect-tfidf-index.py:79` | `extract-functions-regex.py:328` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.905
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### expand_abbreviations ↔ _is_crud_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `_is_crud_name` |
| **File** | `detect-fuzzy-names.py:179` | `merge-signals.py:44` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.902 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.894
- metric_similarity: 0.916

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_set ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_set` | `_iter_scored` |
| **File** | `detect-lsh-ast.py:38` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get_token_strings ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `_iter_scored` |
| **File** | `detect-winnowing.py:114` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `iter_jsonl` |
| **File** | `detect-tfidf-index.py:34` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `validate_corpus` |
| **File** | `detect-tfidf-index.py:156` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### segment_into_blocks ↔ get_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `segment_into_blocks` | `get_tokens` |
| **File** | `detect-pdg-semantic.py:52` | `detect-tfidf-index.py:34` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### arity_match_score ↔ param_name_similarity_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `arity_match_score` | `param_name_similarity_score` |
| **File** | `detect-signature-match.py:158` | `detect-signature-match.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ _get_token_strings

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `_get_token_strings` |
| **File** | `detect-token-clones.py:78` | `detect-winnowing.py:114` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `skip_ws` |
| **File** | `extract-functions-ast-py.py:246` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _param_names_from_template ↔ tokenize_to_typed

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_param_names_from_template` | `tokenize_to_typed` |
| **File** | `generate-corpus.py:93` | `lib/common.py:110` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_set ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_set` | `kgrams` |
| **File** | `detect-lsh-ast.py:38` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### segment_into_blocks ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `segment_into_blocks` | `kgrams` |
| **File** | `detect-pdg-semantic.py:52` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _placeholder ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_placeholder` | `skip_ws` |
| **File** | `extract-functions-ast-py.py:48` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ normalize_simple_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `normalize_simple_tokens` |
| **File** | `detect-tfidf-index.py:34` | `detect-token-clones.py:78` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `load_strategy_results` |
| **File** | `detect-token-clones.py:78` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.971
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### segment_into_blocks ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `segment_into_blocks` | `load_strategy_results` |
| **File** | `detect-pdg-semantic.py:52` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `_iter_scored` |
| **File** | `detect-tfidf-index.py:34` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `_strategy_name_from_path` |
| **File** | `extract-functions-ast-py.py:246` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `_iter_records` |
| **File** | `detect-tfidf-index.py:34` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get_token_strings ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `validate_corpus` |
| **File** | `detect-winnowing.py:114` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ _param_names_from_template

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `_param_names_from_template` |
| **File** | `detect-signature-match.py:132` | `generate-corpus.py:93` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_detected_pairs ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_detected_pairs` | `iter_jsonl` |
| **File** | `evaluate.py:84` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### generate_type1_pair ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `generate_type1_pair` | `_iter_scored` |
| **File** | `generate-corpus.py:99` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### validate_corpus ↔ _tokenize_core

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `validate_corpus` | `_tokenize_core` |
| **File** | `generate-corpus.py:316` | `lib/common.py:134` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _count_table ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_count_table` | `_strategy_name_from_path` |
| **File** | `generate_report.py:89` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `stable_hash` |
| **File** | `generate_report.py:296` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_values ↔ normalize_simple_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_values` | `normalize_simple_tokens` |
| **File** | `detect-ast-similarity.py:33` | `detect-token-clones.py:78` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### abbreviation_boost ↔ arity_match_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `abbreviation_boost` | `arity_match_score` |
| **File** | `detect-fuzzy-names.py:238` | `detect-signature-match.py:158` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_signature ↔ peek_ws_or_eof

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_signature` | `peek_ws_or_eof` |
| **File** | `extract-functions-ast-py.py:246` | `lib/jsonstream.py:96` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.97
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _decorator_name ↔ _decode_next

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_decorator_name` | `_decode_next` |
| **File** | `extract-functions-ast-py.py:270` | `lib/jsonstream.py:49` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- lsh_ast: 0.836

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ _class_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `_class_name` |
| **File** | `extract-functions-ast-py.py:43` | `extract-functions-ast-py.py:363` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.901
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _safe_divide ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_safe_divide` | `__init__` |
| **File** | `evaluate.py:119` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.891
- metric_similarity: 0.917

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _placeholder ↔ stop

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_placeholder` | `stop` |
| **File** | `extract-functions-ast-py.py:48` | `lib/resource_policy.py:211` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.901 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.888
- metric_similarity: 0.922

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_detected_pairs ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_detected_pairs` | `iter_object_member_array` |
| **File** | `evaluate.py:84` | `lib/jsonstream.py:246` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.9 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### get_token_values ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_values` | `iter_object_member_array` |
| **File** | `detect-ast-similarity.py:33` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- metric_similarity: 0.902
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### visit_arg ↔ visit_AsyncFunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `visit_arg` | `visit_AsyncFunctionDef` |
| **File** | `extract-functions-ast-py.py:59` | `extract-functions-ast-py.py:417` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.956
- metric_similarity: 0.941
- tfidf_index: 0.824

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### _func_to_spec ↔ _low_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_func_to_spec` | `_low_entry` |
| **File** | `evaluate.py:31` | `generate_report.py:147` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.914
- signature_match: 0.82
- tfidf_index: 0.95

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### embedding_cosine ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `embedding_cosine` | `stable_hash` |
| **File** | `detect-code-embedding.py:91` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.969
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `iter_json_array` |
| **File** | `detect-token-clones.py:67` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.969
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ compute_fingerprint

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `compute_fingerprint` |
| **File** | `detect-winnowing.py:48` | `detect-winnowing.py:133` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.969
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_params ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_params` | `iter_json_array` |
| **File** | `extract-functions-ast-py.py:188` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.969
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_pdg_fingerprint ↔ normalize_simple_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_pdg_fingerprint` | `normalize_simple_tokens` |
| **File** | `detect-pdg-semantic.py:84` | `detect-token-clones.py:78` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### segment_into_blocks ↔ _get_token_strings

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `segment_into_blocks` | `_get_token_strings` |
| **File** | `detect-pdg-semantic.py:52` | `detect-winnowing.py:114` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _extract_token_sequence ↔ _decorator_names

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_extract_token_sequence` | `_decorator_names` |
| **File** | `extract-functions-ast-py.py:109` | `extract-functions-ast-py.py:278` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### tokenize ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize` | `load_strategy_results` |
| **File** | `lib/common.py:84` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `iter_object_member_array` |
| **File** | `detect-tfidf-index.py:156` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _decorator_names ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_decorator_names` | `descendants_from_table` |
| **File** | `extract-functions-ast-py.py:278` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get_token_strings ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get_token_strings` | `iter_object_member_array` |
| **File** | `detect-winnowing.py:114` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### skip_value ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `skip_value` | `__init__` |
| **File** | `lib/jsonstream.py:171` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expand_abbreviations ↔ _is_nested

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `_is_nested` |
| **File** | `detect-fuzzy-names.py:179` | `extract-functions-ast-py.py:370` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.893
- metric_similarity: 0.911

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ _body_lines

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `_body_lines` |
| **File** | `detect-ast-similarity.py:63` | `merge-signals.py:49` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.9 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.887
- metric_similarity: 0.919

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_object_members ↔ convert_llm_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_object_members` | `convert_llm_results` |
| **File** | `lib/jsonstream.py:187` | `merge-signals.py:1050` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.899 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### make_pair_key ↔ _num_or_zero

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `_num_or_zero` |
| **File** | `evaluate.py:26` | `generate_report.py:58` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.947
- metric_similarity: 0.928
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### get_param_count ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `load_strategy_results` |
| **File** | `detect-signature-match.py:132` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `validate_corpus` |
| **File** | `detect-tfidf-index.py:34` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_function_name ↔ _s

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_function_name` | `_s` |
| **File** | `extract-functions-regex.py:212` | `generate_report.py:37` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _param_names_from_template ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_param_names_from_template` | `_iter_scored` |
| **File** | `generate-corpus.py:93` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _signals_lines ↔ _strategy_name_from_path

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_signals_lines` | `_strategy_name_from_path` |
| **File** | `generate_report.py:105` | `merge-signals.py:492` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_fuzzy_duplicates ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_fuzzy_duplicates` | `iter_object_member_array` |
| **File** | `detect-fuzzy-names.py:274` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_params ↔ _tokenize_core

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_params` | `_tokenize_core` |
| **File** | `extract-functions-ast-py.py:188` | `lib/common.py:134` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_strategy_results ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_strategy_results` | `_iter_scored` |
| **File** | `merge-signals.py:171` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.968
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_pdg_fingerprint ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_pdg_fingerprint` | `iter_object_member_array` |
| **File** | `detect-pdg-semantic.py:84` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_ast_tokens ↔ render

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_ast_tokens` | `render` |
| **File** | `detect-token-clones.py:30` | `generate_report.py:197` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### cosine_similarity ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `cosine_similarity` | `stable_hash` |
| **File** | `detect-bag-of-ast.py:57` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `_iter_records` |
| **File** | `detect-token-clones.py:78` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `load_strategy_results` |
| **File** | `detect-winnowing.py:48` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_fingerprint ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_fingerprint` | `_iter_scored` |
| **File** | `detect-winnowing.py:133` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `load_strategy_results` |
| **File** | `detect-ast-similarity.py:63` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `iter_object_member_array` |
| **File** | `detect-signature-match.py:132` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_fingerprint ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_fingerprint` | `descendants_from_table` |
| **File** | `detect-winnowing.py:133` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_fingerprint ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_fingerprint` | `load_strategy_results` |
| **File** | `detect-winnowing.py:133` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_fingerprint ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_fingerprint` | `iter_jsonl` |
| **File** | `detect-winnowing.py:133` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### abbreviation_boost ↔ _cyclomatic_complexity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `abbreviation_boost` | `_cyclomatic_complexity` |
| **File** | `detect-fuzzy-names.py:238` | `extract-functions-ast-py.py:143` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _iter_records ↔ _open_scratch_db

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_iter_records` | `_open_scratch_db` |
| **File** | `merge-signals.py:524` | `merge-signals.py:554` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.967
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_bag_of_ast_duplicates ↔ load_detected_pairs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_bag_of_ast_duplicates` | `load_detected_pairs` |
| **File** | `detect-bag-of-ast.py:87` | `evaluate.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_pdg_duplicates ↔ load_detected_pairs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_pdg_duplicates` | `load_detected_pairs` |
| **File** | `detect-pdg-semantic.py:138` | `evaluate.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_object_member_array ↔ suppress_noise_patterns

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_object_member_array` | `suppress_noise_patterns` |
| **File** | `lib/jsonstream.py:246` | `merge-signals.py:88` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### assert_only_trailing_ws ↔ write

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `assert_only_trailing_ws` | `write` |
| **File** | `lib/jsonstream.py:180` | `lib/resource_policy.py:404` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `kgrams` |
| **File** | `detect-token-clones.py:78` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ _count_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `_count_table` |
| **File** | `detect-signature-match.py:147` | `generate_report.py:89` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `descendants_from_table` |
| **File** | `detect-ast-similarity.py:63` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_ast_similarity ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_ast_similarity` | `validate_corpus` |
| **File** | `detect-ast-similarity.py:112` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_embedding_duplicates ↔ load_detected_pairs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_embedding_duplicates` | `load_detected_pairs` |
| **File** | `detect-code-embedding.py:126` | `evaluate.py:84` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### elapsed ↔ _empty_summary

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `elapsed` | `_empty_summary` |
| **File** | `lib/resource_policy.py:216` | `merge-signals.py:689` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.899 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.896
- metric_similarity: 0.903

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _summary_block ↔ _medium_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_summary_block` | `_medium_entry` |
| **File** | `generate_report.py:71` | `generate_report.py:132` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 4 strategies

**Detection Signals:**

- bag_of_ast: 0.995
- code_embedding: 0.877
- signature_match: 0.82
- tfidf_index: 0.89

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 4 independent detection strategies

---

### _low_entry ↔ func_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_low_entry` | `func_key` |
| **File** | `generate_report.py:147` | `lib/common.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.947
- signature_match: 0.82
- tfidf_index: 0.914

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### _signals_lines ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_signals_lines` | `skip_ws` |
| **File** | `generate_report.py:105` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### param_name_similarity_score ↔ _cyclomatic_complexity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `param_name_similarity_score` | `_cyclomatic_complexity` |
| **File** | `detect-signature-match.py:261` | `extract-functions-ast-py.py:143` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.966
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### arity_match_score ↔ fingerprint_similarity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `arity_match_score` | `fingerprint_similarity` |
| **File** | `detect-signature-match.py:158` | `detect-winnowing.py:152` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _cyclomatic_complexity ↔ atomic_write_text

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_cyclomatic_complexity` | `atomic_write_text` |
| **File** | `extract-functions-ast-py.py:143` | `lib/jsonstream.py:344` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_json_array ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_json_array` | `descendants_from_table` |
| **File** | `lib/jsonstream.py:222` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expand_abbreviations ↔ normalize_simple_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `normalize_simple_tokens` |
| **File** | `detect-fuzzy-names.py:179` | `detect-token-clones.py:78` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ walk_and_extract

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `walk_and_extract` |
| **File** | `detect-token-clones.py:78` | `extract-functions-ast-py.py:459` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _extract_metrics ↔ generate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_extract_metrics` | `generate_corpus` |
| **File** | `detect-metric-similarity.py:110` | `generate-corpus.py:237` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_params ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_params` | `_iter_records` |
| **File** | `detect-signature-match.py:105` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### winnow ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `winnow` | `iter_jsonl` |
| **File** | `detect-winnowing.py:65` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _build_params ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_build_params` | `iter_jsonl` |
| **File** | `extract-functions-ast-py.py:188` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _positive_int ↔ _refusal

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_positive_int` | `_refusal` |
| **File** | `merge-signals.py:752` | `merge-signals.py:804` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `_iter_records` |
| **File** | `detect-token-clones.py:67` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_params ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_params` | `kgrams` |
| **File** | `detect-signature-match.py:105` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_jsonl ↔ merge_pair_signals

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_jsonl` | `merge_pair_signals` |
| **File** | `lib/jsonstream.py:301` | `merge-signals.py:185` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _placeholder ↔ peek_ws_or_eof

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_placeholder` | `peek_ws_or_eof` |
| **File** | `extract-functions-ast-py.py:48` | `lib/jsonstream.py:96` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.965
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _extract_metrics ↔ generate_summary

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_extract_metrics` | `generate_summary` |
| **File** | `detect-metric-similarity.py:110` | `merge-signals.py:445` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_params ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_params` | `iter_json_array` |
| **File** | `detect-signature-match.py:105` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_ground_truth ↔ _compute_metrics

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_ground_truth` | `_compute_metrics` |
| **File** | `evaluate.py:36` | `evaluate.py:124` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ peek_ws_or_eof

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `peek_ws_or_eof` |
| **File** | `detect-signature-match.py:147` | `lib/jsonstream.py:96` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_length ↔ type_pattern_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `type_pattern_score` |
| **File** | `detect-ast-similarity.py:70` | `detect-signature-match.py:185` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### segment_into_blocks ↔ compute_fingerprint

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `segment_into_blocks` | `compute_fingerprint` |
| **File** | `detect-pdg-semantic.py:52` | `detect-winnowing.py:133` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### fingerprint_similarity ↔ tree_rss_bytes_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `fingerprint_similarity` | `tree_rss_bytes_from_table` |
| **File** | `detect-winnowing.py:152` | `lib/resource_policy.py:144` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_array ↔ _loop

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_array` | `_loop` |
| **File** | `lib/jsonstream.py:144` | `lib/resource_policy.py:220` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.895
- metric_similarity: 0.902

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _compute_metrics ↔ _actionable_row

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_compute_metrics` | `_actionable_row` |
| **File** | `evaluate.py:124` | `generate_report.py:98` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.898 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.895
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 2 independent strategies

---

### _summary_block ↔ _high_entry

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_summary_block` | `_high_entry` |
| **File** | `generate_report.py:71` | `generate_report.py:112` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 4 strategies

**Detection Signals:**

- bag_of_ast: 0.995
- code_embedding: 0.873
- signature_match: 0.82
- tfidf_index: 0.891

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 4 independent detection strategies

---

### _safe_divide ↔ note_error

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_safe_divide` | `note_error` |
| **File** | `evaluate.py:119` | `lib/resource_policy.py:367` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.897 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.886
- metric_similarity: 0.908
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 3 independent strategies

---

### make_pair_key ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `make_pair_key` | `__init__` |
| **File** | `merge-signals.py:160` | `merge-signals.py:486` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.872
- lsh_ast: 0.875
- tfidf_index: 0.941

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### detect_signature_duplicates ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_signature_duplicates` | `iter_object_member_array` |
| **File** | `detect-signature-match.py:329` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ extract_function_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `extract_function_name` |
| **File** | `detect-signature-match.py:147` | `extract-functions-regex.py:212` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `iter_json_array` |
| **File** | `detect-token-clones.py:78` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_token_set ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_token_set` | `iter_object_member_array` |
| **File** | `detect-lsh-ast.py:38` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_tokens ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_tokens` | `iter_object_member_array` |
| **File** | `detect-tfidf-index.py:34` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ _process_function

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_process_function` |
| **File** | `detect-fuzzy-names.py:338` | `extract-functions-ast-py.py:376` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ _process_function

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_process_function` |
| **File** | `detect-signature-match.py:378` | `extract-functions-ast-py.py:376` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.964
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_params ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_params` | `iter_jsonl` |
| **File** | `detect-signature-match.py:105` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### abbreviation_boost ↔ stable_hash

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `abbreviation_boost` | `stable_hash` |
| **File** | `detect-fuzzy-names.py:238` | `lib/common.py:15` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### load_strategy_results ↔ _open_scratch_db

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `load_strategy_results` | `_open_scratch_db` |
| **File** | `merge-signals.py:171` | `merge-signals.py:554` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_type ↔ _build_signature

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_type` | `_build_signature` |
| **File** | `detect-signature-match.py:71` | `extract-functions-ast-py.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_object_member_array ↔ _discover_inputs

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_object_member_array` | `_discover_inputs` |
| **File** | `lib/jsonstream.py:246` | `merge-signals.py:501` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_winnowing_duplicates ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_winnowing_duplicates` | `iter_object_member_array` |
| **File** | `detect-winnowing.py:172` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ descendants_from_table

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `descendants_from_table` |
| **File** | `detect-winnowing.py:48` | `lib/resource_policy.py:126` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_length ↔ param_name_similarity_score

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_length` | `param_name_similarity_score` |
| **File** | `detect-ast-similarity.py:70` | `detect-signature-match.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ walk_and_extract

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `walk_and_extract` |
| **File** | `detect-winnowing.py:48` | `extract-functions-ast-py.py:459` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ get_param_count

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `get_param_count` |
| **File** | `detect-ast-similarity.py:63` | `detect-signature-match.py:132` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### extract_ast_paths ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `extract_ast_paths` | `iter_object_member_array` |
| **File** | `detect-code-embedding.py:30` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_metric_clones ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_metric_clones` | `iter_object_member_array` |
| **File** | `detect-metric-similarity.py:221` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### validate_corpus ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `validate_corpus` | `_iter_records` |
| **File** | `generate-corpus.py:316` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _s ↔ peek_ws_or_eof

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_s` | `peek_ws_or_eof` |
| **File** | `generate_report.py:37` | `lib/jsonstream.py:96` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.963
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_ast_similarity ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_ast_similarity` | `iter_object_member_array` |
| **File** | `detect-ast-similarity.py:112` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_metric_clones ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_metric_clones` | `validate_corpus` |
| **File** | `detect-metric-similarity.py:221` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_tfidf_duplicates ↔ _iter_records

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_tfidf_duplicates` | `_iter_records` |
| **File** | `detect-tfidf-index.py:156` | `merge-signals.py:524` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _estimate_nesting_depth ↔ normalize_ast_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_estimate_nesting_depth` | `normalize_ast_tokens` |
| **File** | `detect-metric-similarity.py:55` | `detect-token-clones.py:30` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.895
- metric_similarity: 0.901

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### token_jaccard_score ↔ visit_AsyncFunctionDef

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `token_jaccard_score` | `visit_AsyncFunctionDef` |
| **File** | `detect-fuzzy-names.py:192` | `extract-functions-ast-py.py:417` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.875
- metric_similarity: 0.931

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _safe_divide ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_safe_divide` | `__init__` |
| **File** | `evaluate.py:119` | `extract-functions-ast-py.py:43` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.897 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.866
- metric_similarity: 0.945

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _medium_entry ↔ func_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_medium_entry` | `func_key` |
| **File** | `generate_report.py:132` | `lib/common.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.943
- signature_match: 0.82
- tfidf_index: 0.912

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### get_param_count ↔ normalize_simple_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `normalize_simple_tokens` |
| **File** | `detect-signature-match.py:132` | `detect-token-clones.py:78` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_embedding_duplicates ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_embedding_duplicates` | `validate_corpus` |
| **File** | `detect-code-embedding.py:126` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `skip_ws` |
| **File** | `detect-signature-match.py:147` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _cyclomatic_complexity ↔ main

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_cyclomatic_complexity` | `main` |
| **File** | `extract-functions-ast-py.py:143` | `extract-functions-ast-py.py:537` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### raw_token_values ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `raw_token_values` | `_iter_scored` |
| **File** | `detect-token-clones.py:67` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### compute_fingerprint ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `compute_fingerprint` | `iter_object_member_array` |
| **File** | `detect-winnowing.py:133` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _process_function ↔ __init__

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_process_function` | `__init__` |
| **File** | `extract-functions-ast-py.py:376` | `lib/jsonstream.py:61` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _s ↔ skip_ws

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_s` | `skip_ws` |
| **File** | `generate_report.py:37` | `lib/jsonstream.py:83` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_return_type ↔ make_pair_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_return_type` | `make_pair_key` |
| **File** | `detect-signature-match.py:147` | `evaluate.py:26` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.962
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expand_abbreviations ↔ tokenize_to_strings

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `tokenize_to_strings` |
| **File** | `detect-fuzzy-names.py:179` | `lib/common.py:125` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### expand_abbreviations ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `iter_json_array` |
| **File** | `detect-fuzzy-names.py:179` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _tokenize_core ↔ iter_jsonl

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_tokenize_core` | `iter_jsonl` |
| **File** | `lib/common.py:134` | `lib/jsonstream.py:301` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ iter_json_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `iter_json_array` |
| **File** | `detect-winnowing.py:48` | `lib/jsonstream.py:222` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### ngrams ↔ normalize_simple_tokens

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `ngrams` | `normalize_simple_tokens` |
| **File** | `detect-ast-similarity.py:63` | `detect-token-clones.py:78` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### get_param_count ↔ kgrams

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `get_param_count` | `kgrams` |
| **File** | `detect-signature-match.py:132` | `detect-winnowing.py:48` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _tokenize_core ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_tokenize_core` | `iter_object_member_array` |
| **File** | `lib/common.py:134` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### lcs_similarity ↔ _cyclomatic_complexity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `lcs_similarity` | `_cyclomatic_complexity` |
| **File** | `detect-ast-similarity.py:100` | `extract-functions-ast-py.py:143` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_bag_of_ast_duplicates ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_bag_of_ast_duplicates` | `validate_corpus` |
| **File** | `detect-bag-of-ast.py:87` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_pdg_duplicates ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_pdg_duplicates` | `validate_corpus` |
| **File** | `detect-pdg-semantic.py:138` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_ast_tokens ↔ load_strategy_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_ast_tokens` | `load_strategy_results` |
| **File** | `detect-token-clones.py:30` | `merge-signals.py:171` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _iter_records ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_iter_records` | `_iter_scored` |
| **File** | `merge-signals.py:524` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### arity_match_score ↔ _cyclomatic_complexity

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `arity_match_score` | `_cyclomatic_complexity` |
| **File** | `detect-signature-match.py:158` | `extract-functions-ast-py.py:143` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### kgrams ↔ generate_type4_pair

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `kgrams` | `generate_type4_pair` |
| **File** | `detect-winnowing.py:48` | `generate-corpus.py:177` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### detect_winnowing_duplicates ↔ validate_corpus

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `detect_winnowing_duplicates` | `validate_corpus` |
| **File** | `detect-winnowing.py:172` | `generate-corpus.py:316` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### __init__ ↔ _loop

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `__init__` | `_loop` |
| **File** | `lib/resource_policy.py:180` | `lib/resource_policy.py:220` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### tokenize_to_strings ↔ _open_cursor

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `tokenize_to_strings` | `_open_cursor` |
| **File** | `lib/common.py:125` | `lib/jsonstream.py:217` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- tfidf_index: 0.835

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### abbreviation_boost ↔ _positive_int

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `abbreviation_boost` | `_positive_int` |
| **File** | `detect-fuzzy-names.py:238` | `merge-signals.py:752` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_ast_tokens ↔ _get_token_strings

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_ast_tokens` | `_get_token_strings` |
| **File** | `detect-token-clones.py:30` | `detect-winnowing.py:114` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.961
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### normalize_simple_tokens ↔ _iter_scored

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `normalize_simple_tokens` | `_iter_scored` |
| **File** | `detect-token-clones.py:78` | `merge-signals.py:681` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### winnow ↔ iter_object_member_array

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `winnow` | `iter_object_member_array` |
| **File** | `detect-winnowing.py:65` | `lib/jsonstream.py:246` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### embedding_cosine ↔ overlap_coefficient

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `embedding_cosine` | `overlap_coefficient` |
| **File** | `detect-code-embedding.py:91` | `lib/common.py:214` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.896 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_array ↔ iter_object_members

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_array` | `iter_object_members` |
| **File** | `lib/jsonstream.py:144` | `lib/jsonstream.py:187` |

**Clone Type:** Type 3 (near-miss clone)

**Composite Score:** 0.895 from 7 strategies

**Detection Signals:**

- ast_similarity: 0.757
- bag_of_ast: 0.994
- code_embedding: 0.913
- lsh_ast: 0.945
- signature_match: 0.82
- tfidf_index: 0.974
- winnowing: 0.875

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 7 independent detection strategies

---

### expand_abbreviations ↔ _decorator_names

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `expand_abbreviations` | `_decorator_names` |
| **File** | `detect-fuzzy-names.py:179` | `extract-functions-ast-py.py:278` |

**Clone Type:** Type 2 (renamed clone)

**Composite Score:** 0.895 from 6 strategies

**Detection Signals:**

- bag_of_ast: 0.977
- lsh_ast: 0.844
- metric_similarity: 1.0
- signature_match: 0.82
- tfidf_index: 0.855
- token_clone: 0.9

**Recommendation:** CONSOLIDATE (immediate) — Structurally identical code detected by 6 independent strategies

---

### _high_entry ↔ func_key

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_high_entry` | `func_key` |
| **File** | `generate_report.py:112` | `lib/common.py:261` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.942
- signature_match: 0.82
- tfidf_index: 0.91

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### _should_skip_test_file ↔ _is_crud_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_should_skip_test_file` | `_is_crud_name` |
| **File** | `extract-functions-regex.py:142` | `merge-signals.py:44` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 3 strategies

**Detection Signals:**

- bag_of_ast: 0.938
- signature_match: 0.82
- tfidf_index: 0.914

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 3 independent detection strategies

---

### main ↔ _process_function

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_process_function` |
| **File** | `detect-bag-of-ast.py:149` | `extract-functions-ast-py.py:376` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ _process_function

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_process_function` |
| **File** | `detect-pdg-semantic.py:203` | `extract-functions-ast-py.py:376` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### main ↔ _process_function

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `main` | `_process_function` |
| **File** | `detect-token-clones.py:210` | `extract-functions-ast-py.py:376` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _get ↔ load_object_member

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_get` | `load_object_member` |
| **File** | `generate_report.py:50` | `lib/jsonstream.py:278` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### iter_array ↔ convert_llm_results

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `iter_array` | `convert_llm_results` |
| **File** | `lib/jsonstream.py:144` | `merge-signals.py:1050` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _cyclomatic_complexity ↔ jaccard

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_cyclomatic_complexity` | `jaccard` |
| **File** | `extract-functions-ast-py.py:143` | `lib/common.py:194` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---

### _is_test_file ↔ _is_crud_name

| | Function A | Function B |
|---|-----------|------------|
| **Name** | `_is_test_file` | `_is_crud_name` |
| **File** | `extract-functions-ast-py.py:444` | `merge-signals.py:44` |

**Clone Type:** Type 4 (semantic clone)

**Composite Score:** 0.895 from 2 strategies

**Detection Signals:**

- bag_of_ast: 0.96
- signature_match: 0.82

**Recommendation:** CONSOLIDATE (high) — Strong duplicate signal from 2 independent detection strategies

---


_2873 additional HIGH pair(s) omitted (cap 500)_

## MEDIUM Confidence Duplicates

> These pairs show moderate duplicate signals. Investigate before consolidating.

### abbreviation_boost ↔ printUsage

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ getDocstring

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ printUsage

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ getDocstring

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ extractParams

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `extractParams` in `extract-functions-ast-ts.mjs:215`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### printUsage ↔ getDocstring

- **A:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **B:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### isTestFile ↔ _count_table

- **A:** `isTestFile` in `extract-functions-ast-ts.mjs:74`
- **B:** `_count_table` in `generate_report.py:89`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### isTestFile ↔ _refusal

- **A:** `isTestFile` in `extract-functions-ast-ts.mjs:74`
- **B:** `_refusal` in `merge-signals.py:804`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### computeTokenSequence ↔ overlap_coefficient

- **A:** `computeTokenSequence` in `extract-functions-ast-ts.mjs:160`
- **B:** `overlap_coefficient` in `lib/common.py:214`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### getDecorators ↔ overlap_coefficient

- **A:** `getDecorators` in `extract-functions-ast-ts.mjs:176`
- **B:** `overlap_coefficient` in `lib/common.py:214`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### getBodyLines ↔ _iter_records

- **A:** `getBodyLines` in `extract-functions-ast-ts.mjs:335`
- **B:** `_iter_records` in `merge-signals.py:524`
- **Score:** 1.0 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=1.0
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _func_to_spec ↔ _open_cursor

- **A:** `_func_to_spec` in `evaluate.py:31`
- **B:** `_open_cursor` in `lib/jsonstream.py:217`
- **Score:** 0.996 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.996
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ tokenize

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.991 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.991
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### evaluate ↔ main

- **A:** `evaluate` in `evaluate.py:139`
- **B:** `main` in `extract-functions-ast-ts.mjs:480`
- **Score:** 0.989 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.989
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ compute_pdg_fingerprint

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `compute_pdg_fingerprint` in `detect-pdg-semantic.py:84`
- **Score:** 0.988 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.988
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _ingest

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_ingest` in `merge-signals.py:582`
- **Score:** 0.987 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.987
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _score_all

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_score_all` in `merge-signals.py:635`
- **Score:** 0.987 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.987
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ lcs_similarity

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `lcs_similarity` in `detect-ast-similarity.py:100`
- **Score:** 0.986 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.986
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ getReturnType

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `getReturnType` in `extract-functions-ast-ts.mjs:232`
- **Score:** 0.986 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.986
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ getReturnType

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `getReturnType` in `extract-functions-ast-ts.mjs:232`
- **Score:** 0.986 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.986
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### printUsage ↔ getReturnType

- **A:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **B:** `getReturnType` in `extract-functions-ast-ts.mjs:232`
- **Score:** 0.986 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.986
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### getDocstring ↔ getReturnType

- **A:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **B:** `getReturnType` in `extract-functions-ast-ts.mjs:232`
- **Score:** 0.986 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.986
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ suppress_noise_patterns

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `suppress_noise_patterns` in `merge-signals.py:88`
- **Score:** 0.985 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.985
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ extract_for_language

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `extract_for_language` in `extract-functions-regex.py:260`
- **Score:** 0.985 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.985
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ skip_value

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `skip_value` in `lib/jsonstream.py:171`
- **Score:** 0.985 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.985
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ embedding_cosine

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `embedding_cosine` in `detect-code-embedding.py:91`
- **Score:** 0.985 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.985
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _num_or_zero ↔ start

- **A:** `_num_or_zero` in `generate_report.py:58`
- **B:** `start` in `lib/resource_policy.py:207`
- **Score:** 0.985 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.985
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_similarity ↔ kgrams

- **A:** `lcs_similarity` in `detect-ast-similarity.py:100`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.984 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.984
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ _discover_inputs

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.984 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.984
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_fuzzy_duplicates

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_fuzzy_duplicates` in `detect-fuzzy-names.py:274`
- **Score:** 0.984 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.984
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ extract_function_name

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.984 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.984
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _compute_pair_similarity

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ compute_pdg_fingerprint

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `compute_pdg_fingerprint` in `detect-pdg-semantic.py:84`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ descendants_from_table

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `descendants_from_table` in `lib/resource_policy.py:126`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_ast_similarity ↔ embedding_cosine

- **A:** `detect_ast_similarity` in `detect-ast-similarity.py:112`
- **B:** `embedding_cosine` in `detect-code-embedding.py:91`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ _best_per_strategy

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ winnow

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `winnow` in `detect-winnowing.py:65`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ evaluate

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `evaluate` in `evaluate.py:139`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ iter_json_array

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ iter_json_array

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ _best_per_strategy

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.983 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.983
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _abort

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_abort` in `lib/resource_policy.py:241`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ detect_signature_duplicates

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `detect_signature_duplicates` in `detect-signature-match.py:329`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ load_strategy_results

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `load_strategy_results` in `merge-signals.py:171`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ extract_for_language

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `extract_for_language` in `extract-functions-regex.py:260`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _get_token_strings

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_get_token_strings` in `detect-winnowing.py:114`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ peek_ws_or_eof

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ overlap_coefficient

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `overlap_coefficient` in `lib/common.py:214`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_tfidf_duplicates

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ winnow

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `winnow` in `detect-winnowing.py:65`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ generate_corpus

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `generate_corpus` in `generate-corpus.py:237`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _build_signature ↔ finish

- **A:** `_build_signature` in `extract-functions-ast-py.py:246`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extractParams ↔ _summary_block

- **A:** `extractParams` in `extract-functions-ast-ts.mjs:215`
- **B:** `_summary_block` in `generate_report.py:71`
- **Score:** 0.982 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ merge_pair_signals

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `merge_pair_signals` in `merge-signals.py:185`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.982
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_metric_clones

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_metric_clones` in `detect-metric-similarity.py:221`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ _strategy_name_from_path

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ _should_skip_test_file

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ kgrams

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ extract_for_language

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `extract_for_language` in `extract-functions-regex.py:260`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_ast_paths ↔ embedding_cosine

- **A:** `extract_ast_paths` in `detect-code-embedding.py:30`
- **B:** `embedding_cosine` in `detect-code-embedding.py:91`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ get_tokens

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `get_tokens` in `detect-tfidf-index.py:34`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ extract_function_name

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ _iter_scored

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _param_names_from_template ↔ tree_rss_bytes_from_table

- **A:** `_param_names_from_template` in `generate-corpus.py:93`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ _iter_scored

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ generate_type3_pair

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `generate_type3_pair` in `generate-corpus.py:140`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_type4_pair ↔ with_overrides

- **A:** `generate_type4_pair` in `generate-corpus.py:177`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ _discover_inputs

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _sample_table ↔ finish

- **A:** `_sample_table` in `lib/resource_policy.py:109`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _strategy_name_from_path ↔ _discover_inputs

- **A:** `_strategy_name_from_path` in `merge-signals.py:492`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ build_minhash

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `build_minhash` in `detect-lsh-ast.py:58`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_length ↔ suppress_noise_patterns

- **A:** `lcs_length` in `detect-ast-similarity.py:70`
- **B:** `suppress_noise_patterns` in `merge-signals.py:88`
- **Score:** 0.981 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.981
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ extract_function_name

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ raw_token_values

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `raw_token_values` in `detect-token-clones.py:67`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ _count_table

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `_count_table` in `generate_report.py:89`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ load_strategy_results

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `load_strategy_results` in `merge-signals.py:171`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_pair_similarity ↔ peek_ws_or_eof

- **A:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ _should_skip_test_file

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _iter_scored

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ skip_ws

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### decode_value ↔ atomic_write_text

- **A:** `decode_value` in `lib/jsonstream.py:116`
- **B:** `atomic_write_text` in `lib/jsonstream.py:344`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ compute_fingerprint

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `compute_fingerprint` in `detect-winnowing.py:133`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### validate_corpus ↔ _write_pairs

- **A:** `validate_corpus` in `generate-corpus.py:316`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ skip_ws

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### should_prefilter_pair ↔ with_overrides

- **A:** `should_prefilter_pair` in `lib/prefilter.py:15`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ peek_ws_or_eof

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ tree_rss_bytes_from_table

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ tokenize

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ computeAstFingerprint

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `computeAstFingerprint` in `extract-functions-ast-ts.mjs:128`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ computeTokenSequence

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `computeTokenSequence` in `extract-functions-ast-ts.mjs:160`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ getDecorators

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `getDecorators` in `extract-functions-ast-ts.mjs:176`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### computeTokenSequence ↔ extractParams

- **A:** `computeTokenSequence` in `extract-functions-ast-ts.mjs:160`
- **B:** `extractParams` in `extract-functions-ast-ts.mjs:215`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extractParams ↔ overlap_coefficient

- **A:** `extractParams` in `extract-functions-ast-ts.mjs:215`
- **B:** `overlap_coefficient` in `lib/common.py:214`
- **Score:** 0.98 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.98
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ validate_corpus

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `validate_corpus` in `generate-corpus.py:316`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ _strategy_name_from_path

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### finish ↔ generate_summary

- **A:** `finish` in `lib/resource_policy.py:370`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ cosine_similarity

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_winnowing_duplicates

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_winnowing_duplicates` in `detect-winnowing.py:172`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_pdg_fingerprint ↔ with_overrides

- **A:** `compute_pdg_fingerprint` in `detect-pdg-semantic.py:84`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### type_pattern_score ↔ with_overrides

- **A:** `type_pattern_score` in `detect-signature-match.py:185`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### evaluate ↔ iter_json_array

- **A:** `evaluate` in `evaluate.py:139`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ kgrams

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _strategy_name_from_path

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ _resolve_input

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `_resolve_input` in `generate_report.py:160`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_tfidf_duplicates ↔ skip_ws

- **A:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ _load_catalog_index

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ extract_function_name

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _build_params ↔ __init__

- **A:** `_build_params` in `extract-functions-ast-py.py:188`
- **B:** `__init__` in `lib/resource_policy.py:180`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _tokenize_core ↔ should_prefilter_pair

- **A:** `_tokenize_core` in `lib/common.py:134`
- **B:** `should_prefilter_pair` in `lib/prefilter.py:15`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ compute_idf

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `compute_idf` in `detect-tfidf-index.py:62`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_values ↔ peek_ws_or_eof

- **A:** `get_token_values` in `detect-ast-similarity.py:33`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _score_all

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_score_all` in `merge-signals.py:635`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _resolve_input ↔ skip_ws

- **A:** `_resolve_input` in `generate_report.py:160`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _param_names_from_template ↔ _best_per_strategy

- **A:** `_param_names_from_template` in `generate-corpus.py:93`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ with_overrides

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ generate_type4_pair

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `generate_type4_pair` in `generate-corpus.py:177`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ load_strategy_results

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `load_strategy_results` in `merge-signals.py:171`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ peek_ws_or_eof

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_set ↔ peek_ws_or_eof

- **A:** `get_token_set` in `detect-lsh-ast.py:38`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ get_param_count

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `get_param_count` in `detect-signature-match.py:132`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ _strategy_name_from_path

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ computeTokenSequence

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `computeTokenSequence` in `extract-functions-ast-ts.mjs:160`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ getDecorators

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `getDecorators` in `extract-functions-ast-ts.mjs:176`
- **Score:** 0.979 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.979
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _discover_inputs

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _cyclomatic_complexity

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ winnow

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `winnow` in `detect-winnowing.py:65`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_tfidf_duplicates ↔ with_overrides

- **A:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### synonym_boost ↔ with_overrides

- **A:** `synonym_boost` in `detect-fuzzy-names.py:197`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _extract_metrics ↔ normalize_type

- **A:** `_extract_metrics` in `detect-metric-similarity.py:110`
- **B:** `normalize_type` in `detect-signature-match.py:71`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _extract_token_sequence ↔ note_phase

- **A:** `_extract_token_sequence` in `extract-functions-ast-py.py:109`
- **B:** `note_phase` in `lib/resource_policy.py:364`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ with_overrides

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ overlap_coefficient

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `overlap_coefficient` in `lib/common.py:214`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _extract_token_sequence ↔ __init__

- **A:** `_extract_token_sequence` in `extract-functions-ast-py.py:109`
- **B:** `__init__` in `extract-functions-ast-py.py:354`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ _s

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `_s` in `generate_report.py:37`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ compute_idf

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `compute_idf` in `detect-tfidf-index.py:62`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ evaluate

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `evaluate` in `evaluate.py:139`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ iter_json_array

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ peek_ws_or_eof

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_tfidf_duplicates ↔ peek_ws_or_eof

- **A:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ _strategy_name_from_path

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_function_name ↔ _iter_scored

- **A:** `extract_function_name` in `extract-functions-regex.py:212`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ load_detected_pairs

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `load_detected_pairs` in `evaluate.py:84`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ _process_function

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `_process_function` in `extract-functions-ast-py.py:376`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ with_overrides

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### winnow ↔ _cyclomatic_complexity

- **A:** `winnow` in `detect-winnowing.py:65`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _decorator_names ↔ __init__

- **A:** `_decorator_names` in `extract-functions-ast-py.py:278`
- **B:** `__init__` in `extract-functions-ast-py.py:354`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_pair_similarity ↔ _sample_table

- **A:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **B:** `_sample_table` in `lib/resource_policy.py:109`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ skip_ws

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ peek_ws_or_eof

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_detected_pairs ↔ _cyclomatic_complexity

- **A:** `load_detected_pairs` in `evaluate.py:84`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _process_function

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_process_function` in `extract-functions-ast-py.py:376`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ walk_and_extract

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `walk_and_extract` in `extract-functions-ast-py.py:459`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_set ↔ _should_skip_test_file

- **A:** `get_token_set` in `detect-lsh-ast.py:38`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_pair_similarity ↔ skip_ws

- **A:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_type4_pair ↔ load_object_member

- **A:** `generate_type4_pair` in `generate-corpus.py:177`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _normalized_distance ↔ _func_to_spec

- **A:** `_normalized_distance` in `detect-metric-similarity.py:179`
- **B:** `_func_to_spec` in `evaluate.py:31`
- **Score:** 0.978 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.978
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ extract_function_name

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### write ↔ _strategy_name_from_path

- **A:** `write` in `lib/resource_policy.py:404`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_set ↔ _strategy_name_from_path

- **A:** `get_token_set` in `detect-lsh-ast.py:38`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _abort

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_abort` in `lib/resource_policy.py:241`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expand_abbreviations ↔ tree_rss_bytes_from_table

- **A:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ peek_ws_or_eof

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _strategy_name_from_path ↔ _load_catalog_index

- **A:** `_strategy_name_from_path` in `merge-signals.py:492`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ stable_hash

- **A:** `main` in `detect-fuzzy-names.py:338`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ stable_hash

- **A:** `main` in `detect-signature-match.py:378`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _build_params ↔ stable_hash

- **A:** `_build_params` in `extract-functions-ast-py.py:188`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ jaccard

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `jaccard` in `lib/common.py:194`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_params ↔ _resolve_input

- **A:** `extract_params` in `detect-signature-match.py:105`
- **B:** `_resolve_input` in `generate_report.py:160`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_object_member ↔ _iter_scored

- **A:** `load_object_member` in `lib/jsonstream.py:278`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_return_type ↔ load_strategy_results

- **A:** `get_return_type` in `detect-signature-match.py:147`
- **B:** `load_strategy_results` in `merge-signals.py:171`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_ast_tokens ↔ finish

- **A:** `normalize_ast_tokens` in `detect-token-clones.py:30`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ _resolve_input

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `_resolve_input` in `generate_report.py:160`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ suppress_noise_patterns

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `suppress_noise_patterns` in `merge-signals.py:88`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ jaccard

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `jaccard` in `lib/common.py:194`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ generate_type3_pair

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `generate_type3_pair` in `generate-corpus.py:140`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_fuzzy_duplicates ↔ normalize_type

- **A:** `detect_fuzzy_duplicates` in `detect-fuzzy-names.py:274`
- **B:** `normalize_type` in `detect-signature-match.py:71`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ extract_function_name

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_fingerprint ↔ extract_function_name

- **A:** `compute_fingerprint` in `detect-winnowing.py:133`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ _loop

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `_loop` in `lib/resource_policy.py:220`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_similarity ↔ build_embedding

- **A:** `lcs_similarity` in `detect-ast-similarity.py:100`
- **B:** `build_embedding` in `detect-code-embedding.py:70`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ get_token_set

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `get_token_set` in `detect-lsh-ast.py:38`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### evaluate ↔ tokenize

- **A:** `evaluate` in `evaluate.py:139`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### decode_value ↔ _abort

- **A:** `decode_value` in `lib/jsonstream.py:116`
- **B:** `_abort` in `lib/resource_policy.py:241`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_ast_similarity ↔ with_overrides

- **A:** `detect_ast_similarity` in `detect-ast-similarity.py:112`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ stable_hash

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ atomic_write_text

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `atomic_write_text` in `lib/jsonstream.py:344`
- **Score:** 0.977 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.977
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_params ↔ _build_signature

- **A:** `extract_params` in `detect-signature-match.py:105`
- **B:** `_build_signature` in `extract-functions-ast-py.py:246`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_params ↔ generate_summary

- **A:** `extract_params` in `detect-signature-match.py:105`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _build_signature ↔ generate_summary

- **A:** `_build_signature` in `extract-functions-ast-py.py:246`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_bag_of_ast_duplicates ↔ embedding_cosine

- **A:** `detect_bag_of_ast_duplicates` in `detect-bag-of-ast.py:87`
- **B:** `embedding_cosine` in `detect-code-embedding.py:91`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ embedding_cosine

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `embedding_cosine` in `detect-code-embedding.py:91`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_embedding_duplicates

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_embedding_duplicates` in `detect-code-embedding.py:126`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_pdg_duplicates

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_pdg_duplicates` in `detect-pdg-semantic.py:138`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_simple_tokens ↔ finish

- **A:** `normalize_simple_tokens` in `detect-token-clones.py:78`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _get_token_strings

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_get_token_strings` in `detect-winnowing.py:114`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ expand_abbreviations

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ skip_ws

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ skip_ws

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ extract_function_name

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ with_overrides

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ evaluate

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `evaluate` in `evaluate.py:139`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ skip_ws

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ peek_ws_or_eof

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### with_overrides ↔ _score_all

- **A:** `with_overrides` in `lib/resource_policy.py:81`
- **B:** `_score_all` in `merge-signals.py:635`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expand_abbreviations ↔ _best_per_strategy

- **A:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ _cyclomatic_complexity

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ _should_skip_test_file

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ _discover_inputs

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_value ↔ _iter_scored

- **A:** `skip_value` in `lib/jsonstream.py:171`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### param_name_similarity_score ↔ scan_source_tree

- **A:** `param_name_similarity_score` in `detect-signature-match.py:261`
- **B:** `scan_source_tree` in `extract-functions-regex.py:153`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_simple_tokens ↔ _load_catalog_index

- **A:** `normalize_simple_tokens` in `detect-token-clones.py:78`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _tokenize_core ↔ with_overrides

- **A:** `_tokenize_core` in `lib/common.py:134`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ generate_corpus

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `generate_corpus` in `generate-corpus.py:237`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _placeholder ↔ __init__

- **A:** `_placeholder` in `extract-functions-ast-py.py:48`
- **B:** `__init__` in `extract-functions-ast-py.py:354`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ skip_value

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `skip_value` in `lib/jsonstream.py:171`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ skip_ws

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_values ↔ _should_skip_test_file

- **A:** `get_token_values` in `detect-ast-similarity.py:33`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ peek_ws_or_eof

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ iter_json_array

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ descendants_from_table

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `descendants_from_table` in `lib/resource_policy.py:126`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _strategy_name_from_path ↔ __init__

- **A:** `_strategy_name_from_path` in `merge-signals.py:492`
- **B:** `__init__` in `merge-signals.py:696`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### parseArgs ↔ generate_summary

- **A:** `parseArgs` in `extract-functions-ast-ts.mjs:13`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.976 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.976
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_length ↔ _score_all

- **A:** `lcs_length` in `detect-ast-similarity.py:70`
- **B:** `_score_all` in `merge-signals.py:635`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ generate_type4_pair

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `generate_type4_pair` in `generate-corpus.py:177`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ get_param_count

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `get_param_count` in `detect-signature-match.py:132`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_length ↔ _best_per_strategy

- **A:** `lcs_length` in `detect-ast-similarity.py:70`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ kgrams

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_pair_similarity ↔ kgrams

- **A:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### score_pair_tfidf ↔ peek_ws_or_eof

- **A:** `score_pair_tfidf` in `detect-tfidf-index.py:121`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ jaccard

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `jaccard` in `lib/common.py:194`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### evaluate ↔ with_overrides

- **A:** `evaluate` in `evaluate.py:139`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _count_table ↔ _iter_scored

- **A:** `_count_table` in `generate_report.py:89`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _process_function

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_process_function` in `extract-functions-ast-py.py:376`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_pdg_fingerprint ↔ arity_match_score

- **A:** `compute_pdg_fingerprint` in `detect-pdg-semantic.py:84`
- **B:** `arity_match_score` in `detect-signature-match.py:158`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ decode_value

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `decode_value` in `lib/jsonstream.py:116`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _param_names_from_template ↔ skip_ws

- **A:** `_param_names_from_template` in `generate-corpus.py:93`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### stable_hash ↔ _write_pairs

- **A:** `stable_hash` in `lib/common.py:15`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _best_per_strategy ↔ _strategy_name_from_path

- **A:** `_best_per_strategy` in `merge-signals.py:225`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ detect_fuzzy_duplicates

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `detect_fuzzy_duplicates` in `detect-fuzzy-names.py:274`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ compute_fingerprint

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `compute_fingerprint` in `detect-winnowing.py:133`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ _sample_table

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `_sample_table` in `lib/resource_policy.py:109`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_fingerprint ↔ _best_per_strategy

- **A:** `compute_fingerprint` in `detect-winnowing.py:133`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _load_catalog_index

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_inverted_index ↔ kgrams

- **A:** `build_inverted_index` in `detect-tfidf-index.py:48`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ _load_catalog_index

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ get_tokens

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `get_tokens` in `detect-tfidf-index.py:34`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_signature_duplicates ↔ _build_signature

- **A:** `detect_signature_duplicates` in `detect-signature-match.py:329`
- **B:** `_build_signature` in `extract-functions-ast-py.py:246`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_strategy_results ↔ _positive_int

- **A:** `load_strategy_results` in `merge-signals.py:171`
- **B:** `_positive_int` in `merge-signals.py:752`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### synonym_boost ↔ iter_json_array

- **A:** `synonym_boost` in `detect-fuzzy-names.py:197`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_inverted_index ↔ skip_ws

- **A:** `build_inverted_index` in `detect-tfidf-index.py:48`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ _sample_table

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `_sample_table` in `lib/resource_policy.py:109`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ skip_ws

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ _loop

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `_loop` in `lib/resource_policy.py:220`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tree_rss_bytes_from_table ↔ __init__

- **A:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **B:** `__init__` in `merge-signals.py:696`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_signature_duplicates

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_signature_duplicates` in `detect-signature-match.py:329`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _sha256_file

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_sha256_file` in `lib/resource_policy.py:317`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ compute_fingerprint

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `compute_fingerprint` in `detect-winnowing.py:133`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### param_name_similarity_score ↔ _abort

- **A:** `param_name_similarity_score` in `detect-signature-match.py:261`
- **B:** `_abort` in `lib/resource_policy.py:241`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### with_overrides ↔ _iter_scored

- **A:** `with_overrides` in `lib/resource_policy.py:81`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ compute_idf

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `compute_idf` in `detect-tfidf-index.py:62`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ _get

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `_get` in `generate_report.py:50`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ decode_value

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `decode_value` in `lib/jsonstream.py:116`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### decode_value ↔ _iter_records

- **A:** `decode_value` in `lib/jsonstream.py:116`
- **B:** `_iter_records` in `merge-signals.py:524`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### write ↔ _iter_scored

- **A:** `write` in `lib/resource_policy.py:404`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.975 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.975
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_values ↔ with_overrides

- **A:** `get_token_values` in `detect-ast-similarity.py:33`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_length ↔ get_param_count

- **A:** `lcs_length` in `detect-ast-similarity.py:70`
- **B:** `get_param_count` in `detect-signature-match.py:132`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _compute_pair_similarity

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _process_function

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_process_function` in `extract-functions-ast-py.py:376`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_ground_truth ↔ generate_type1_pair

- **A:** `load_ground_truth` in `evaluate.py:36`
- **B:** `generate_type1_pair` in `generate-corpus.py:99`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _resolve_input ↔ peek_ws_or_eof

- **A:** `_resolve_input` in `generate_report.py:160`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ load_object_member

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_length ↔ load_ground_truth

- **A:** `lcs_length` in `detect-ast-similarity.py:70`
- **B:** `load_ground_truth` in `evaluate.py:36`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _write_pairs

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_signature_duplicates ↔ should_compare

- **A:** `detect_signature_duplicates` in `detect-signature-match.py:329`
- **B:** `should_compare` in `lib/common.py:230`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_ground_truth ↔ tokenize

- **A:** `load_ground_truth` in `evaluate.py:36`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_ground_truth ↔ _strategy_name_from_path

- **A:** `load_ground_truth` in `evaluate.py:36`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ iter_json_array

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ _sample_table

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `_sample_table` in `lib/resource_policy.py:109`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expand_abbreviations ↔ build_minhash

- **A:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **B:** `build_minhash` in `detect-lsh-ast.py:58`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_set ↔ _loop

- **A:** `get_token_set` in `detect-lsh-ast.py:38`
- **B:** `_loop` in `lib/resource_policy.py:220`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ finish

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ generate_type3_pair

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `generate_type3_pair` in `generate-corpus.py:140`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ _load_catalog_index

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ _build_params

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `_build_params` in `extract-functions-ast-py.py:188`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### stable_hash ↔ _open_scratch_db

- **A:** `stable_hash` in `lib/common.py:15`
- **B:** `_open_scratch_db` in `merge-signals.py:554`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tokenize ↔ peek_ws_or_eof

- **A:** `tokenize` in `lib/common.py:84`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ load_detected_pairs

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `load_detected_pairs` in `evaluate.py:84`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _extract_metrics ↔ _tokenize_core

- **A:** `_extract_metrics` in `detect-metric-similarity.py:110`
- **B:** `_tokenize_core` in `lib/common.py:134`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_detected_pairs ↔ with_overrides

- **A:** `load_detected_pairs` in `evaluate.py:84`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ _loop

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `_loop` in `lib/resource_policy.py:220`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ peek_ws_or_eof

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_corpus ↔ _tokenize_core

- **A:** `generate_corpus` in `generate-corpus.py:237`
- **B:** `_tokenize_core` in `lib/common.py:134`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_ast_similarity ↔ cosine_similarity

- **A:** `detect_ast_similarity` in `detect-ast-similarity.py:112`
- **B:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ compute_idf

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `compute_idf` in `detect-tfidf-index.py:62`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ peek_ws_or_eof

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ _sample_table

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `_sample_table` in `lib/resource_policy.py:109`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### score_pair_tfidf ↔ iter_json_array

- **A:** `score_pair_tfidf` in `detect-tfidf-index.py:121`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ iter_json_array

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _write_pairs

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ fingerprint_similarity

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `fingerprint_similarity` in `detect-winnowing.py:152`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_function_name ↔ iter_json_array

- **A:** `extract_function_name` in `extract-functions-regex.py:212`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_for_language ↔ load_object_member

- **A:** `extract_for_language` in `extract-functions-regex.py:260`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_value ↔ iter_json_array

- **A:** `skip_value` in `lib/jsonstream.py:171`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ extract_ast_paths

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `extract_ast_paths` in `detect-code-embedding.py:30`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ compute_fingerprint

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `compute_fingerprint` in `detect-winnowing.py:133`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ peek_ws_or_eof

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ _process_function

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `_process_function` in `extract-functions-ast-py.py:376`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ iter_json_array

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### score_pair_tfidf ↔ skip_ws

- **A:** `score_pair_tfidf` in `detect-tfidf-index.py:121`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tokenize ↔ _loop

- **A:** `tokenize` in `lib/common.py:84`
- **B:** `_loop` in `lib/resource_policy.py:220`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### decode_value ↔ _discover_inputs

- **A:** `decode_value` in `lib/jsonstream.py:116`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### iter_object_member_array ↔ _write_pairs

- **A:** `iter_object_member_array` in `lib/jsonstream.py:246`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ compute_idf

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `compute_idf` in `detect-tfidf-index.py:62`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ skip_value

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `skip_value` in `lib/jsonstream.py:171`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ detect_metric_clones

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `detect_metric_clones` in `detect-metric-similarity.py:221`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ winnow

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `winnow` in `detect-winnowing.py:65`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### param_name_similarity_score ↔ with_overrides

- **A:** `param_name_similarity_score` in `detect-signature-match.py:261`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_fingerprint ↔ _signals_lines

- **A:** `compute_fingerprint` in `detect-winnowing.py:133`
- **B:** `_signals_lines` in `generate_report.py:105`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### fingerprint_similarity ↔ walk_and_extract

- **A:** `fingerprint_similarity` in `detect-winnowing.py:152`
- **B:** `walk_and_extract` in `extract-functions-ast-py.py:459`
- **Score:** 0.974 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.974
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ skip_ws

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ _strategy_name_from_path

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ raw_token_values

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `raw_token_values` in `detect-token-clones.py:67`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _should_skip_test_file

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ fingerprint_similarity

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `fingerprint_similarity` in `detect-winnowing.py:152`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _extract_metrics ↔ type_pattern_score

- **A:** `_extract_metrics` in `detect-metric-similarity.py:110`
- **B:** `type_pattern_score` in `detect-signature-match.py:185`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ _iter_scored

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ _build_params

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `_build_params` in `extract-functions-ast-py.py:188`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_pair_similarity ↔ iter_json_array

- **A:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_tokens ↔ with_overrides

- **A:** `get_tokens` in `detect-tfidf-index.py:34`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ kgrams

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_tfidf_duplicates ↔ extract_function_name

- **A:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_ground_truth ↔ generate_type4_pair

- **A:** `load_ground_truth` in `evaluate.py:36`
- **B:** `generate_type4_pair` in `generate-corpus.py:177`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ _strategy_name_from_path

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _tokenize_core ↔ finish

- **A:** `_tokenize_core` in `lib/common.py:134`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _iter_records ↔ _load_catalog_index

- **A:** `_iter_records` in `merge-signals.py:524`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ with_overrides

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ iter_json_array

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### param_name_similarity_score ↔ load_detected_pairs

- **A:** `param_name_similarity_score` in `detect-signature-match.py:261`
- **B:** `load_detected_pairs` in `evaluate.py:84`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_ground_truth ↔ generate_type2_pair

- **A:** `load_ground_truth` in `evaluate.py:36`
- **B:** `generate_type2_pair` in `generate-corpus.py:119`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_length ↔ generate_summary

- **A:** `lcs_length` in `detect-ast-similarity.py:70`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ walk_and_extract

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `walk_and_extract` in `extract-functions-ast-py.py:459`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ _should_skip_test_file

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ stable_hash

- **A:** `main` in `detect-bag-of-ast.py:149`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### segment_into_blocks ↔ skip_ws

- **A:** `segment_into_blocks` in `detect-pdg-semantic.py:52`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ stable_hash

- **A:** `main` in `detect-pdg-semantic.py:203`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_params ↔ _strategy_name_from_path

- **A:** `extract_params` in `detect-signature-match.py:105`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ stable_hash

- **A:** `main` in `detect-token-clones.py:210`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### evaluate ↔ _cyclomatic_complexity

- **A:** `evaluate` in `evaluate.py:139`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _best_per_strategy ↔ _iter_scored

- **A:** `_best_per_strategy` in `merge-signals.py:225`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ _best_per_strategy

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### raw_token_values ↔ overlap_coefficient

- **A:** `raw_token_values` in `detect-token-clones.py:67`
- **B:** `overlap_coefficient` in `lib/common.py:214`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get ↔ jaccard

- **A:** `_get` in `generate_report.py:50`
- **B:** `jaccard` in `lib/common.py:194`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ with_overrides

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ detect_clones

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `detect_clones` in `detect-token-clones.py:119`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ get_return_type

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `get_return_type` in `detect-signature-match.py:147`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ extract_function_name

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_simple_tokens ↔ tree_rss_bytes_from_table

- **A:** `normalize_simple_tokens` in `detect-token-clones.py:78`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_for_language ↔ should_prefilter_pair

- **A:** `extract_for_language` in `extract-functions-regex.py:260`
- **B:** `should_prefilter_pair` in `lib/prefilter.py:15`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ detect_tfidf_duplicates

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ add_pairs

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `add_pairs` in `detect-token-clones.py:168`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ extract_function_name

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### score_pair_tfidf ↔ tokenize

- **A:** `score_pair_tfidf` in `detect-tfidf-index.py:121`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### score_pair_tfidf ↔ with_overrides

- **A:** `score_pair_tfidf` in `detect-tfidf-index.py:121`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_simple_tokens ↔ peek_ws_or_eof

- **A:** `normalize_simple_tokens` in `detect-token-clones.py:78`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _count_table ↔ tokenize

- **A:** `_count_table` in `generate_report.py:89`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### iter_jsonl ↔ _score_all

- **A:** `iter_jsonl` in `lib/jsonstream.py:301`
- **B:** `_score_all` in `merge-signals.py:635`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### winnow ↔ with_overrides

- **A:** `winnow` in `detect-winnowing.py:65`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_fingerprint ↔ with_overrides

- **A:** `compute_fingerprint` in `detect-winnowing.py:133`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### fingerprint_similarity ↔ extract_function_name

- **A:** `fingerprint_similarity` in `detect-winnowing.py:152`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _loop ↔ _strategy_name_from_path

- **A:** `_loop` in `lib/resource_policy.py:220`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.973 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.973
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ _s

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `_s` in `generate_report.py:37`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ should_prefilter_pair

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `should_prefilter_pair` in `lib/prefilter.py:15`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _normalized_distance ↔ _compute_metrics

- **A:** `_normalized_distance` in `detect-metric-similarity.py:179`
- **B:** `_compute_metrics` in `evaluate.py:124`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_function_name ↔ jaccard

- **A:** `extract_function_name` in `extract-functions-regex.py:212`
- **B:** `jaccard` in `lib/common.py:194`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_function_name ↔ with_overrides

- **A:** `extract_function_name` in `extract-functions-regex.py:212`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_type4_pair ↔ _best_per_strategy

- **A:** `generate_type4_pair` in `generate-corpus.py:177`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### validate_corpus ↔ should_compare

- **A:** `validate_corpus` in `generate-corpus.py:316`
- **B:** `should_compare` in `lib/common.py:230`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _loop ↔ _load_catalog_index

- **A:** `_loop` in `lib/resource_policy.py:220`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ get_token_set

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `get_token_set` in `detect-lsh-ast.py:38`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ extract_function_name

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `extract_function_name` in `extract-functions-regex.py:212`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ score_pair_tfidf

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `score_pair_tfidf` in `detect-tfidf-index.py:121`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_signature_duplicates ↔ with_overrides

- **A:** `detect_signature_duplicates` in `detect-signature-match.py:329`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ _cyclomatic_complexity

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### evaluate ↔ iter_jsonl

- **A:** `evaluate` in `evaluate.py:139`
- **B:** `iter_jsonl` in `lib/jsonstream.py:301`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ iter_jsonl

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `iter_jsonl` in `lib/jsonstream.py:301`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### iter_object_member_array ↔ _ingest

- **A:** `iter_object_member_array` in `lib/jsonstream.py:246`
- **B:** `_ingest` in `merge-signals.py:582`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### raw_token_values ↔ peek_ws_or_eof

- **A:** `raw_token_values` in `detect-token-clones.py:67`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ _best_per_strategy

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _build_signature ↔ tokenize

- **A:** `_build_signature` in `extract-functions-ast-py.py:246`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_function_name ↔ skip_value

- **A:** `extract_function_name` in `extract-functions-regex.py:212`
- **B:** `skip_value` in `lib/jsonstream.py:171`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tokenize ↔ generate_summary

- **A:** `tokenize` in `lib/common.py:84`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ merge_pair_signals

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `merge_pair_signals` in `merge-signals.py:185`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_type ↔ _write_pairs

- **A:** `normalize_type` in `detect-signature-match.py:71`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_metrics ↔ _count_table

- **A:** `_compute_metrics` in `evaluate.py:124`
- **B:** `_count_table` in `generate_report.py:89`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ tokenize

- **A:** `main` in `extract-functions-ast-py.py:537`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ load_strategy_results

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `load_strategy_results` in `merge-signals.py:171`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### extract_ast_paths ↔ with_overrides

- **A:** `extract_ast_paths` in `detect-code-embedding.py:30`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### validate_corpus ↔ finish

- **A:** `validate_corpus` in `generate-corpus.py:316`
- **B:** `finish` in `lib/resource_policy.py:370`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ with_overrides

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expand_abbreviations ↔ to_dict

- **A:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **B:** `to_dict` in `lib/resource_policy.py:101`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_pair_similarity ↔ with_overrides

- **A:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ jaccard

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `jaccard` in `lib/common.py:194`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _get_token_strings ↔ load_object_member

- **A:** `_get_token_strings` in `detect-winnowing.py:114`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _process_function ↔ atomic_write_text

- **A:** `_process_function` in `extract-functions-ast-py.py:376`
- **B:** `atomic_write_text` in `lib/jsonstream.py:344`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### scan_source_tree ↔ with_overrides

- **A:** `scan_source_tree` in `extract-functions-regex.py:153`
- **B:** `with_overrides` in `lib/resource_policy.py:81`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### validate_corpus ↔ stable_hash

- **A:** `validate_corpus` in `generate-corpus.py:316`
- **B:** `stable_hash` in `lib/common.py:15`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _best_per_strategy

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ _cyclomatic_complexity

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ generate_type4_pair

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `generate_type4_pair` in `generate-corpus.py:177`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ iter_jsonl

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `iter_jsonl` in `lib/jsonstream.py:301`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_similarity ↔ build_minhash

- **A:** `lcs_similarity` in `detect-ast-similarity.py:100`
- **B:** `build_minhash` in `detect-lsh-ast.py:58`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ tokenize

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `tokenize` in `lib/common.py:84`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_type1_pair ↔ _positive_int

- **A:** `generate_type1_pair` in `generate-corpus.py:99`
- **B:** `_positive_int` in `merge-signals.py:752`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ _iter_records

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `_iter_records` in `merge-signals.py:524`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### getBodyLines ↔ _should_skip_test_file

- **A:** `getBodyLines` in `extract-functions-ast-ts.mjs:335`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.972 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _iter_result_pairs ↔ _open_scratch_db

- **A:** `_iter_result_pairs` in `evaluate.py:61`
- **B:** `_open_scratch_db` in `merge-signals.py:554`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _decorator_names ↔ to_dict

- **A:** `_decorator_names` in `extract-functions-ast-py.py:278`
- **B:** `to_dict` in `lib/resource_policy.py:101`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### iter_json_array ↔ _strategy_name_from_path

- **A:** `iter_json_array` in `lib/jsonstream.py:222`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.972
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### abbreviation_boost ↔ _get

- **A:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **B:** `_get` in `generate_report.py:50`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### param_name_similarity_score ↔ walk_and_extract

- **A:** `param_name_similarity_score` in `detect-signature-match.py:261`
- **B:** `walk_and_extract` in `extract-functions-ast-py.py:459`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_ground_truth ↔ generate_type3_pair

- **A:** `load_ground_truth` in `evaluate.py:36`
- **B:** `generate_type3_pair` in `generate-corpus.py:140`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _compute_metrics ↔ _param_names_from_template

- **A:** `_compute_metrics` in `evaluate.py:124`
- **B:** `_param_names_from_template` in `generate-corpus.py:93`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### validate_corpus ↔ generate_summary

- **A:** `validate_corpus` in `generate-corpus.py:316`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expect ↔ _iter_scored

- **A:** `expect` in `lib/jsonstream.py:109`
- **B:** `_iter_scored` in `merge-signals.py:681`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### iter_json_array ↔ _load_catalog_index

- **A:** `iter_json_array` in `lib/jsonstream.py:222`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ _should_skip_test_file

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ _resolve_input

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `_resolve_input` in `generate_report.py:160`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ load_ground_truth

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `load_ground_truth` in `evaluate.py:36`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _param_names_from_template ↔ _open_cursor

- **A:** `_param_names_from_template` in `generate-corpus.py:93`
- **B:** `_open_cursor` in `lib/jsonstream.py:217`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_type2_pair ↔ _positive_int

- **A:** `generate_type2_pair` in `generate-corpus.py:119`
- **B:** `_positive_int` in `merge-signals.py:752`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ detect_winnowing_duplicates

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `detect_winnowing_duplicates` in `detect-winnowing.py:172`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ arity_match_score

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `arity_match_score` in `detect-signature-match.py:158`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_tfidf_duplicates ↔ load_object_member

- **A:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _iter_result_pairs ↔ visit_alias

- **A:** `_iter_result_pairs` in `evaluate.py:61`
- **B:** `visit_alias` in `extract-functions-ast-py.py:86`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ _load_catalog_index

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `_load_catalog_index` in `merge-signals.py:536`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_value ↔ _discover_inputs

- **A:** `skip_value` in `lib/jsonstream.py:171`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ _build_signature

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `_build_signature` in `extract-functions-ast-py.py:246`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ _build_signature

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `_build_signature` in `extract-functions-ast-py.py:246`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ _best_per_strategy

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### fingerprint_similarity ↔ _best_per_strategy

- **A:** `fingerprint_similarity` in `detect-winnowing.py:152`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_type4_pair ↔ _write_pairs

- **A:** `generate_type4_pair` in `generate-corpus.py:177`
- **B:** `_write_pairs` in `merge-signals.py:962`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### embedding_cosine ↔ validate_corpus

- **A:** `embedding_cosine` in `detect-code-embedding.py:91`
- **B:** `validate_corpus` in `generate-corpus.py:316`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ write

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `write` in `lib/resource_policy.py:404`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tokenize ↔ __init__

- **A:** `tokenize` in `lib/common.py:84`
- **B:** `__init__` in `lib/resource_policy.py:180`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expand_abbreviations ↔ skip_ws

- **A:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### retrieve_candidates ↔ kgrams

- **A:** `retrieve_candidates` in `detect-tfidf-index.py:79`
- **B:** `kgrams` in `detect-winnowing.py:48`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### iter_json_array ↔ _best_per_strategy

- **A:** `iter_json_array` in `lib/jsonstream.py:222`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ _score_all

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `_score_all` in `merge-signals.py:635`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _should_skip_test_file ↔ _discover_inputs

- **A:** `_should_skip_test_file` in `extract-functions-regex.py:142`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_set ↔ skip_value

- **A:** `get_token_set` in `detect-lsh-ast.py:38`
- **B:** `skip_value` in `lib/jsonstream.py:171`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ _compute_pair_similarity

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `_compute_pair_similarity` in `detect-metric-similarity.py:184`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_idf ↔ _get

- **A:** `compute_idf` in `detect-tfidf-index.py:62`
- **B:** `_get` in `generate_report.py:50`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### detect_tfidf_duplicates ↔ _cyclomatic_complexity

- **A:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **B:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### normalize_simple_tokens ↔ generate_summary

- **A:** `normalize_simple_tokens` in `detect-token-clones.py:78`
- **B:** `generate_summary` in `merge-signals.py:445`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### winnow ↔ should_prefilter_pair

- **A:** `winnow` in `detect-winnowing.py:65`
- **B:** `should_prefilter_pair` in `lib/prefilter.py:15`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _iter_result_pairs ↔ decode_value

- **A:** `_iter_result_pairs` in `evaluate.py:61`
- **B:** `decode_value` in `lib/jsonstream.py:116`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tokenize ↔ __init__

- **A:** `tokenize` in `lib/common.py:84`
- **B:** `__init__` in `merge-signals.py:696`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _sample_table ↔ _strategy_name_from_path

- **A:** `_sample_table` in `lib/resource_policy.py:109`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_values ↔ _sample_table

- **A:** `get_token_values` in `detect-ast-similarity.py:33`
- **B:** `_sample_table` in `lib/resource_policy.py:109`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ descendants_from_table

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `descendants_from_table` in `lib/resource_policy.py:126`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### main ↔ extract_params

- **A:** `main` in `detect-metric-similarity.py:332`
- **B:** `extract_params` in `detect-signature-match.py:105`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ detect_tfidf_duplicates

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `detect_tfidf_duplicates` in `detect-tfidf-index.py:156`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _cyclomatic_complexity ↔ _resolve_input

- **A:** `_cyclomatic_complexity` in `extract-functions-ast-py.py:143`
- **B:** `_resolve_input` in `generate_report.py:160`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### tokenize ↔ skip_ws

- **A:** `tokenize` in `lib/common.py:84`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _loop ↔ _iter_records

- **A:** `_loop` in `lib/resource_policy.py:220`
- **B:** `_iter_records` in `merge-signals.py:524`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_token_set ↔ decode_value

- **A:** `get_token_set` in `detect-lsh-ast.py:38`
- **B:** `decode_value` in `lib/jsonstream.py:116`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ generate_type4_pair

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `generate_type4_pair` in `generate-corpus.py:177`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_minhash ↔ load_object_member

- **A:** `build_minhash` in `detect-lsh-ast.py:58`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### arity_match_score ↔ add_pairs

- **A:** `arity_match_score` in `detect-signature-match.py:158`
- **B:** `add_pairs` in `detect-token-clones.py:168`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### assert_only_trailing_ws ↔ legacy

- **A:** `assert_only_trailing_ws` in `lib/jsonstream.py:180`
- **B:** `legacy` in `merge-signals.py:716`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_detected_pairs ↔ computeAstFingerprint

- **A:** `load_detected_pairs` in `evaluate.py:84`
- **B:** `computeAstFingerprint` in `extract-functions-ast-ts.mjs:128`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ printUsage

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ getDocstring

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _first_line_docstring ↔ printUsage

- **A:** `_first_line_docstring` in `extract-functions-ast-py.py:333`
- **B:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _first_line_docstring ↔ getDocstring

- **A:** `_first_line_docstring` in `extract-functions-ast-py.py:333`
- **B:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### printUsage ↔ start

- **A:** `printUsage` in `extract-functions-ast-ts.mjs:51`
- **B:** `start` in `lib/resource_policy.py:343`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### getDocstring ↔ start

- **A:** `getDocstring` in `extract-functions-ast-ts.mjs:192`
- **B:** `start` in `lib/resource_policy.py:343`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_final_score ↔ getSignature

- **A:** `compute_final_score` in `detect-signature-match.py:298`
- **B:** `getSignature` in `extract-functions-ast-ts.mjs:256`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### getSignature ↔ _both_small

- **A:** `getSignature` in `extract-functions-ast-ts.mjs:256`
- **B:** `_both_small` in `merge-signals.py:57`
- **Score:** 0.971 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** metric_similarity=0.971
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ segment_into_blocks

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `segment_into_blocks` in `detect-pdg-semantic.py:52`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _extract_metrics ↔ validate_corpus

- **A:** `_extract_metrics` in `detect-metric-similarity.py:110`
- **B:** `validate_corpus` in `generate-corpus.py:316`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### load_detected_pairs ↔ peek_ws_or_eof

- **A:** `load_detected_pairs` in `evaluate.py:84`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### __init__ ↔ tree_rss_bytes_from_table

- **A:** `__init__` in `extract-functions-ast-py.py:354`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### peek_ws_or_eof ↔ tree_rss_bytes_from_table

- **A:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### build_embedding ↔ peek_ws_or_eof

- **A:** `build_embedding` in `detect-code-embedding.py:70`
- **B:** `peek_ws_or_eof` in `lib/jsonstream.py:96`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### get_param_count ↔ tree_rss_bytes_from_table

- **A:** `get_param_count` in `detect-signature-match.py:132`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### generate_corpus ↔ iter_object_member_array

- **A:** `generate_corpus` in `generate-corpus.py:237`
- **B:** `iter_object_member_array` in `lib/jsonstream.py:246`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ngrams ↔ _best_per_strategy

- **A:** `ngrams` in `detect-ast-similarity.py:63`
- **B:** `_best_per_strategy` in `merge-signals.py:225`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### compute_pdg_fingerprint ↔ load_object_member

- **A:** `compute_pdg_fingerprint` in `detect-pdg-semantic.py:84`
- **B:** `load_object_member` in `lib/jsonstream.py:278`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### __init__ ↔ _strategy_name_from_path

- **A:** `__init__` in `lib/resource_policy.py:180`
- **B:** `_strategy_name_from_path` in `merge-signals.py:492`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ add_pairs

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `add_pairs` in `detect-token-clones.py:168`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ iter_json_array

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `iter_json_array` in `lib/jsonstream.py:222`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ should_prefilter_pair

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `should_prefilter_pair` in `lib/prefilter.py:15`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### expand_abbreviations ↔ abbreviation_boost

- **A:** `expand_abbreviations` in `detect-fuzzy-names.py:179`
- **B:** `abbreviation_boost` in `detect-fuzzy-names.py:238`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### kgrams ↔ fingerprint_similarity

- **A:** `kgrams` in `detect-winnowing.py:48`
- **B:** `fingerprint_similarity` in `detect-winnowing.py:152`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### skip_ws ↔ tree_rss_bytes_from_table

- **A:** `skip_ws` in `lib/jsonstream.py:83`
- **B:** `tree_rss_bytes_from_table` in `lib/resource_policy.py:144`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### _iter_scored ↔ __init__

- **A:** `_iter_scored` in `merge-signals.py:681`
- **B:** `__init__` in `merge-signals.py:696`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### lcs_similarity ↔ _discover_inputs

- **A:** `lcs_similarity` in `detect-ast-similarity.py:100`
- **B:** `_discover_inputs` in `merge-signals.py:501`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### ast_node_vector ↔ _build_params

- **A:** `ast_node_vector` in `detect-bag-of-ast.py:29`
- **B:** `_build_params` in `extract-functions-ast-py.py:188`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---

### cosine_similarity ↔ skip_ws

- **A:** `cosine_similarity` in `detect-bag-of-ast.py:57`
- **B:** `skip_ws` in `lib/jsonstream.py:83`
- **Score:** 0.97 from 1 strategy(ies)
- **Clone Type:** Type 4 (semantic clone)
- **Signals:** bag_of_ast=0.97
- **Action:** INVESTIGATE — Likely duplicate flagged by 1 strategy(ies) — review implementations

---


_7366 additional MEDIUM pair(s) omitted (cap 500)_

## LOW Confidence (Review)

> Weak signals — review if time permits.

- `tree_rss_bytes_from_table` (lib/resource_policy.py:144) ↔ `stop` (lib/resource_policy.py:211) — score 0.549, signals: tfidf_index
- `_summary_block` (generate_report.py:71) ↔ `generate_recommendation` (merge-signals.py:412) — score 0.543, signals: tfidf_index
- `_open_cursor` (lib/jsonstream.py:217) ↔ `_git_head` (lib/resource_policy.py:325) — score 0.542, signals: tfidf_index
- `getDecorators` (extract-functions-ast-ts.mjs:176) ↔ `getReturnType` (extract-functions-ast-ts.mjs:232) — score 0.533, signals: tfidf_index
- `_compute_ast_fingerprint` (extract-functions-ast-py.py:94) ↔ `_build_parser` (merge-signals.py:762) — score 0.532, signals: tfidf_index
- `build_embedding` (detect-code-embedding.py:70) ↔ `_build_parser` (merge-signals.py:762) — score 0.531, signals: tfidf_index
- `load_ground_truth` (evaluate.py:36) ↔ `_resolve_language` (extract-functions-regex.py:130) — score 0.531, signals: tfidf_index
- `_build_params` (extract-functions-ast-py.py:188) ↔ `generate_recommendation` (merge-signals.py:412) — score 0.531, signals: tfidf_index
- `_num_or_zero` (generate_report.py:58) ↔ `_utc_now` (lib/resource_policy.py:313) — score 0.523, signals: metric_similarity, signature_match
- `compute_fingerprint` (detect-winnowing.py:133) ↔ `computeAstFingerprint` (extract-functions-ast-ts.mjs:128) — score 0.522, signals: fuzzy_name
- `_process_function` (extract-functions-ast-py.py:376) ↔ `_resolve_language` (extract-functions-regex.py:130) — score 0.522, signals: tfidf_index
- `build_embedding` (detect-code-embedding.py:70) ↔ `build_parser` (extract-functions-ast-py.py:505) — score 0.52, signals: tfidf_index
- `get_return_type` (detect-signature-match.py:147) ↔ `_git_head` (lib/resource_policy.py:325) — score 0.518, signals: metric_similarity, signature_match
- `build_embedding` (detect-code-embedding.py:70) ↔ `build_parser` (detect-metric-similarity.py:290) — score 0.515, signals: tfidf_index
- `validate_corpus` (generate-corpus.py:316) ↔ `generate_recommendation` (merge-signals.py:412) — score 0.514, signals: tfidf_index
- `decode_value` (lib/jsonstream.py:116) ↔ `generate_recommendation` (merge-signals.py:412) — score 0.51, signals: tfidf_index
- `computeTokenSequence` (extract-functions-ast-ts.mjs:160) ↔ `getBodyLines` (extract-functions-ast-ts.mjs:335) — score 0.509, signals: tfidf_index
- `tokenize_to_typed` (lib/common.py:110) ↔ `_git_head` (lib/resource_policy.py:325) — score 0.506, signals: tfidf_index
- `_git_head` (lib/resource_policy.py:325) ↔ `load_strategy_results` (merge-signals.py:171) — score 0.506, signals: tfidf_index
- `getDocstring` (extract-functions-ast-ts.mjs:192) ↔ `detectLanguage` (extract-functions-ast-ts.mjs:347) — score 0.503, signals: tfidf_index
- `_func_to_spec` (evaluate.py:31) ↔ `tokenize_to_typed` (lib/common.py:110) — score 0.5, signals: pdg_semantic
- `_func_to_spec` (evaluate.py:31) ↔ `tokenize_to_strings` (lib/common.py:125) — score 0.5, signals: pdg_semantic
- `ngrams` (detect-ast-similarity.py:63) ↔ `defaults` (lib/resource_policy.py:78) — score 0.5, signals: winnowing
- `_extract_token_sequence` (extract-functions-ast-py.py:109) ↔ `defaults` (lib/resource_policy.py:78) — score 0.5, signals: winnowing
- `_decorator_names` (extract-functions-ast-py.py:278) ↔ `defaults` (lib/resource_policy.py:78) — score 0.5, signals: winnowing
- `_param_names_from_template` (generate-corpus.py:93) ↔ `defaults` (lib/resource_policy.py:78) — score 0.5, signals: winnowing
- `_actionable_row` (generate_report.py:98) ↔ `defaults` (lib/resource_policy.py:78) — score 0.5, signals: winnowing
- `_signals_lines` (generate_report.py:105) ↔ `defaults` (lib/resource_policy.py:78) — score 0.5, signals: winnowing
- `defaults` (lib/resource_policy.py:78) ↔ `tree_rss_bytes_from_table` (lib/resource_policy.py:144) — score 0.5, signals: winnowing
- `defaults` (lib/resource_policy.py:78) ↔ `_strategy_name_from_path` (merge-signals.py:492) — score 0.5, signals: winnowing
- `defaults` (lib/resource_policy.py:78) ↔ `_iter_scored` (merge-signals.py:681) — score 0.5, signals: winnowing
- `defaults` (lib/resource_policy.py:78) ↔ `__init__` (merge-signals.py:696) — score 0.5, signals: winnowing
- `defaults` (lib/resource_policy.py:78) ↔ `_refusal` (merge-signals.py:804) — score 0.5, signals: winnowing
- `to_dict` (lib/resource_policy.py:101) ↔ `start` (lib/resource_policy.py:343) — score 0.5, signals: winnowing
- `main` (extract-functions-ast-ts.mjs:480) ↔ `main` (generate-corpus.py:351) — score 0.491, signals: fuzzy_name, metric_similarity
- `main` (evaluate.py:198) ↔ `main` (extract-functions-ast-ts.mjs:480) — score 0.487, signals: fuzzy_name, metric_similarity
- `compute_final_score` (detect-fuzzy-names.py:261) ↔ `get_return_type` (detect-signature-match.py:147) — score 0.4, signals: winnowing
- `compute_final_score` (detect-fuzzy-names.py:261) ↔ `_empty_summary` (merge-signals.py:689) — score 0.4, signals: winnowing
- `start` (lib/resource_policy.py:343) ↔ `_empty_summary` (merge-signals.py:689) — score 0.4, signals: winnowing


---

_Report generated by multi-signal duplicate detection pipeline._
_Clone types follow the standard taxonomy: Type 1 (exact), Type 2 (renamed), Type 3 (near-miss), Type 4 (semantic)._
