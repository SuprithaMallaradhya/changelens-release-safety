"""CLI entry point for ``python -m changelens``."""

from __future__ import annotations

import argparse
import json
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import Decision, EvidenceReport, ToolStatus
from .analyst import analyze
from .diff_analysis import DiffAnalysisError
from .policy import evaluate
from .pr_analysis import analyze_pull_request
from .report import write_json, write_markdown
from .scenarios import load_manifest, scenario_changed_files
from .tools import (analyze_scenario, check_health, enrich_report, run_api_contract,
                    run_load_test, run_maven, run_security)


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def commit_sha(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True,
                              check=False).stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic ChangeLens evidence checks.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run checks for a manifest scenario")
    run.add_argument("--scenario", required=True)
    run.add_argument("--base-url", default="http://localhost:8080")
    run.add_argument("--timeout", type=int, default=120)
    for name, help_text in (("analyze-pr", "analyze committed pull-request base/head refs"),
                            ("analyze-diff", "analyze committed local base/head refs")):
        analysis = subparsers.add_parser(name, help=help_text)
        analysis.add_argument("--base-ref", required=True)
        analysis.add_argument("--head-ref", required=True)
        analysis.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    root = repository_root()
    if args.command in {"analyze-pr", "analyze-diff"}:
        try:
            report, evidence, markdown = analyze_pull_request(root, args.base_ref, args.head_ref, args.timeout)
        except DiffAnalysisError as exc:
            parser.error(str(exc))
        print(json.dumps({"run_id": report.run_id, "evidence": str(evidence), "report": str(markdown),
                          "analysis_mode": report.analysis_mode, "policy": report.policy.get("status")}, indent=2))
        # REVIEW is a successful workflow outcome with an explicit human-review
        # warning; only a deterministic BLOCK fails the required check.
        return policy_exit_code(report.policy.get("status"))

    scenarios = load_manifest(root / "fixtures" / "scenarios" / "manifest.json")
    if args.scenario not in scenarios:
        parser.error(f"unknown scenario {args.scenario!r}; choose from {', '.join(sorted(scenarios))}")
    scenario = scenarios[args.scenario]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    artifact_dir = root / "artifacts" / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report = EvidenceReport("1.0", run_id, scenario.name, commit_sha(root), scenario_changed_files(scenario))

    def add(result):
        report.tools.append(result)
        enrich_report(report, result)

    add(analyze_scenario(root, scenario, args.timeout))
    add(run_maven(root, args.timeout))
    add(run_security(root, scenario, args.timeout))
    health = check_health(args.base_url, min(args.timeout, 10))
    add(health)
    add(run_api_contract(root, args.base_url, args.timeout) if health.status == ToolStatus.PASSED else
        _unavailable("api-contract-check", "application health check did not pass"))
    load_output = artifact_dir / "baseline.json"
    add(run_load_test(root, args.base_url, load_output, max(args.timeout, 45)) if health.status == ToolStatus.PASSED else
        _unavailable("baseline-load-test", "application health check did not pass"))
    if load_output.exists():
        performance = load_performance_metrics(load_output)
        if performance is None:
            report.errors.append("baseline-load-test output was missing or malformed JSON")
        else:
            report.performance = performance
    policy = evaluate(report)
    report.policy = policy.to_dict()
    report.ai_analysis = analyze(report, policy, scenario.expected_outcome).to_dict()
    write_json(report, artifact_dir / "evidence.json")
    write_markdown(report, scenario, artifact_dir / "report.md")
    print(json.dumps({"run_id": run_id, "evidence": str(artifact_dir / "evidence.json"),
                      "report": str(artifact_dir / "report.md")}, indent=2))
    # REVIEW is intentionally non-failing: the report carries the missing or
    # ambiguous evidence and the workflow emits the human-review warning.
    return policy_exit_code(policy.status.value)


def policy_exit_code(status: str) -> int:
    """Map policy outcomes to CI semantics: only BLOCK fails the check."""
    return 1 if status == Decision.BLOCK.value else 0


def _unavailable(name: str, reason: str):
    from .models import ToolResult
    return ToolResult(name, "not run", ToolStatus.UNAVAILABLE, None, 0, "", reason)


def load_performance_metrics(path: Path):
    """Read load-test JSON without allowing malformed output to crash reporting."""
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
