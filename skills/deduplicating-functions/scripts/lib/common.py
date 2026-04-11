"""Shared helpers for duplicate-function detection scripts.

This module consolidates functions and constants that were previously duplicated
across detect-fuzzy-names.py, detect-signature-match.py, detect-token-clones.py,
detect-ast-similarity.py, and detect-metric-similarity.py.
"""
from __future__ import annotations


import hashlib
import re
from typing import Any


def stable_hash(value: Any) -> int:
    """Process-stable hash — deterministic across runs.

    Python's built-in hash() is randomized per process (PYTHONHASHSEED),
    making set/dict ordering and fingerprints nondeterministic. This uses
    SHA-256 truncated to signed 64-bit int for stable ordering.

    Accepts any value: tuples of strings (k-grams), nested tuples
    (PDG neighborhoods), or anything with a stable repr().
    """
    if isinstance(value, tuple) and all(isinstance(v, str) for v in value):
        data = "\x00".join(value).encode("utf-8")
    else:
        data = repr(value).encode("utf-8")
    digest = hashlib.sha256(data).digest()
    return int.from_bytes(digest[:8], "big", signed=True)


# ---------------------------------------------------------------------------
# KEYWORDS — union of Python + JS/TS keywords used by tokenizers
# ---------------------------------------------------------------------------

KEYWORDS: frozenset[str] = frozenset({
    # JS/TS
    "async", "await", "break", "case", "catch", "class", "const", "continue",
    "debugger", "default", "delete", "do", "else", "enum", "export", "extends",
    "false", "finally", "for", "function", "if", "import", "in", "instanceof",
    "let", "new", "null", "of", "return", "super", "switch", "this", "throw",
    "true", "try", "typeof", "undefined", "var", "void", "while", "with",
    "yield", "interface", "type", "implements", "static", "public", "private",
    "protected", "abstract", "as", "from", "get", "set", "readonly",
    # Python
    "def", "lambda", "pass", "raise", "except", "nonlocal",
    "global", "assert", "elif", "is", "not", "and", "or", "None", "True",
    "False", "print", "self", "cls",
})


# ---------------------------------------------------------------------------
# Compiled regex patterns for code tokenizers
# ---------------------------------------------------------------------------

# Operators (multi-char first so we match greedily)
OPERATOR_RE: re.Pattern[str] = re.compile(
    r"===|!==|==|!=|<=|>=|=>|&&|\|\||<<|>>|>>>|\?\?|\?\.|"
    r"\+\+|--|[+\-*/%&|^~<>!=?:]"
)

# String literal patterns (simplified -- handles common cases)
STRING_RE: re.Pattern[str] = re.compile(
    r"""(?:"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)"""
)

# Number literal
NUMBER_RE: re.Pattern[str] = re.compile(
    r"\b(?:0x[\da-fA-F]+|0b[01]+|0o[0-7]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b"
)

# Identifier
IDENT_RE: re.Pattern[str] = re.compile(r"\b[a-zA-Z_$][\w$]*\b")

# Punctuation
PUNCT_RE: re.Pattern[str] = re.compile(r"[(){}\[\];,.]")


# ---------------------------------------------------------------------------
# tokenize() — split camelCase / snake_case / kebab-case names into tokens
# ---------------------------------------------------------------------------

def tokenize(name: str) -> list[str]:
    """Split a function/parameter name into lowercase tokens.

    Handles camelCase, PascalCase, snake_case, kebab-case, and mixed styles.

    Examples::

        >>> tokenize("getUserById")
        ['get', 'user', 'by', 'id']
        >>> tokenize("format_date")
        ['format', 'date']
        >>> tokenize("XMLParser")
        ['xml', 'parser']
    """
    # Insert boundary between lowercase->uppercase and uppercase->lowercase-run
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    # Split on non-alphanumeric characters
    tokens = re.split(r"[^a-zA-Z0-9]+", s)
    return [t.lower() for t in tokens if t]


# ---------------------------------------------------------------------------
# tokenize_to_typed() — code tokenizer returning list[dict[str, str]]
# ---------------------------------------------------------------------------

def tokenize_to_typed(code: str) -> list[dict[str, str]]:
    """Tokenize a code string into typed token dicts.

    Returns a list of ``{"type": ..., "value": ...}`` dicts where type is one
    of: keyword, identifier, string, number, operator, punctuation.

    Comments and whitespace are stripped.
    """
    return _tokenize_core(code, typed=True)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# tokenize_to_strings() — code tokenizer returning list[str]
# ---------------------------------------------------------------------------

def tokenize_to_strings(code: str) -> list[str]:
    """Tokenize a code string into a flat list of token value strings.

    Comments and whitespace are stripped.  Used when only the raw token values
    are needed (e.g. for n-gram or LCS comparison).
    """
    return _tokenize_core(code, typed=False)  # type: ignore[return-value]


