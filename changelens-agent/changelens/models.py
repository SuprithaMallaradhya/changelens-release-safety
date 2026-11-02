"""Versioned evidence models for ChangeLens runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ToolStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    UNAVAILABLE = "unavailable"


class Decision(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass
class ToolResult:
    name: str
    command: str
    status: ToolStatus
    exit_code: Optional[int]
    duration_ms: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    stdout_truncated: bool = False
    stderr_truncated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


EVIDENCE_FIELDS = (
    "schema_version", "run_id", "scenario", "commit_sha", "changed_files", "tools",
    "tests", "security_findings", "api_findings", "performance", "errors",
)


def validate_evidence_payload(payload: Any) -> None:
    """Reject incomplete untyped evidence before it reaches an analyst."""
    if not isinstance(payload, dict):
        raise ValueError("evidence payload must be an object")
    missing = [field for field in EVIDENCE_FIELDS if field not in payload]
    if missing:
        raise ValueError("evidence payload is missing: " + ", ".join(missing))


@dataclass
class EvidenceReport:
    schema_version: str
    run_id: str
    scenario: str
    commit_sha: str
    changed_files: List[str]
    tools: List[ToolResult] = field(default_factory=list)
    tests: Dict[str, Any] = field(default_factory=dict)
    security_findings: List[str] = field(default_factory=list)
    api_findings: List[str] = field(default_factory=list)
    performance: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    policy: Dict[str, Any] = field(default_factory=dict)
    ai_analysis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["tools"] = [tool.to_dict() for tool in self.tools]
        return value


@dataclass
class PolicyReason:
    rule: str
    message: str
    observed: Any
    threshold: Any = None
    unit: str = ""
    evidence_references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyResult:
    status: Decision
    policy_version: str
    triggered_rules: List[str] = field(default_factory=list)
    measured_values: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, Any] = field(default_factory=dict)
    reasons: List[PolicyReason] = field(default_factory=list)
    evidence_references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "policy_version": self.policy_version,
            "triggered_rules": self.triggered_rules,
            "measured_values": self.measured_values,
            "thresholds": self.thresholds,
            "reasons": [reason.to_dict() for reason in self.reasons],
            "evidence_references": self.evidence_references,
        }


@dataclass
class AIAnalysis:
    summary: str
    decision: Decision
    confidence: float
    affected_components: List[str]
    evidence_references: List[str]
    prioritized_findings: List[str]
    recommended_action: str
    rollback_plan: List[str]
    limitations: List[str]
    provider: str
    model: str
    prompt_version: str
    generated_at: str

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["decision"] = self.decision.value
        return value
