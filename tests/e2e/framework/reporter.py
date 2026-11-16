"""
StegaShield E2E Reporting Framework.
Generates structured JSON summaries, JUnit XML reports, and formatted console outputs.
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET


@dataclass
class TestResultItem:
    nodeid: str
    tier: str
    status: str  # "passed", "failed", "skipped", "error"
    duration: float
    message: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


class E2EReporter:
    """Collects test results and produces structured outputs."""

    def __init__(self, mode: str = "auto"):
        self.mode = mode
        self.start_time = time.time()
        self.items: List[TestResultItem] = []

    def record(
        self,
        nodeid: str,
        tier: str,
        status: str,
        duration: float,
        message: Optional[str] = None,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> None:
        self.items.append(
            TestResultItem(
                nodeid=nodeid,
                tier=tier,
                status=status,
                duration=duration,
                message=message,
                stdout=stdout,
                stderr=stderr,
            )
        )

    def get_summary_dict(self) -> Dict[str, Any]:
        total = len(self.items)
        passed = sum(1 for it in self.items if it.status == "passed")
        failed = sum(1 for it in self.items if it.status == "failed")
        skipped = sum(1 for it in self.items if it.status == "skipped")
        duration = round(time.time() - self.start_time, 3)

        # Breakdown by tier
        tier_breakdown: Dict[str, Dict[str, int]] = {}
        for it in self.items:
            t = it.tier or "unknown"
            if t not in tier_breakdown:
                tier_breakdown[t] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
            tier_breakdown[t]["total"] += 1
            if it.status in tier_breakdown[t]:
                tier_breakdown[t][it.status] += 1

        return {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": self.mode,
            "python_version": sys.version.split()[0],
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "duration_seconds": duration,
            },
            "tiers": tier_breakdown,
            "results": [
                {
                    "nodeid": it.nodeid,
                    "tier": it.tier,
                    "status": it.status,
                    "duration": round(it.duration, 4),
                    "error_message": it.message if it.status in ("failed", "error") else None,
                }
                for it in self.items
            ],
        }

    def write_json_report(self, filepath: str) -> None:
        """Writes structured JSON report to target path."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        data = self.get_summary_dict()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def write_junit_xml(self, filepath: str) -> None:
        """Writes JUnit XML test report."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        summary = self.get_summary_dict()["summary"]
        testsuites = ET.Element("testsuites", {
            "name": "StegaShield E2E Test Suite",
            "tests": str(summary["total"]),
            "failures": str(summary["failed"]),
            "time": str(summary["duration_seconds"]),
        })

        testsuite = ET.SubElement(testsuites, "testsuite", {
            "name": "E2E Tests",
            "tests": str(summary["total"]),
            "failures": str(summary["failed"]),
            "skipped": str(summary["skipped"]),
            "time": str(summary["duration_seconds"]),
        })

        for it in self.items:
            tc = ET.SubElement(testsuite, "testcase", {
                "name": it.nodeid.split("::")[-1],
                "classname": it.nodeid.split("::")[0],
                "time": str(round(it.duration, 4)),
            })
            if it.status == "failed":
                fail = ET.SubElement(tc, "failure", {
                    "message": it.message or "Test failed",
                })
                fail.text = it.message or ""
            elif it.status == "skipped":
                ET.SubElement(tc, "skipped")

        tree = ET.ElementTree(testsuites)
        tree.write(filepath, encoding="utf-8", xml_declaration=True)

    def print_console_summary(self) -> None:
        """Prints a colored terminal summary of test execution."""
        summary = self.get_summary_dict()["summary"]
        tiers = self.get_summary_dict()["tiers"]

        green = "\033[92m"
        red = "\033[91m"
        yellow = "\033[93m"
        cyan = "\033[96m"
        bold = "\033[1m"
        reset = "\033[0m"

        print("\n" + "=" * 70)
        print(f"{bold}{cyan}STEGASHIELD E2E TEST EXECUTION SUMMARY{reset} [Mode: {self.mode}]")
        print("=" * 70)

        for t_name, t_data in sorted(tiers.items()):
            p_rate = (t_data['passed'] / t_data['total'] * 100) if t_data['total'] > 0 else 0
            color = green if t_data['failed'] == 0 else red
            print(f"  {bold}{t_name:<30}{reset} Total: {t_data['total']:<4} Passed: {color}{t_data['passed']:<4}{reset} Failed: {t_data['failed']:<4} ({p_rate:.1f}%)")

        print("-" * 70)
        overall_color = green if summary['failed'] == 0 else red
        print(
            f"TOTAL: {summary['total']} | "
            f"PASSED: {green}{summary['passed']}{reset} | "
            f"FAILED: {overall_color}{summary['failed']}{reset} | "
            f"SKIPPED: {yellow}{summary['skipped']}{reset} | "
            f"DURATION: {summary['duration_seconds']:.2f}s"
        )
        print("=" * 70 + "\n")
