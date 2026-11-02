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

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


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

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["tools"] = [tool.to_dict() for tool in self.tools]
        return value
