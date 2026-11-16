"""Test-only in-process admission adapter for pipeline CLI integration tests.

Normal CLI and environment variables cannot select this path. Tests invoke this file
explicitly with the runner path as argv[1].
"""
from __future__ import annotations

import importlib.util
import os
import sys


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("runner path required")
    runner = os.path.abspath(sys.argv[1])
    runner_argv = list(sys.argv[2:])
    test_lock = None
    while "--test-lock-file" in runner_argv:
        index = runner_argv.index("--test-lock-file")
        if test_lock is not None or index + 1 >= len(runner_argv):
            raise SystemExit("--test-lock-file requires one unique path")
        test_lock = os.path.abspath(runner_argv[index + 1])
        del runner_argv[index:index + 2]
    sys.path.insert(0, os.path.dirname(runner))
    spec = importlib.util.spec_from_file_location("dedup_test_runner", runner)
    if spec is None or spec.loader is None:
        raise SystemExit("runner import failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.check_preflight = lambda: (
        True, "ok: isolated test adapter; no live admission assertion")
    if test_lock is not None:
        module.DEFAULT_LOCK_PATH = test_lock
    sys.argv = [runner, *runner_argv]
    module.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
