import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/changelens.yml"


class Phase5WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text()

    def test_workflow_exists_and_triggers_on_pull_requests(self):
        self.assertTrue(WORKFLOW.exists())
        self.assertRegex(self.text, r"(?m)^  pull_request:")
        self.assertIn("workflow_dispatch:", self.text)

    def test_environment_and_test_commands_are_explicit(self):
        self.assertIn("actions/checkout@v4", self.text)
        self.assertIn("fetch-depth: 0", self.text)
        self.assertIn("actions/setup-python@v5", self.text)
        self.assertIn("actions/setup-java@v4", self.text)
        self.assertIn("mvn dependency:go-offline -B", self.text)
        self.assertIn("working-directory: demo-app/order-api", self.text)
        for command in (
            "mvn test",
            "python -m unittest tests.test_phase2_scenarios",
            "python -m unittest tests.test_phase3_control_plane",
            "python -m unittest tests.test_phase4_policy_analyst",
            "python -m unittest tests.test_phase7_diff_analysis",
        ):
            self.assertIn(command, self.text)

    def test_mock_provider_and_artifact_upload_are_configured(self):
        self.assertIn("CHANGELENS_MODEL_PROVIDER: mock", self.text)
        self.assertNotIn("CHANGELENS_MODEL_API_KEY", self.text)
        self.assertIn("actions/upload-artifact@v4", self.text)
        self.assertIn("if: always()", self.text)
        self.assertIn("path: artifacts/", self.text)

    def test_pull_requests_use_actual_base_and_head_analysis(self):
        self.assertIn("if [ \"$GITHUB_EVENT_NAME\" = \"pull_request\" ]", self.text)
        self.assertIn("python -m changelens analyze-pr --base-ref \"$BASE_SHA\" --head-ref \"$HEAD_SHA\"", self.text)
        self.assertIn("BASE_SHA:", self.text)
        self.assertIn("HEAD_SHA:", self.text)
        self.assertNotIn("pull requests use safe-change by default", self.text)

    def test_policy_failure_is_enforced_after_reports_are_published(self):
        self.assertIn("name: Enforce deterministic policy", self.text)
        self.assertRegex(self.text, r'(?s)BLOCK\).*?exit 1')
        self.assertIn("name: Upload ChangeLens reports", self.text)
        self.assertLess(self.text.index("Upload ChangeLens reports"), self.text.index("Enforce deterministic policy"))

    def test_no_hard_coded_machine_paths_or_cloud_credentials(self):
        self.assertIsNone(re.search(r"/Users/|/home/|[A-Za-z]:\\", self.text))
        self.assertNotRegex(self.text, r"(?i)(aws_access_key|azure_client_secret|google_application_credentials)")
        self.assertNotIn("docker login", self.text)

    def test_summary_contains_required_report_fields(self):
        for field in ("scenario", "commit_sha", "changed_files", "tests", "security_findings",
                      "api_findings", "performance", "policy", "summary", "rollback_plan", "limitations"):
            self.assertIn(field, self.text)


if __name__ == "__main__":
    unittest.main()
