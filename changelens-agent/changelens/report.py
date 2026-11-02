"""JSON and Markdown evidence report writers."""

from __future__ import annotations

import json
from pathlib import Path

from .models import EvidenceReport
from .scenarios import Scenario


def write_json(report: EvidenceReport, destination: Path) -> None:
    destination.write_text(json.dumps(report.to_dict(), indent=2) + "\n")


def write_markdown(report: EvidenceReport, scenario: Scenario, destination: Path) -> None:
    lines = [
        "# ChangeLens evidence report", "", f"- Scenario: `{report.scenario}`",
        f"- Run ID: `{report.run_id}`", f"- Commit: `{report.commit_sha}`", "",
        "## Changed files", "", *[f"- `{path}`" for path in report.changed_files], "",
        "## Commands and tool status", "",
        "| Tool | Status | Exit code | Duration (ms) | Command |", "|---|---|---:|---:|---|",
    ]
    for tool in report.tools:
        lines.append(f"| {tool.name} | {tool.status.value} | {tool.exit_code if tool.exit_code is not None else ''} | {tool.duration_ms} | `{tool.command}` |")
    lines += ["", "## Test results", "", "```json", json.dumps(report.tests, indent=2), "```", "",
              "## Security results", "", *([f"- {finding}" for finding in report.security_findings] or ["- No findings recorded."]), "",
              "## API results", "", *([f"- {finding}" for finding in report.api_findings] or ["- No findings recorded."]), "",
              "## Performance results", "", "```json", json.dumps(report.performance, indent=2), "```", "",
              "## Deterministic policy", "", "```json", json.dumps(report.policy, indent=2), "```", "",
              "## AI evidence analyst", "", "```json", json.dumps(report.ai_analysis, indent=2), "```", "",
              "## Errors and limitations", "", *([f"- {error}" for error in report.errors] or ["- None recorded."]), "",
              "## Scenario evidence", "", f"Expected outcome: {scenario.expected_outcome}", "",
              "Expected evidence:", "", *[f"- {item}" for item in scenario.expected_evidence], "",
              "Artifacts: `evidence.json`, `report.md` in this run directory.", ""]
    destination.write_text("\n".join(lines))
