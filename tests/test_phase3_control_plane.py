import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "changelens-agent"))

from changelens.models import EvidenceReport, ToolStatus
from changelens.report import write_json, write_markdown
from changelens.runner import run_command
from changelens.scenarios import extract_changed_files, load_manifest


class Phase3ControlPlaneTests(unittest.TestCase):
    def test_evidence_schema_serializes_versioned_report(self):
        report = EvidenceReport("1.0", "run-1", "safe-change", "abc", ["file.txt"])
        payload = report.to_dict()
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["tools"], [])

    def test_subprocess_success_and_failure(self):
        success = run_command("success", [sys.executable, "-c", "print('ok')"], ROOT)
        failure = run_command("failure", [sys.executable, "-c", "import sys; print('bad'); sys.exit(3)"], ROOT)
        self.assertEqual(success.status, ToolStatus.PASSED)
        self.assertEqual(success.exit_code, 0)
        self.assertEqual(failure.status, ToolStatus.FAILED)
        self.assertEqual(failure.exit_code, 3)

    def test_timeout_and_unavailable_are_distinguished(self):
        timeout = run_command("timeout", [sys.executable, "-c", "import time; time.sleep(1)"], ROOT, 0)
        unavailable = run_command("missing", ["command-that-does-not-exist"], ROOT)
        self.assertEqual(timeout.status, ToolStatus.TIMED_OUT)
        self.assertTrue(timeout.timed_out)
        self.assertEqual(unavailable.status, ToolStatus.UNAVAILABLE)

    def test_report_generation(self):
        scenario = load_manifest(ROOT / "fixtures/scenarios/manifest.json")["safe-change"]
        report = EvidenceReport("1.0", "run-2", scenario.name, "abc", scenario.changed_files)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            write_json(report, destination / "evidence.json")
            write_markdown(report, scenario, destination / "report.md")
            self.assertEqual(json.loads((destination / "evidence.json").read_text())["scenario"], "safe-change")
            self.assertIn("# ChangeLens evidence report", (destination / "report.md").read_text())

    def test_scenario_discovery_and_changed_file_extraction(self):
        scenarios = load_manifest(ROOT / "fixtures/scenarios/manifest.json")
        self.assertEqual(len(scenarios), 5)
        files = extract_changed_files(ROOT / "fixtures/scenarios/api-compatibility-regression/change.patch")
        self.assertEqual(files, ["demo-app/order-api/src/main/java/com/changelens/orderapi/order/OrderDtos.java"])

    def test_integration_runs_infrastructure_scenario_and_writes_evidence(self):
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "changelens-agent")
        result = subprocess.run(
            [sys.executable, "-m", "changelens", "run", "--scenario", "infrastructure-security-regression"],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        self.assertEqual(result.returncode, 1)  # the fixture intentionally has findings
        paths = json.loads(result.stdout)
        evidence = json.loads(Path(paths["evidence"]).read_text())
        self.assertEqual(evidence["scenario"], "infrastructure-security-regression")
        self.assertEqual(len(evidence["security_findings"]), 3)
        self.assertEqual(evidence["policy"]["status"], "BLOCK")
        self.assertEqual(evidence["ai_analysis"]["decision"], "BLOCK")
        self.assertTrue(Path(paths["report"]).exists())


if __name__ == "__main__":
    unittest.main()
