"""Actual base/head pull-request analysis in an isolated candidate directory."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .analyst import analyze
from .diff_analysis import (DiffAnalysisError, ChangedFile, cleanup_workspace,
                            create_candidate_workspace, extract_diff)
from .models import Decision, EvidenceReport, ToolResult, ToolStatus
from .policy import evaluate
from .report import write_json, write_markdown
from .scenarios import Scenario
from .tools import enrich_report, run_maven, run_python_tests, run_security


def analyze_pull_request(root: Path, base_ref: str, head_ref: str, timeout: int = 120) -> tuple[EvidenceReport, Path, Path]:
    """Analyze committed head code without modifying the caller's worktree."""
    diff = extract_diff(root, base_ref, head_ref)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    artifact_dir = root / "artifacts" / run_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report = EvidenceReport(
        schema_version="1.0", run_id=run_id, scenario="pull-request",
        commit_sha=diff.head_sha, changed_files=[item.path for item in diff.files if item.status != "D"],
        analysis_mode="pull_request", base_commit_sha=diff.base_sha, head_commit_sha=diff.head_sha,
        merge_base_ref=diff.merge_base, diff_summary=diff.to_dict(),
        candidate_workspace={"type": "temporary git archive", "path_exposed": False},
    )
    temporary = None
    try:
        candidate, temporary = create_candidate_workspace(root, diff.head_sha)
        report.candidate_workspace.update({"created": True, "isolated": True, "source": "committed head archive"})
        environment = _candidate_environment(candidate)

        add(report, ToolResult("git-diff-analysis", f"git diff {diff.base_sha} {diff.head_sha}",
                               ToolStatus.PASSED, 0, 0,
                               f"{len(diff.files)} changed file(s), {diff.insertions} insertion(s), {diff.deletions} deletion(s)", ""))
        add(report, run_maven(candidate, timeout, environment))
        for module in ("tests.test_phase2_scenarios", "tests.test_phase3_control_plane", "tests.test_phase4_policy_analyst"):
            add(report, run_python_tests(candidate, module, timeout, environment))

        security_file = next((item.path for item in diff.files if item.path.endswith("kubernetes.yaml")
                              and (candidate / item.path).is_file()), None)
        if security_file:
            scenario = Scenario("pull-request-security", "infrastructure-security", [security_file], "", "", [], "", candidate / Path(security_file).parent)
            add(report, run_security(candidate, scenario, timeout, environment))
        else:
            add_skipped(report, "security-fixture-validator", "no changed Kubernetes security fixture")

        _detect_static_api_findings(report, candidate, diff.files)
        for name, reason in (
            ("application-health", "candidate application is not started by isolated PR analysis"),
            ("api-contract-check", "requires a running candidate application"),
            ("baseline-load-test", "requires a running candidate application and is not run in static PR mode"),
        ):
            add_skipped(report, name, reason)
            report.skipped_checks.append(name)

        policy = evaluate(report)
        report.policy = policy.to_dict()
        report.ai_analysis = analyze(report, policy,
                                     f"Actual pull-request diff from {diff.base_sha} to {diff.head_sha}.").to_dict()
    except Exception as exc:
        report.errors.append(f"candidate analysis: {type(exc).__name__}: {exc}")
        report.candidate_workspace["created"] = False
        policy = evaluate(report)
        report.policy = policy.to_dict()
        report.ai_analysis = analyze(report, policy, "Actual pull-request diff analysis failed before all checks ran.").to_dict()
    finally:
        if temporary is not None:
            report.cleanup_status = "cleaned" if cleanup_workspace(temporary) else "cleanup_failed"
        else:
            report.cleanup_status = "not_created"
        write_json(report, artifact_dir / "evidence.json")
        write_markdown(report, None, artifact_dir / "report.md")
    return report, artifact_dir / "evidence.json", artifact_dir / "report.md"


def add(report: EvidenceReport, result: ToolResult) -> None:
    report.tools.append(result)
    enrich_report(report, result)


def add_skipped(report: EvidenceReport, name: str, reason: str) -> None:
    add(report, ToolResult(name, "not run", ToolStatus.SKIPPED, None, 0, "", reason))


def _candidate_environment(candidate: Path) -> dict[str, str]:
    """Pass only execution basics, never arbitrary credentials, into candidate tools."""
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "JAVA_HOME": os.environ.get("JAVA_HOME", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONPATH": str(candidate / "changelens-agent"),
    }
    return {key: value for key, value in environment.items() if value}


def _detect_static_api_findings(report: EvidenceReport, candidate: Path, files: list[ChangedFile]) -> None:
    for changed in files:
        if not changed.path.endswith("OrderDtos.java"):
            continue
        source = candidate / changed.path
        if not source.exists() or "public OrderStatus status;" not in source.read_text(errors="replace"):
            report.api_findings.append("required response field status is missing from the candidate OrderDtos.java")
