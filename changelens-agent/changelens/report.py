"""JSON and Markdown evidence report writers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceReport
from .policy import rule_guidance, rule_label
from .scenarios import Scenario


def write_json(report: EvidenceReport, destination: Path) -> None:
    destination.write_text(json.dumps(report.to_dict(), indent=2) + "\n")


def write_markdown(report: EvidenceReport, scenario: Scenario | None, destination: Path) -> None:
    policy = report.policy or {}
    reasons = policy.get("reasons", [])
    candidate_failures = [tool for tool in report.tools
                          if tool.status.value in {"failed", "timed_out"}
                          and tool.name not in {"application-health", "baseline-load-test"}]
    infrastructure_failures = [tool for tool in report.tools
                               if tool.status.value in {"unavailable", "timed_out"}
                               and tool.name in {"application-health", "api-contract-check", "baseline-load-test"}]
    failure_details = report.tests.get("failure_details", [])
    lines = [
        "# ChangeLens evidence report", "", f"- Scenario: `{report.scenario}`",
        f"- Analysis mode: `{report.analysis_mode}`", f"- Run ID: `{report.run_id}`",
        f"- Commit: `{report.commit_sha}`", f"- Base commit: `{report.base_commit_sha or 'not applicable'}`",
        f"- Head commit: `{report.head_commit_sha or report.commit_sha}`",
        f"- Merge base: `{report.merge_base_ref or 'not applicable'}`", "",
        "## Changed files", "", *[f"- `{path}`" for path in report.changed_files], "",
        "## Diff summary", "", "```json", json.dumps(report.diff_summary, indent=2), "```", "",
        "## Candidate workspace", "", "```json", json.dumps(report.candidate_workspace, indent=2), "```", "",
        "## Commands and tool status", "",
        "| Tool | Status | Exit code | Duration (ms) | Command |", "|---|---|---:|---:|---|",
    ]
    for tool in report.tools:
        lines.append(f"| {tool.name} | {tool.status.value} | {tool.exit_code if tool.exit_code is not None else ''} | {tool.duration_ms} | `{tool.command}` |")
    lines += ["", "## Decision at a glance", "",
              f"- Deterministic policy: **{policy.get('status', 'NOT_EVALUATED')}**",
              f"- Policy version: `{policy.get('policy_version', 'unknown')}`", "",
              "## Policy rules and remediation", ""]
    if reasons:
        lines += ["| Rule | Why it triggered | Observed | Threshold | Remediation |", "|---|---|---|---|---|"]
        for reason in reasons:
            lines.append(f"| {rule_label(reason.get('rule', 'unknown'))} (`{reason.get('rule', 'unknown')}`) | "
                         f"{reason.get('message', '')} | {_display(reason.get('observed'))} | "
                         f"{_display(reason.get('threshold'))} | {rule_guidance(reason.get('rule', ''))} |")
    else:
        lines.append("- No policy rules triggered; all required evidence supports approval.")
    lines += ["", "## Candidate check failures", ""]
    if candidate_failures or failure_details or report.security_findings or report.api_findings:
        for tool in candidate_failures:
            lines.append(f"- **{tool.name}**: `{tool.status.value}` (exit code `{tool.exit_code if tool.exit_code is not None else 'n/a'}`)")
        for detail in failure_details:
            lines.append(f"- Maven test failure: {detail}")
        for finding in report.security_findings:
            lines.append(f"- Security finding: {finding}")
        for finding in report.api_findings:
            lines.append(f"- API finding: {finding}")
    else:
        lines.append("- None recorded.")
    lines += ["", "## Infrastructure and tool availability", ""]
    if infrastructure_failures:
        for tool in infrastructure_failures:
            detail = tool.stderr.strip() or tool.stdout.strip() or tool.status.value
            lines.append(f"- **{tool.name}**: `{tool.status.value}` — {detail}")
    else:
        lines.append("- No infrastructure/tool availability failures recorded.")
    lines += ["", "## Test results", "", "```json", json.dumps(report.tests, indent=2), "```", "",
              "## Security results", "", *([f"- {finding}" for finding in report.security_findings] or ["- No findings recorded."]), "",
              "## API results", "", *([f"- {finding}" for finding in report.api_findings] or ["- No findings recorded."]), "",
              "## Performance results", "", "```json", json.dumps(report.performance, indent=2), "```", "",
              "## Deterministic policy (machine-readable)", "", "```json", json.dumps(report.policy, indent=2), "```", "",
              "## AI evidence analyst", "", "```json", json.dumps(report.ai_analysis, indent=2), "```", "",
              "## Skipped checks", "", *([f"- {item}" for item in report.skipped_checks] or ["- None recorded."]), "",
              f"Cleanup status: `{report.cleanup_status}`", "",
              "## Errors and limitations", "", *([f"- {error}" for error in report.errors] or ["- None recorded."]), "",
              "## Scenario evidence", ""]
    if scenario:
        lines += [f"Expected outcome: {scenario.expected_outcome}", "", "Expected evidence:", "",
                  *[f"- {item}" for item in scenario.expected_evidence], ""]
    else:
        lines += ["This report was generated from the actual base/head pull-request diff.", ""]
    lines += ["Artifacts: `evidence.json`, `report.md` in this run directory.", ""]
    destination.write_text("\n".join(lines))


def _display(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(", ", ": "))
    return str(value)
