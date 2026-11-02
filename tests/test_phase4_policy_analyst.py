import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "changelens-agent"))

from changelens.analyst import (MockProvider, analyze, build_model_input, unsupported_references,
                                validate_output)
from changelens.models import AIAnalysis, Decision, EvidenceReport, PolicyResult, ToolResult, ToolStatus
from changelens.policy import PolicyConfig, evaluate


def tool(name, status=ToolStatus.PASSED):
    return ToolResult(name, name, status, 0 if status == ToolStatus.PASSED else 1, 1)


def evidence(performance=None, tools=None, security=None, api=None):
    return EvidenceReport(
        "1.0", "run", "test", "sha", ["demo-app/order-api/file"],
        tools or [tool("maven-tests"), tool("api-contract-check"), tool("application-health"), tool("baseline-load-test")],
        {"status": "passed"}, security_findings=security or [], api_findings=api or [],
        performance=performance or {},
    )


class Phase4PolicyTests(unittest.TestCase):
    def test_safe_evidence_is_approved(self):
        result = evaluate(evidence({"baseline_p95_latency_ms": 100, "candidate_p95_latency_ms": 105,
                                    "error_rate": 0.0}))
        self.assertEqual(result.status, Decision.APPROVE)
        self.assertEqual(result.triggered_rules, [])

    def test_critical_security_finding_blocks(self):
        result = evaluate(evidence({"error_rate": 0}, security=["CRITICAL: privileged container"]))
        self.assertEqual(result.status, Decision.BLOCK)
        self.assertIn("critical_security_finding", result.triggered_rules)

    def test_security_validator_findings_block(self):
        result = evaluate(evidence({"error_rate": 0}, tools=[tool("security-fixture-validator", ToolStatus.FAILED)],
                                   security=["privileged containers have excessive kernel access"]))
        self.assertEqual(result.status, Decision.BLOCK)
        self.assertIn("security_validation_failure", result.triggered_rules)

    def test_failed_contract_check_blocks(self):
        result = evaluate(evidence({"error_rate": 0}, tools=[tool("maven-tests"), tool("api-contract-check", ToolStatus.FAILED)]))
        self.assertEqual(result.status, Decision.BLOCK)

    def test_excessive_latency_blocks(self):
        result = evaluate(evidence({"baseline_p95_latency_ms": 100, "candidate_p95_latency_ms": 160, "error_rate": 0}))
        self.assertEqual(result.status, Decision.BLOCK)
        self.assertEqual(result.reasons[0].rule, "p95_latency_limit")

    def test_moderate_latency_increase_requires_review(self):
        result = evaluate(evidence({"baseline_p95_latency_ms": 100, "candidate_p95_latency_ms": 125, "error_rate": 0}))
        self.assertEqual(result.status, Decision.REVIEW)

    def test_missing_candidate_metrics_requires_review(self):
        result = evaluate(evidence({"error_rate": 0}))
        self.assertEqual(result.status, Decision.REVIEW)
        self.assertIn("performance_unavailable", result.triggered_rules)

    def test_thresholds_are_configurable(self):
        result = evaluate(evidence({"baseline_p95_latency_ms": 100, "candidate_p95_latency_ms": 120, "error_rate": 0.015}),
                           PolicyConfig(error_rate_block=0.01, latency_block_multiplier=1.3))
        self.assertEqual(result.status, Decision.BLOCK)
        self.assertEqual(result.thresholds["error_rate_block"], 0.01)


class Phase4AnalystTests(unittest.TestCase):
    def test_mock_provider_returns_valid_structured_output(self):
        report = evidence({"baseline_p95_latency_ms": 100, "candidate_p95_latency_ms": 100, "error_rate": 0})
        policy = evaluate(report)
        result = analyze(report, policy)
        self.assertEqual(result.provider, "mock")
        self.assertEqual(result.decision, Decision.APPROVE)
        self.assertTrue(result.evidence_references)

    def test_malformed_output_is_rejected(self):
        report = evidence({"baseline_p95_latency_ms": 100, "candidate_p95_latency_ms": 100, "error_rate": 0})
        policy = evaluate(report)
        with self.assertRaises(ValueError):
            validate_output({"summary": "incomplete"}, report, policy, "test", "test")

    def test_unavailable_provider_uses_deterministic_fallback(self):
        report = evidence({"error_rate": 0})
        policy = evaluate(report)
        class BrokenProvider:
            name = "broken"
            model = "unavailable"
            def analyze(self, payload):
                raise OSError("provider unavailable")
        with patch("changelens.analyst.provider_from_environment", return_value=BrokenProvider()):
            result = analyze(report, policy)
        self.assertEqual(result.decision, policy.status)
        self.assertTrue(result.limitations)

    def test_ai_cannot_override_deterministic_block(self):
        report = evidence({"error_rate": 0}, security=["CRITICAL: unsafe setting"])
        policy = evaluate(report)
        raw = MockProvider().analyze({"policy": policy.to_dict(), "changed_files": report.changed_files})
        raw["decision"] = "APPROVE"
        constrained = validate_output(raw, report, policy, "test", "test")
        self.assertEqual(constrained.decision, Decision.BLOCK)
        self.assertTrue(any("constrained" in item for item in constrained.limitations))

    def test_unsupported_references_are_detected(self):
        report = evidence({"error_rate": 0})
        policy = evaluate(report)
        self.assertEqual(unsupported_references(["made_up.metric"], report, policy), ["made_up.metric"])

    def test_secrets_are_not_in_model_input(self):
        report = evidence({"error_rate": 0}, tools=[ToolResult("tool", "tool", ToolStatus.PASSED, 0, 1,
                                                                  "token=super-secret password=hunter2", "")])
        payload = build_model_input(report, evaluate(report), "summary")
        serialized = str(payload)
        self.assertNotIn("super-secret", serialized)
        self.assertNotIn("hunter2", serialized)
        self.assertIn("REDACTED", serialized)

    def test_rollback_plan_uses_only_available_evidence(self):
        report = evidence({"error_rate": 0}, security=["CRITICAL: unsafe setting"])
        result = analyze(report, evaluate(report))
        self.assertTrue(result.rollback_plan)
        self.assertTrue(set(result.evidence_references).issubset(
            {"security_findings", "performance", "changed_files", "policy"} |
            {f"tools.{t.name}" for t in report.tools}))


if __name__ == "__main__":
    unittest.main()
