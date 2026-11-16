#!/usr/bin/env python3
"""
StegaShield E2E Standalone Test Runner.
Executes opaque-box E2E test suites with tier filtering, mode selection,
rich console reporting, and structured JSON / JUnit XML export.

Exit Codes:
  0: All executed tests passed cleanly.
  1: One or more tests failed.
  2: Interrupted by user (SIGINT / KeyboardInterrupt).
  3: Harness environment/configuration error.
  4: Invalid arguments.
  5: No tests collected.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Ensure paths: PROJECT_ROOT must precede BACKEND_DIR so tests/e2e is not shadowed by backend/tests
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

for p in [str(BACKEND_DIR), str(PROJECT_ROOT)]:
    p_str = str(p)
    while p_str in sys.path:
        sys.path.remove(p_str)
    sys.path.insert(0, p_str)

import pytest
from tests.e2e.framework.reporter import E2EReporter
from tests.e2e.framework.env_check import run_full_env_check


class TestResultCollector:
    """Pytest plugin collecting item-level results for E2EReporter."""

    def __init__(self, reporter: E2EReporter):
        self.reporter = reporter

    def pytest_runtest_logreport(self, report):
        if report.when == "call":
            tier = "unknown"
            for t_marker in ["tier1", "tier2", "tier3", "tier4"]:
                if t_marker in report.keywords:
                    tier = t_marker
                    break
            status = "passed" if report.passed else ("skipped" if report.skipped else "failed")
            msg = None
            if report.failed:
                msg = str(report.longrepr)
            self.reporter.record(
                nodeid=report.nodeid,
                tier=tier,
                status=status,
                duration=report.duration,
                message=msg,
            )
        elif report.when == "setup" and report.skipped:
            self.reporter.record(
                nodeid=report.nodeid,
                tier="tier1",
                status="skipped",
                duration=report.duration,
                message="Skipped in setup",
            )


def parse_args(args: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="StegaShield Standalone E2E Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Execute all available test tiers (Tiers 1-4).",
    )
    parser.add_argument(
        "--tier",
        type=str,
        default=None,
        help="Comma-separated tier list to execute (e.g. '1', '1,2', '3,4').",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="auto",
        choices=["auto", "direct_core", "asgi_testclient", "live_http"],
        help="Client adapter execution mode (default: auto).",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL for live_http mode (default: http://127.0.0.1:8000).",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skip slow tests (e.g. 16MP covers).",
    )
    parser.add_argument(
        "--json-report",
        type=str,
        default=None,
        help="Path to output structured JSON report file.",
    )
    parser.add_argument(
        "--junit-xml",
        type=str,
        default=None,
        help="Path to output JUnit XML report file.",
    )
    parser.add_argument(
        "--env-check",
        action="store_true",
        help="Run environment health check and exit.",
    )
    parser.add_argument(
        "--collect-only",
        action="store_true",
        help="Only collect and list matching tests without execution.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose pytest output.",
    )

    try:
        return parser.parse_args(args)
    except SystemExit as e:
        sys.exit(4 if e.code != 0 else 0)


def main() -> int:
    try:
        args = parse_args(sys.argv[1:])
    except Exception:
        return 4

    # Environment check command
    if args.env_check:
        env = run_full_env_check(args.url)
        print("StegaShield Environment Verification:")
        for k, v in env.items():
            print(f"  {k}: {v}")
        return 0 if env["status"] in ("ok", "degraded") else 3

    # Build pytest CLI arguments
    pytest_args = [str(SCRIPT_DIR)]

    # Custom options for StegaShield conftest
    pytest_args.extend([f"--e2e-mode={args.mode}", f"--e2e-url={args.url}"])

    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-q")

    # Marker filtering
    marker_exprs = []
    if args.tier:
        tiers = [f"tier{t.strip()}" for t in args.tier.split(",") if t.strip()]
        if tiers:
            marker_exprs.append(f"({' or '.join(tiers)})")
    elif not args.all:
        # Default if neither --all nor --tier specified is tier1
        marker_exprs.append("tier1")

    if args.quick:
        marker_exprs.append("not slow")

    if marker_exprs:
        pytest_args.extend(["-m", " and ".join(marker_exprs)])

    if args.collect_only:
        pytest_args.append("--collect-only")

    # Reporter and plugin hook
    reporter = E2EReporter(mode=args.mode)
    collector = TestResultCollector(reporter)

    try:
        exit_code = pytest.main(pytest_args, plugins=[collector])
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        return 2
    except Exception as e:
        print(f"\nConfiguration or harness error: {e}")
        return 3

    # Format and write reports
    if not args.collect_only:
        reporter.print_console_summary()

        if args.json_report:
            reporter.write_json_report(args.json_report)
            print(f"JSON report written to: {args.json_report}")

        if args.junit_xml:
            reporter.write_junit_xml(args.junit_xml)
            print(f"JUnit XML report written to: {args.junit_xml}")

    # Map pytest ExitCodes to runner semantics:
    # 0: OK, 1: TESTS_FAILED, 2: INTERRUPTED, 3: INTERNAL_ERROR, 4: USAGE_ERROR, 5: NO_TESTS_COLLECTED
    code_val = int(exit_code)
    if code_val in (0, 1, 2, 3, 4, 5):
        return code_val
    return 1 if code_val > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
