"""Deterministic release policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List

from .models import Decision, EvidenceReport, PolicyReason, PolicyResult, ToolStatus


RULE_LABELS = {
    "critical_security_finding": "Critical security finding",
    "security_validation_failure": "Security validation failure",
    "api_contract_failure": "Required API contract failed",
    "api_contract_findings": "API compatibility finding",
    "required_tests_failed": "Required candidate tests failed",
    "error_rate_limit": "Candidate error rate exceeded limit",
    "p95_latency_limit": "Candidate p95 latency exceeded limit",
    "p95_latency_review": "Candidate p95 latency requires review",
    "performance_unavailable": "Candidate performance evidence unavailable",
    "medium_high_finding": "Medium/high finding requires review",
    "required_evidence_unavailable": "Required evidence unavailable",
}

RULE_GUIDANCE = {
    "critical_security_finding": "Remediate the critical security finding and rerun the security checks.",
    "security_validation_failure": "Remove the unsafe infrastructure setting, then rerun the security validator.",
    "api_contract_failure": "Restore the required API contract or update it through a deliberate compatible change.",
    "api_contract_findings": "Resolve the API compatibility finding and rerun the contract check.",
    "required_tests_failed": "Fix the failing candidate test before release; do not treat a test failure as a tooling pass.",
    "error_rate_limit": "Investigate the candidate errors, correct the regression, and rerun the workload.",
    "p95_latency_limit": "Restore or optimize the regressed execution path and rerun the comparison workload.",
    "p95_latency_review": "Review the latency increase with the owning team and collect comparable workload evidence.",
    "performance_unavailable": "Start the candidate runtime and collect baseline/candidate performance evidence.",
    "medium_high_finding": "Resolve or explicitly accept the finding through human review before release.",
    "required_evidence_unavailable": "Restore the unavailable tool or service and rerun the affected check.",
}


def rule_label(rule: str) -> str:
    return RULE_LABELS.get(rule, rule.replace("_", " ").capitalize())


def rule_guidance(rule: str) -> str:
    return RULE_GUIDANCE.get(rule, "Investigate the rule evidence and rerun ChangeLens before release.")


@dataclass(frozen=True)
class PolicyConfig:
    version: str = "1.0"
    error_rate_block: float = 0.02
    latency_block_multiplier: float = 1.5
    latency_review_min_increase: float = 0.10
    latency_review_max_increase: float = 0.50
    critical_security_markers: tuple[str, ...] = ("critical", "severity: critical", "severity=critical")
    review_finding_markers: tuple[str, ...] = ("high", "medium")

    def thresholds(self) -> Dict[str, Any]:
        return {
            "error_rate_block": self.error_rate_block,
            "latency_block_multiplier": self.latency_block_multiplier,
            "latency_review_min_increase": self.latency_review_min_increase,
            "latency_review_max_increase": self.latency_review_max_increase,
        }


def evaluate(report: EvidenceReport, config: PolicyConfig | None = None) -> PolicyResult:
    config = config or PolicyConfig()
    reasons: List[PolicyReason] = []
    measured: Dict[str, Any] = {}
    references: List[str] = []

    critical = [finding for finding in report.security_findings if _contains_marker(finding, config.critical_security_markers)]
    if critical:
        reasons.append(PolicyReason("critical_security_finding", "A critical security finding was reported.", critical,
                                    "no critical findings", "findings", ["security_findings"]))
        references.append("security_findings")

    security_tool = _tool(report, "security-fixture-validator")
    if security_tool and security_tool.status == ToolStatus.FAILED and report.security_findings:
        reasons.append(PolicyReason("security_validation_failure", "The security validator reported unsafe configuration.",
                                    report.security_findings, "no security findings", "findings",
                                    ["security_findings", "tools.security-fixture-validator"]))
        references.extend(["security_findings", "tools.security-fixture-validator"])

    api_tool = _tool(report, "api-contract-check")
    if api_tool and api_tool.status == ToolStatus.FAILED:
        reasons.append(PolicyReason("api_contract_failure", "The required API contract check failed.", api_tool.exit_code,
                                    0, "exit_code", ["tools.api-contract-check"]))
        references.append("tools.api-contract-check")
    elif report.api_findings:
        reasons.append(PolicyReason("api_contract_findings", "The API contract check reported findings.", report.api_findings,
                                    "no findings", "findings", ["api_findings"]))
        references.append("api_findings")

    failed_tools = [tool.name for tool in report.tools if tool.status == ToolStatus.FAILED and tool.name == "maven-tests"]
    if failed_tools:
        reasons.append(PolicyReason("required_tests_failed", "The required Maven test suite failed.", failed_tools,
                                    "no failed required tests", "tools", ["tools.maven-tests"]))
        references.append("tools.maven-tests")

    performance = report.performance
    error_rate = _number(performance.get("error_rate"))
    if error_rate is not None:
        measured["error_rate"] = error_rate
        if error_rate > config.error_rate_block:
            reasons.append(PolicyReason("error_rate_limit", "Observed error rate exceeded the configured threshold.",
                                        error_rate, config.error_rate_block, "ratio", ["performance.error_rate"]))
            references.append("performance.error_rate")

    baseline_p95 = _number(performance.get("baseline_p95_latency_ms", performance.get("baseline_p95_ms")))
    candidate_p95 = _number(performance.get("candidate_p95_latency_ms", performance.get("p95_latency_ms")))
    if baseline_p95 is not None and candidate_p95 is not None and baseline_p95 > 0:
        increase = (candidate_p95 - baseline_p95) / baseline_p95
        block_threshold = baseline_p95 * config.latency_block_multiplier
        measured.update({"baseline_p95_latency_ms": baseline_p95, "candidate_p95_latency_ms": candidate_p95,
                         "latency_increase_ratio": increase})
        if candidate_p95 > block_threshold:
            reasons.append(PolicyReason("p95_latency_limit", "Candidate p95 latency exceeded the configured threshold.",
                                        candidate_p95, block_threshold, "ms", ["performance.candidate_p95_latency_ms",
                                                                                "performance.baseline_p95_latency_ms"]))
            references.extend(["performance.candidate_p95_latency_ms", "performance.baseline_p95_latency_ms"])
        elif config.latency_review_min_increase <= increase <= config.latency_review_max_increase:
            reasons.append(PolicyReason("p95_latency_review", "Candidate p95 latency increased within the review range.",
                                        increase, config.latency_review_min_increase, "ratio",
                                        ["performance.latency_increase_ratio"]))
            references.append("performance.latency_increase_ratio")
    elif (baseline_p95 is None or candidate_p95 is None) and report.analysis_mode != "pull_request":
        reasons.append(PolicyReason("performance_unavailable", "Candidate performance metrics were not available.",
                                    "unavailable", "required for approval", "metrics", ["performance"]))
        references.append("performance")

    finding_text = [*report.security_findings, *report.api_findings]
    review_findings = [finding for finding in finding_text if _contains_marker(finding, config.review_finding_markers)]
    if review_findings and not critical:
        reasons.append(PolicyReason("medium_high_finding", "A medium or high finding requires review.", review_findings,
                                    "no medium/high findings", "findings", ["security_findings", "api_findings"]))
        references.extend(["security_findings", "api_findings"])

    unavailable = [tool.name for tool in report.tools
                   if tool.status in (ToolStatus.UNAVAILABLE, ToolStatus.TIMED_OUT)
                   and tool.name not in report.skipped_checks]
    if unavailable:
        reasons.append(PolicyReason("required_evidence_unavailable", "One or more checks did not produce evidence.",
                                    unavailable, "no unavailable required checks", "tools", [f"tools.{name}" for name in unavailable]))
        references.extend(f"tools.{name}" for name in unavailable)

    status = Decision.APPROVE
    if any(reason.rule in {"critical_security_finding", "security_validation_failure", "api_contract_failure", "api_contract_findings",
                           "required_tests_failed", "error_rate_limit", "p95_latency_limit"} for reason in reasons):
        status = Decision.BLOCK
    elif reasons:
        status = Decision.REVIEW
    triggered = _unique(reason.rule for reason in reasons)
    return PolicyResult(status, config.version, triggered, measured, config.thresholds(), reasons,
                        _unique(references))


def _tool(report: EvidenceReport, name: str):
    return next((tool for tool in report.tools if tool.name == name), None)


def _number(value: Any):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _contains_marker(value: str, markers: Iterable[str]) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in markers)


def _unique(values: Iterable[str]) -> List[str]:
    return list(dict.fromkeys(values))
