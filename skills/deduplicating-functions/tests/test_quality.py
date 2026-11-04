"""Positive and planted-fault controls for the repository quality gate."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ENGINE = Path(__file__).resolve().parents[1] / "run_quality.py"
spec = importlib.util.spec_from_file_location("quality", ENGINE)
quality = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quality)


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / "src").mkdir()
        self.source = self.root / "src/a.py"
        self.source.write_text("def answer(x: int) -> int:\n    return x + 1\n")
        self.policy = {"schema": 1, "groups": {"production": ["src/"]},
                       "extensions": [".py"]}

    def analyze(self):
        return quality.analyze(self.root, self.policy)

    def test_baseline_is_read_only_and_current_source_is_measured(self):
        baseline = self.analyze()
        original = json.dumps(baseline)
        self.assertEqual(quality.compare(self.analyze(), baseline), [])
        self.source.write_text(self.source.read_text() + "\nextra = 1\n")
        self.assertTrue(quality.compare(self.analyze(), baseline))
        self.assertEqual(json.dumps(baseline), original)

    def test_baseline_publication_never_overwrites_an_existing_file(self):
        path = self.root / "baseline.json"
        quality.write_json(path, {"first": True}, exclusive=True)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            quality.write_json(path, {"second": True}, exclusive=True)
        self.assertEqual(path.read_bytes(), original)

    def test_partial_serialization_never_publishes_a_baseline(self):
        before = set(self.root.iterdir())
        def failed(value, stream, **kwargs):
            stream.write('{"partial":')
            raise OSError("seeded full disk")
        with mock.patch.object(quality.json, "dump", side_effect=failed), self.assertRaises(OSError):
            quality.write_json(self.root / "baseline.json", {}, exclusive=True)
        self.assertEqual(set(self.root.iterdir()), before)

    def test_minification_does_not_hide_ast_growth(self):
        baseline = self.analyze()
        self.source.write_text("def answer(x: int) -> int:\n    a = 1; b = 2; return x + a + b\n")
        errors = quality.compare(self.analyze(), baseline)
        self.assertTrue(any("nodes" in error for error in errors), errors)

    def test_missing_empty_ambiguous_and_unclassified_scopes_fail(self):
        for groups in ({"production": ["absent/"]},
                       {"production": ["src/"], "tests": ["src/"]},
                       {"production": ["other/"]}):
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                quality.analyze(self.root, dict(self.policy, groups=groups))
        self.source.unlink()
        with self.assertRaises(ValueError):
            self.analyze()

    def test_parser_failure_is_not_zero_functions(self):
        self.source.write_text("def broken(:\n")
        with self.assertRaises(SyntaxError):
            self.analyze()

    def test_source_change_during_analysis_is_rejected(self):
        original = quality.python_functions
        def changing(source, name, root):
            result = original(source, name, root)
            self.source.write_text(source + "extra = 1\n")
            return result
        with mock.patch.object(quality, "python_functions", side_effect=changing):
            with self.assertRaisesRegex(ValueError, "changed during analysis"):
                self.analyze()

    def test_policy_reclassification_and_parser_drift_fail(self):
        baseline = self.analyze()
        current = quality.analyze(self.root, dict(self.policy, groups={"tooling": ["src/"]}))
        self.assertTrue(quality.compare(current, baseline))
        current = self.analyze()
        current["parsers"]["python"] = "different"
        self.assertTrue(quality.compare(current, baseline))

    def test_helper_change_requires_new_review_even_when_counts_match(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = Path(directory)
            for name in quality.ENGINE_FILES:
                path = engine / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((quality.BASE / name).read_bytes())
            with mock.patch.object(quality, "BASE", engine):
                baseline = self.analyze()
                helper = engine / "scripts/extract-functions-ast-py.py"
                helper.write_text(helper.read_text() + "\n# Provenance drift fixture.\n")
                current = self.analyze()
                self.assertEqual(current["totals"], baseline["totals"])
                self.assertTrue(any("analyzer_files" in error for error in quality.compare(current, baseline)))
    def test_changed_constants_operators_types_and_calls_are_not_exact(self):
        source = "def allow(x: int) -> bool:\n    return service.read(x) == 1\n"
        variants = [source.replace("read", "write"), source.replace("1", "2"),
                    source.replace("==", "!="), source.replace("int", "str")]
        for variant in variants:
            self.source.write_text(source + "\n" + variant.replace("allow", "deny"))
            self.assertEqual(self.analyze()["duplicate_candidates"], [])
        self.source.write_text(source + "\n" + source.replace("allow", "alias"))
        self.assertEqual(len(self.analyze()["duplicate_candidates"]), 1)

    def test_symlink_source_fails(self):
        self.source.rename(self.root / "outside.py")
        self.source.symlink_to(self.root / "outside.py")
        with self.assertRaises(ValueError):
            self.analyze()

    def test_cli_failure_replaces_stale_success_receipt(self):
        policy = self.root / "policy.json"
        policy.write_text(json.dumps(self.policy))
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps(self.analyze()))
        report = self.root / "report.json"
        report.write_text('{"status":"pass"}')
        self.source.write_text("def broken(:\n")
        result = subprocess.run([sys.executable, str(ENGINE), "--root", str(self.root),
                                 "--policy", str(policy), "--baseline", str(baseline),
                                 "--report", str(report)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(report.read_text())["status"], "incomplete")

    def test_swift_compiler_ranges_preserve_literals_and_unicode(self):
        self.source.unlink()
        swift = self.root / "src/a.swift"
        swift.write_text('func answer(_ café: Int) -> Int {\n  café + 1\n}\n')
        self.policy["extensions"] = [".swift"]
        current = self.analyze()
        functions = current["files"][0]["functions"]
        self.assertEqual(len(functions), 1)
        self.assertEqual((functions[0]["line"], functions[0]["end_line"]), (1, 3))
        fingerprint = functions[0]["syntax_sha256"]
        swift.write_text(swift.read_text().replace("+ 1", "+ 2"))
        self.assertNotEqual(self.analyze()["files"][0]["functions"][0]["syntax_sha256"], fingerprint)
        swift.write_text("func broken( {\n")
        with self.assertRaises(ValueError):
            self.analyze()

    def test_missing_swift_parser_cannot_pass(self):
        self.source.unlink()
        (self.root / "src/a.swift").write_text("func a() {}\n")
        self.policy["extensions"] = [".swift"]
        original = quality.command
        def missing(argv, cwd=None):
            if argv[0] == "xcrun":
                raise FileNotFoundError("seeded missing compiler")
            return original(argv, cwd)
        with mock.patch.object(quality, "command", side_effect=missing), self.assertRaises(FileNotFoundError):
            self.analyze()

    def test_swift_function_types_and_parentheses_in_strings_are_valid(self):
        self.source.unlink()
        (self.root / "src/a.swift").write_text(
            'struct Example {\n var name: String { "(café)" }\n'
            ' func send(_ callback: (String) -> Void) {\n // Internal comment remains intact.\n callback("(done)") }\n}\n')
        self.policy["extensions"] = [".swift"]
        current = self.analyze()
        self.assertEqual(current["totals"]["total"]["functions"], 2)
        self.assertGreater(current["totals"]["total"]["nodes"], 10)

    def test_unpublished_report_is_not_success(self):
        policy = self.root / "policy.json"
        policy.write_text(json.dumps(self.policy))
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps(self.analyze()))
        result = subprocess.run([sys.executable, str(ENGINE), "--root", str(self.root),
                                 "--policy", str(policy), "--baseline", str(baseline),
                                 "--report", str(self.root / "absent/report.json")], capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_empty_toolchain_banner_replaces_stale_success(self):
        (self.root / "src/a.sh").write_text("true\n")
        self.policy["extensions"].append(".sh")
        policy, baseline, report = [self.root / name for name in ("policy.json", "baseline.json", "report.json")]
        policy.write_text(json.dumps(self.policy))
        baseline.write_text("{}")
        report.write_text('{"status":"pass"}')
        original = quality.command
        def empty_banner(argv, cwd=None):
            return "" if argv == ["bash", "--version"] else original(argv, cwd)
        argv = [str(ENGINE), "--root", str(self.root), "--policy", str(policy),
                "--baseline", str(baseline), "--report", str(report)]
        with mock.patch.object(quality, "command", side_effect=empty_banner), mock.patch.object(sys, "argv", argv):
            self.assertEqual(quality.main(), 2)
        self.assertEqual(json.loads(report.read_text())["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
