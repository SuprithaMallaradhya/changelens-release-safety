import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "changelens-agent"))

from changelens.__main__ import policy_exit_code
from changelens.models import EvidenceReport, ToolResult, ToolStatus
from changelens.policy import evaluate
from changelens.report import write_markdown
from changelens.tools import enrich_report

WORKFLOW = ROOT / ".github/workflows/changelens.yml"


class Phase8ReleaseHardeningTests(unittest.TestCase):
    def test_only_block_fails_ci(self):
        self.assertEqual(policy_exit_code("APPROVE"), 0)
        self.assertEqual(policy_exit_code("REVIEW"), 0)
        self.assertEqual(policy_exit_code("BLOCK"), 1)

    def test_workflow_warns_on_review_and_enforces_block_after_artifacts(self):
        text = WORKFLOW.read_text()
        self.assertIn("::warning::ChangeLens policy requires human review", text)
        self.assertLess(text.index("Upload ChangeLens reports"), text.index("Enforce deterministic policy"))
        self.assertIn("BLOCK", text)

    def test_report_has_readable_rules_exact_findings_and_remediation(self):
        report = EvidenceReport(
            "1.0", "run", "pull-request", "sha", ["OrderDtos.java"],
            tools=[ToolResult("api-contract-check", "contract", ToolStatus.FAILED, 1, 1)],
            api_findings=["required response field status is missing from the candidate OrderDtos.java"],
        )
        report.policy = evaluate(report).to_dict()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.md"
            write_markdown(report, None, destination)
            text = destination.read_text()
        self.assertIn("Required API contract failed", text)
        self.assertIn("required response field status is missing", text)
        self.assertIn("Restore the required API contract", text)
        self.assertIn("Candidate check failures", text)

    def test_report_separates_infrastructure_unavailability(self):
        report = EvidenceReport(
            "1.0", "run", "safe-change", "sha", [],
            tools=[ToolResult("application-health", "GET", ToolStatus.UNAVAILABLE, None, 1, "", "connection refused")],
        )
        enrich_report(report, report.tools[0])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.md"
            write_markdown(report, None, destination)
            text = destination.read_text()
        self.assertIn("Infrastructure and tool availability", text)
        self.assertIn("connection refused", text)
        self.assertIn("Candidate check failures", text)

    def test_maven_failure_keeps_exact_failure_detail(self):
        report = EvidenceReport("1.0", "run", "api", "sha", [])
        result = ToolResult(
            "maven-tests", "mvn test", ToolStatus.FAILED, 1, 1,
            "[ERROR] createsOrderWithValidation Time elapsed: 0.1 s <<< FAILURE!\n"
            "[ERROR] No value at JSON path $.status\n", "",
        )
        enrich_report(report, result)
        self.assertIn("failure_details", report.tests)
        self.assertTrue(any("createsOrderWithValidation" in item for item in report.tests["failure_details"]))


if __name__ == "__main__":
    unittest.main()
