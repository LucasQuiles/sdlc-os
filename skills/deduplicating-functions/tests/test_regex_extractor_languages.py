"""Language coverage regression tests for the regex extractor.

These tests lock the portable Python implementation of
extract-functions-regex that replaced the BSD-grep-incompatible
shell version. They verify that each advertised language actually
produces non-empty catalogs on real source fixtures.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

import pytest

PYTHON = sys.executable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGEX_EXTRACTOR = os.path.join(BASE, "scripts", "extract-functions-regex.py")
REGEX_SHIM = os.path.join(BASE, "scripts", "extract-functions-regex.sh")


GO_SOURCE = '''\
package main

import "fmt"

func Calculate(items []int) int {
    sum := 0
    for _, v := range items {
        sum += v
    }
    return sum
}

func computeTotal(values []int) int {
    total := 0
    for _, v := range values {
        total += v
    }
    return total
}

type User struct {
    Name string
}

func (u *User) Greet() string {
    return fmt.Sprintf("Hello, %s", u.Name)
}

func main() {
    fmt.Println(Calculate([]int{1, 2, 3}))
}
'''

RUST_SOURCE = '''\
fn calculate(items: &[i32]) -> i32 {
    let mut sum = 0;
    for v in items {
        sum += v;
    }
    sum
}

pub fn compute_total(values: &[i32]) -> i32 {
    let mut total = 0;
    for v in values {
        total += v;
    }
    total
}

struct User {
    name: String,
}

impl User {
    pub fn greet(&self) -> String {
        format!("Hello, {}", self.name)
    }
}

fn main() {
    println!("{}", calculate(&[1, 2, 3]));
}
'''

JAVA_SOURCE = '''\
public class Sample {
    public static int calculate(int[] items) {
        int sum = 0;
        for (int v : items) {
            sum += v;
        }
        return sum;
    }

    public int computeTotal(int[] values) {
        int total = 0;
        for (int v : values) {
            total += v;
        }
        return total;
    }

    public String greet(String name) {
        return "Hello, " + name;
    }

    public static void main(String[] args) {
        System.out.println(calculate(new int[]{1, 2, 3}));
    }
}
'''

KOTLIN_SOURCE = '''\
fun calculate(items: IntArray): Int {
    var sum = 0
    for (v in items) {
        sum += v
    }
    return sum
}

fun computeTotal(values: IntArray): Int {
    var total = 0
    for (v in values) {
        total += v
    }
    return total
}
'''

PYTHON_SOURCE = '''\
def calculate(items):
    total = 0
    for item in items:
        total += item
    return total


def compute_sum(values):
    s = 0
    for v in values:
        s += v
    return s


class Calculator:
    def add(self, a, b):
        return a + b

    def _private_helper(self):
        pass
'''

TS_SOURCE = '''\
export function calculate(items: number[]): number {
    let sum = 0;
    for (const v of items) {
        sum += v;
    }
    return sum;
}

export const computeTotal = (values: number[]): number => {
    return values.reduce((acc, v) => acc + v, 0);
};

class Calculator {
    public add(a: number, b: number): number {
        return a + b;
    }

    private privateHelper(): void {}
}
'''


LANGUAGE_FIXTURES = [
    ("go", "sample.go", GO_SOURCE, 4),
    ("rust", "sample.rs", RUST_SOURCE, 4),
    ("java", "Sample.java", JAVA_SOURCE, 4),
    ("kotlin", "sample.kt", KOTLIN_SOURCE, 2),
    ("python", "sample.py", PYTHON_SOURCE, 4),
    ("typescript", "sample.ts", TS_SOURCE, 4),
]


@pytest.fixture
def tmp_source_dir(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    return str(src)


def _run_extractor(source_dir: str, lang: str | None = None) -> list[dict]:
    """Invoke the Python regex extractor and return the parsed catalog."""
    cmd = [PYTHON, REGEX_EXTRACTOR, source_dir]
    if lang:
        cmd.extend(["--lang", lang])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, (
        f"extractor failed: {result.stderr[-500:]}"
    )
    # Find JSON start in stdout (stderr has the "Scanning for..." messages)
    stdout = result.stdout.strip()
    return json.loads(stdout)


@pytest.mark.parametrize("lang,filename,source,expected_count", LANGUAGE_FIXTURES)
def test_regex_extractor_handles_language(
    tmp_source_dir, lang, filename, source, expected_count
):
    """Regex extractor must produce non-empty catalogs for each advertised language."""
    path = os.path.join(tmp_source_dir, filename)
    with open(path, "w") as f:
        f.write(source)

    functions = _run_extractor(tmp_source_dir, lang=lang)

    assert len(functions) >= expected_count, (
        f"{lang}: expected at least {expected_count} functions, got {len(functions)}.\n"
        f"Extracted: {[(f['name'], f['line']) for f in functions]}"
    )

    # Lock the language metadata field — each function must report the correct language
    for func in functions:
        assert func["language"] == lang, (
            f"{lang}: function {func['name']} has language={func['language']!r}, expected {lang!r}"
        )


@pytest.mark.parametrize("lang,filename,source,expected_count", LANGUAGE_FIXTURES)
def test_regex_extractor_preserves_function_names(
    tmp_source_dir, lang, filename, source, expected_count
):
    """Extracted function names must match what the source declares."""
    path = os.path.join(tmp_source_dir, filename)
    with open(path, "w") as f:
        f.write(source)

    functions = _run_extractor(tmp_source_dir, lang=lang)
    names = {f["name"] for f in functions}

    # Each fixture has known function names — verify the key ones appear
    expected_samples = {
        "go": {"Calculate", "computeTotal", "main"},
        "rust": {"calculate", "compute_total", "main"},
        "java": {"calculate", "computeTotal", "greet"},
        "kotlin": {"calculate", "computeTotal"},
        "python": {"calculate", "compute_sum", "add"},
        "typescript": {"calculate", "add"},
    }

    expected = expected_samples[lang]
    missing = expected - names
    assert not missing, (
        f"{lang} ({filename}): missing expected names {missing}. "
        f"Got: {sorted(names)}"
    )


def test_extractor_output_has_required_fields(tmp_source_dir):
    """Every extracted function must have the fields downstream detectors need."""
    with open(os.path.join(tmp_source_dir, "sample.go"), "w") as f:
        f.write(GO_SOURCE)

    functions = _run_extractor(tmp_source_dir, lang="go")
    assert functions, "Expected at least one function"

    required_fields = {
        "file", "name", "qualified_name", "line", "end_line", "signature",
        "params", "body_lines", "export_type", "language", "context",
    }
    for func in functions:
        missing = required_fields - set(func.keys())
        assert not missing, (
            f"Function {func.get('name', '?')} missing fields: {missing}"
        )
        assert func["line"] > 0
        assert func["body_lines"] >= 1
        assert func["language"] == "go"


def test_extractor_is_deterministic(tmp_source_dir):
    """Two runs against the same source must produce identical output."""
    with open(os.path.join(tmp_source_dir, "sample.go"), "w") as f:
        f.write(GO_SOURCE)
    with open(os.path.join(tmp_source_dir, "sample.rs"), "w") as f:
        f.write(RUST_SOURCE)

    run1 = _run_extractor(tmp_source_dir)
    run2 = _run_extractor(tmp_source_dir)
    assert run1 == run2, "Regex extractor output is nondeterministic"


def test_extractor_auto_detects_languages(tmp_source_dir):
    """Without --lang, the extractor should auto-detect and process all languages."""
    with open(os.path.join(tmp_source_dir, "sample.go"), "w") as f:
        f.write(GO_SOURCE)
    with open(os.path.join(tmp_source_dir, "sample.rs"), "w") as f:
        f.write(RUST_SOURCE)
    with open(os.path.join(tmp_source_dir, "Sample.java"), "w") as f:
        f.write(JAVA_SOURCE)

    functions = _run_extractor(tmp_source_dir)
    langs_found = {f["language"] for f in functions}
    assert "go" in langs_found, f"Go not in {langs_found}"
    assert "rust" in langs_found, f"Rust not in {langs_found}"
    assert "java" in langs_found, f"Java not in {langs_found}"


def test_shim_shell_script_delegates_to_python(tmp_source_dir):
    """The .sh shim must produce identical output to the .py script."""
    with open(os.path.join(tmp_source_dir, "sample.go"), "w") as f:
        f.write(GO_SOURCE)

    # Run both and compare
    py_result = subprocess.run(
        [PYTHON, REGEX_EXTRACTOR, "--lang", "go", tmp_source_dir],
        capture_output=True, text=True, timeout=30,
    )
    sh_result = subprocess.run(
        ["bash", REGEX_SHIM, "--lang", "go", tmp_source_dir],
        capture_output=True, text=True, timeout=30,
    )
    assert py_result.returncode == 0
    assert sh_result.returncode == 0

    py_data = json.loads(py_result.stdout.strip())
    sh_data = json.loads(sh_result.stdout.strip())
    assert py_data == sh_data, "Shim output differs from direct Python invocation"
