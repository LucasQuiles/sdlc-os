# Clone Detection Taxonomy

## Standard Clone Types

The software engineering research community classifies code clones into four types, ordered by detection difficulty:

### Type 1 — Exact Clones

Identical code fragments except for variations in whitespace, layout, and comments.

**Example:**
```python
# Original
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total

# Type 1 clone (different formatting)
def calculate_total(items):
    total=0
    for item in items:
        total+=item.price*item.quantity
    return total
```

**Detection:** Token sequence hashing (after whitespace normalization)
**Our tools:** `detect-token-clones.py` (raw hash mode)

### Type 2 — Renamed Clones

Syntactically identical fragments except for variations in identifiers, literals, types, whitespace, layout, and comments.

**Example:**
```python
# Original
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total

# Type 2 clone (renamed identifiers)
def compute_sum(products):
    result = 0
    for product in products:
        result += product.cost * product.count
    return result
```

**Detection:** Normalized token hashing (replace identifiers with placeholders)
**Our tools:** `detect-token-clones.py` (normalized mode), AST fingerprint comparison

### Type 3 — Near-Miss Clones

Copied fragments with further modifications such as changed, added, or removed statements, in addition to variations in identifiers, literals, types, whitespace, layout, and comments.

**Example:**
```python
# Original
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total

# Type 3 clone (added discount logic)
def calculate_discounted_total(items, discount_rate):
    total = 0
    for item in items:
        subtotal = item.price * item.quantity
        total += subtotal * (1 - discount_rate)
    return total
```

**Detection:** AST n-gram similarity, LCS on token sequences, metric comparison
**Our tools:** `detect-ast-similarity.py`, `detect-metric-similarity.py`

### Type 4 — Semantic Clones

Functionally equivalent fragments implemented using different syntactic constructs.

**Example:**
```python
# Original (imperative)
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total

# Type 4 clone (functional)
def calculate_total(items):
    return sum(item.price * item.quantity for item in items)
```

**Detection:** LLM semantic analysis, behavioral comparison
**Our tools:** LLM semantic phase (opus subagent), `detect-fuzzy-names.py` + `detect-signature-match.py` (heuristic)

## Detection Strategy Matrix

| Strategy | Type 1 | Type 2 | Type 3 | Type 4 |
|----------|--------|--------|--------|--------|
| Token clone detection | **Strong** | **Strong** | Weak | None |
| AST fingerprint | **Strong** | **Strong** | Weak | None |
| AST n-gram similarity | Strong | Strong | **Strong** | Weak |
| Metric similarity | Moderate | Moderate | **Strong** | Moderate |
| Fuzzy name matching | None | Moderate | Moderate | **Moderate** |
| Signature matching | Moderate | Moderate | Moderate | **Strong** |
| LLM semantic analysis | Strong | Strong | Strong | **Strong** |

## Defense in Depth

The multi-signal approach means:

1. **Type 1/2 clones** are caught by 3-4 strategies simultaneously → automatic HIGH confidence
2. **Type 3 clones** are caught by 2-3 strategies → MEDIUM-HIGH confidence
3. **Type 4 clones** require LLM analysis but fuzzy names + signatures provide early warning

A pair flagged by only one strategy (especially a heuristic one) gets LOW confidence, preventing false positives. A pair flagged by 3+ independent strategies gets HIGH confidence regardless of individual scores — the agreement IS the evidence.

## References

- Roy, C.K. & Cordy, J.R. (2007). "A Survey on Software Clone Detection Research"
- Rattan, D. et al. (2013). "Software Clone Detection: A Systematic Review"
- Svajlenko, J. & Roy, C.K. (2015). "Evaluating Clone Detection Tools with BigCloneBench"
