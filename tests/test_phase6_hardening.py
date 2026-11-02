import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "changelens-agent"))

from changelens.analyst import validate_output
from changelens.__main__ import load_performance_metrics
from changelens.models import Decision, EvidenceReport, ToolResult, ToolStatus, validate_evidence_payload
from changelens.policy import evaluate
from changelens.report import write_json, write_markdown
from changelens.runner import MAX_CAPTURE_CHARS, run_command
from changelens.scenarios import load_manifest
from changelens.tools import check_health


class Phase6HardeningTests(unittest.TestCase):
    def test_noisy_command_output_is_bounded(self):
        result = run_command("noisy", [sys.executable, "-c", "print('x' * 100000)"], ROOT)
        self.assertEqual(result.status, ToolStatus.PASSED)
        self.assertLessEqual(len(result.stdout), MAX_CAPTURE_CHARS)
        self.assertTrue(result.stdout_truncated)

    def test_nonzero_exit_code_and_stderr_are_preserved(self):
        result = run_command("failure", [sys.executable, "-c", "import sys; print('failure', file=sys.stderr); sys.exit(7)"], ROOT)
        self.assertEqual(result.status, ToolStatus.FAILED)
        self.assertEqual(result.exit_code, 7)
        self.assertIn("failure", result.stderr)

    def test_missing_evidence_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_evidence_payload({"schema_version": "1.0"})

    def test_malformed_json_output_is_reported_as_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "load.json"
            path.write_text("{not-json")
            self.assertIsNone(load_performance_metrics(path))

    def test_malformed_analyst_output_is_rejected(self):
        report = EvidenceReport("1.0", "run", "safe-change", "sha", ["file"])
        policy = evaluate(report)
        malformed = {
            "summary": "ok", "decision": "APPROVE", "confidence": 0.5,
            "affected_components": "not-a-list", "evidence_references": [],
            "prioritized_findings": [], "recommended_action": "none",
            "rollback_plan": [], "limitations": [],
        }
        with self.assertRaises(ValueError):
            validate_output(malformed, report, policy, "test", "test")

    def test_missing_application_health_is_unavailable(self):
        result = check_health("http://127.0.0.1:1", 1)
        self.assertEqual(result.status, ToolStatus.UNAVAILABLE)
        self.assertIsNone(result.exit_code)

    def test_failed_tool_still_produces_a_report(self):
        scenario = load_manifest(ROOT / "fixtures/scenarios/manifest.json")["safe-change"]
        report = EvidenceReport("1.0", "failure-run", scenario.name, "sha", scenario.changed_files,
                                tools=[ToolResult("maven-tests", "mvn test", ToolStatus.FAILED, 1, 2, "", "failed")],
                                errors=["maven-tests: failed"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_json(report, path / "evidence.json")
            write_markdown(report, scenario, path / "report.md")
            self.assertEqual(json.loads((path / "evidence.json").read_text())["tools"][0]["status"], "failed")
            self.assertIn("failed", (path / "report.md").read_text())

    def test_block_policy_and_report_artifact_remain_distinct(self):
        report = EvidenceReport("1.0", "block-run", "security", "sha", ["fixture"],
                                security_findings=["CRITICAL: unsafe setting"])
        policy = evaluate(report)
        self.assertEqual(policy.status, Decision.BLOCK)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            write_json(report, path / "evidence.json")
            self.assertTrue((path / "evidence.json").exists())
            self.assertEqual(json.loads((path / "evidence.json").read_text())["security_findings"],
                             ["CRITICAL: unsafe setting"])


if __name__ == "__main__":
    unittest.main()
