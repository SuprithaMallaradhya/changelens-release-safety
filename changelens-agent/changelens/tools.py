"""Deterministic ChangeLens tool adapters."""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

from .models import EvidenceReport, ToolResult, ToolStatus
from .runner import run_command
from .scenarios import Scenario, scenario_changed_files


def analyze_scenario(root: Path, scenario: Scenario, timeout: int) -> ToolResult:
    patch = scenario.directory / "change.patch"
    if patch.exists():
        relative_patch = patch.relative_to(root)
        result = run_command("scenario-patch-check", ["git", "apply", "--check", str(relative_patch)], root, timeout)
        result.stdout = (result.stdout + "\nchanged files: " + ", ".join(scenario_changed_files(scenario))).strip()
        patch_text = patch.read_text()
        if "-        public OrderStatus status;" in patch_text:
            result.stdout += "\napi finding: required response field status removed"
        return result
    fixture = scenario.directory / "kubernetes.yaml"
    if fixture.exists():
        return ToolResult("scenario-fixture-analysis", f"inspect {fixture.relative_to(root)}", ToolStatus.PASSED, 0, 0,
                          "changed files: " + ", ".join(scenario_changed_files(scenario)), "")
    return ToolResult("scenario-analysis", "scenario manifest lookup", ToolStatus.FAILED, 1, 0, "",
                      "Scenario has no patch or fixture")


def check_health(base_url: str, timeout: int) -> ToolResult:
    started = time.monotonic()
    url = base_url.rstrip("/") + "/actuator/health"
    command = f"GET {url}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode()
            status = ToolStatus.PASSED if response.status == 200 else ToolStatus.FAILED
            return ToolResult("application-health", command, status, 0 if status == ToolStatus.PASSED else response.status,
                              int((time.monotonic() - started) * 1000), body, "")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return ToolResult("application-health", command, ToolStatus.UNAVAILABLE, None,
                          int((time.monotonic() - started) * 1000), "", str(exc))


def run_maven(root: Path, timeout: int, env=None) -> ToolResult:
    return run_command("maven-tests", ["mvn", "test"], root / "demo-app" / "order-api", timeout, env)


def run_python_tests(root: Path, test_module: str, timeout: int, env=None) -> ToolResult:
    return run_command(f"{test_module}-tests", [sys.executable, "-m", "unittest", test_module],
                       root, timeout, env)


def run_security(root: Path, scenario: Scenario, timeout: int, env=None) -> ToolResult:
    fixture = scenario.directory / "kubernetes.yaml"
    if not fixture.exists():
        return ToolResult("security-fixture-validator", "not applicable: no security fixture", ToolStatus.PASSED, 0, 0,
                          "No infrastructure security fixture for this scenario", "")
    return run_command("security-fixture-validator",
                       [sys.executable, "tests/check_security_fixture.py", str(fixture.relative_to(root))], root, timeout, env)


def run_api_contract(root: Path, base_url: str, timeout: int, env=None) -> ToolResult:
    return run_command("api-contract-check", [sys.executable, "tests/check_openapi_contract.py",
                                               "--base-url", base_url], root, timeout, env)


def run_load_test(root: Path, base_url: str, output: Path, timeout: int, env=None) -> ToolResult:
    output.parent.mkdir(parents=True, exist_ok=True)
    return run_command("baseline-load-test", [sys.executable, "load-tests/baseline.py", "--base-url", base_url,
                                               "--concurrency", "4", "--duration", "30", "--output", str(output)],
                       root, timeout, env)


def enrich_report(report: EvidenceReport, result: ToolResult) -> None:
    if result.status in (ToolStatus.FAILED, ToolStatus.TIMED_OUT, ToolStatus.UNAVAILABLE):
        if result.stderr:
            report.errors.append(f"{result.name}: {result.stderr.strip()}")
        elif result.stdout:
            report.errors.append(f"{result.name}: {result.stdout.strip()}")
        else:
            report.errors.append(f"{result.name}: {result.status.value}")
    if result.name == "maven-tests":
        report.tests.update({"status": result.status.value, "exit_code": result.exit_code})
        match = re.search(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)", result.stdout)
        if match:
            report.tests.update({"run": int(match.group(1)), "failed": int(match.group(2)),
                                 "errors": int(match.group(3)), "skipped": int(match.group(4))})
        details = re.findall(r"^\[ERROR\]\s+([^\n]+?)\s+Time elapsed: [^\n]+<<< FAILURE!$",
                             result.stdout, flags=re.MULTILINE)
        details.extend(re.findall(r"^\[ERROR\]\s+([^\n]*(?:AssertionError|PathNotFoundException)[^\n]*)$",
                                  result.stdout, flags=re.MULTILINE))
        if details:
            report.tests["failure_details"] = list(dict.fromkeys(item.strip() for item in details))[:20]
    elif result.name == "security-fixture-validator":
        report.security_findings.extend(line[2:] for line in result.stdout.splitlines() if line.startswith("- "))
    elif result.name == "api-contract-check":
        report.api_findings.extend(line for line in result.stdout.splitlines() if line.strip())
    elif result.name == "scenario-patch-check":
        report.api_findings.extend(line.removeprefix("api finding: ").strip()
                                   for line in result.stdout.splitlines() if line.startswith("api finding:"))