def _tokenize_core(code: str, typed: bool) -> list[dict[str, str]] | list[str]:
    """Shared scanning core for both tokenizer variants."""
    tokens: list = []
    pos = 0
    length = len(code)

    _MATCHERS: list[tuple[re.Pattern[str], str]] = [
        (STRING_RE, "string"),
        (NUMBER_RE, "number"),
        (IDENT_RE, "identifier"),  # keywords handled below
        (OPERATOR_RE, "operator"),
        (PUNCT_RE, "punctuation"),
    ]

    while pos < length:
        ch = code[pos]

        # Skip whitespace
        if ch in " \t\n\r":
            pos += 1
            continue

        # Skip single-line comments (// and #)
        if (ch == "/" and pos + 1 < length and code[pos + 1] == "/") or ch == "#":
            end = code.find("\n", pos)
            pos = end + 1 if end != -1 else length
            continue

        # Skip block comments
        if ch == "/" and pos + 1 < length and code[pos + 1] == "*":
            end = code.find("*/", pos + 2)
            pos = end + 2 if end != -1 else length
            continue

        # Try each regex matcher
        matched = False
        for pattern, tok_type in _MATCHERS:
            m = pattern.match(code, pos)
            if m:
                val = m.group()
                if tok_type == "identifier" and val in KEYWORDS:
                    tok_type = "keyword"
                if typed:
                    tokens.append({"type": tok_type, "value": val})
                else:
                    tokens.append(val)
                pos = m.end()
                matched = True
                break

        if not matched:
            pos += 1  # Unknown character — skip

    return tokens


# ---------------------------------------------------------------------------
# jaccard() — set similarity (returns 0.0 for empty sets)
# ---------------------------------------------------------------------------

def jaccard(a: set[Any], b: set[Any]) -> float:
    """Jaccard similarity between two sets.

    Returns 0.0 when both sets are empty (mathematical convention: the
    intersection-over-union of two empty sets is undefined, and we default to
    0.0 rather than 1.0 to avoid inflating similarity scores for missing data).
    """
    if not a and not b:
        return 0.0
    intersection_size = len(a & b)
    union_size = len(a) + len(b) - intersection_size
    if union_size == 0:
        return 0.0
    return intersection_size / union_size


# ---------------------------------------------------------------------------
# overlap_coefficient() — asymmetric set similarity (NIL technique)
# ---------------------------------------------------------------------------

def overlap_coefficient(a: set[Any], b: set[Any]) -> float:
    """Overlap coefficient: |A intersection B| / min(|A|, |B|).

    Asymmetric measure — a small function fully contained in a larger one
    scores 1.0. Complements Jaccard for partial clone detection (NIL technique).
    Returns 0.0 when either set is empty.
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


# ---------------------------------------------------------------------------
# should_compare() — pair-filtering predicate
# ---------------------------------------------------------------------------

def should_compare(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Decide whether two catalog entries should be compared.

    Returns ``False`` for self-pairs (same file + same line) and for entries
    in the same file whose qualified name (or plain name) is identical.
    """
    # Same entry (same file + same line) — guard against None==None (F-01)
    file_a, file_b = a.get("file"), b.get("file")
    line_a, line_b = a.get("line"), b.get("line")
    if file_a is not None and file_b is not None and line_a is not None and line_b is not None:
        if file_a == file_b and line_a == line_b:
            return False
    elif file_a is None and file_b is None and line_a is None and line_b is None:
        # Both completely missing metadata — compare by name if names differ
        name_a = a.get("qualified_name", a.get("name", ""))
        name_b = b.get("qualified_name", b.get("name", ""))
        return name_a != name_b

    # Same file: only compare if qualified names differ
    if a.get("file") == b.get("file"):
        qa = a.get("qualified_name", a.get("name", ""))
        qb = b.get("qualified_name", b.get("name", ""))
        return qa != qb

    return True


# ---------------------------------------------------------------------------
# func_key() / func_ref() — canonical identifiers for function entries
# ---------------------------------------------------------------------------

def func_key(func: dict[str, Any]) -> str:
    """Return a unique key for a function entry (``file:line``).

    Handles missing fields gracefully by defaulting to ``"?"`` for file and
    ``0`` for line.
    """
    return f"{func.get('file', '?')}:{func.get('line', 0)}"


def func_ref(func: dict[str, Any]) -> dict[str, Any]:
    """Return a minimal reference dict for output serialization.

    Handles missing fields gracefully by defaulting to ``"unknown"`` for name
    and file, and ``0`` for line.
    """
    return {
        "name": func.get("name", "unknown"),
        "file": func.get("file", "unknown"),
        "line": func.get("line", 0),
    }
