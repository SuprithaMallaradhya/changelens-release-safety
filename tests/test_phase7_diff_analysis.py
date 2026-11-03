import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "changelens-agent"))

from changelens.diff_analysis import DiffAnalysisError, _parse_name_status, extract_diff
from changelens.models import ToolResult, ToolStatus
from changelens.pr_analysis import analyze_pull_request


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return result.stdout.strip()


class Phase7DiffTests(unittest.TestCase):
    def repository(self):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        git(root, "init", "-q")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "ChangeLens Test")
        return directory, root

    def test_changed_files_and_empty_diff_from_real_git_refs(self):
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        (root / "file.txt").write_text("one\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        base = git(root, "rev-parse", "HEAD")
        self.assertEqual(extract_diff(root, base, base).files, [])
        (root / "file.txt").write_text("one\ntwo\n")
        (root / "deleted.txt").write_text("remove\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "candidate")
        diff = extract_diff(root, base, "HEAD")
        self.assertEqual([item.path for item in diff.files], ["deleted.txt", "file.txt"])
        self.assertEqual([item.status for item in diff.files], ["A", "M"])

    def test_deleted_and_binary_files_are_safe(self):
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        (root / "binary.bin").write_bytes(b"\x00\x01")
        (root / "deleted.txt").write_text("gone\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        base = git(root, "rev-parse", "HEAD")
        (root / "binary.bin").write_bytes(b"\x00\x02")
        (root / "deleted.txt").unlink()
        git(root, "add", "-A")
        git(root, "commit", "-qm", "candidate")
        diff = extract_diff(root, base, "HEAD")
        self.assertEqual({item.path for item in diff.files}, {"binary.bin", "deleted.txt"})
        self.assertIn("D", {item.status for item in diff.files})

    def test_missing_ref_and_path_traversal_are_rejected(self):
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        (root / "file.txt").write_text("one\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        with self.assertRaises(DiffAnalysisError):
            extract_diff(root, "missing-base", "HEAD")
        with self.assertRaises(DiffAnalysisError):
            _parse_name_status("M\0../outside\0")

    @patch("changelens.pr_analysis.run_maven")
    @patch("changelens.pr_analysis.run_python_tests")
    def test_actual_pr_evidence_isolated_and_safe_candidate_approves(self, python_tests, maven):
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        (root / "demo-app/order-api/src/main/java/com/example/OrderDtos.java").parent.mkdir(parents=True)
        (root / "demo-app/order-api/src/main/java/com/example/OrderDtos.java").write_text(
            "public OrderStatus status;\n"
        )
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        base = git(root, "rev-parse", "HEAD")
        (root / "README.md").write_text("optional note\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "safe")
        maven.return_value = ToolResult("maven-tests", "mvn test", ToolStatus.PASSED, 0, 1)
        python_tests.side_effect = lambda candidate, module, timeout, env: ToolResult(
            f"{module}-tests", "python tests", ToolStatus.PASSED, 0, 1)
        report, evidence, markdown = analyze_pull_request(root, base, "HEAD", timeout=5)
        self.assertEqual(report.analysis_mode, "pull_request")
        self.assertEqual(report.policy["status"], "APPROVE")
        self.assertEqual(report.cleanup_status, "cleaned")
        self.assertTrue(evidence.exists())
        self.assertIn("Analysis mode: `pull_request`", markdown.read_text())

    @patch("changelens.pr_analysis.run_maven")
    @patch("changelens.pr_analysis.run_python_tests")
    def test_breaking_candidate_blocks_and_identifies_file(self, python_tests, maven):
        temporary, root = self.repository()
        self.addCleanup(temporary.cleanup)
        source = root / "demo-app/order-api/src/main/java/com/example/OrderDtos.java"
        source.parent.mkdir(parents=True)
        source.write_text("public OrderStatus status;\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        base = git(root, "rev-parse", "HEAD")
        source.write_text("public String id;\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "breaking")
        maven.return_value = ToolResult("maven-tests", "mvn test", ToolStatus.FAILED, 1, 1)
        python_tests.side_effect = lambda candidate, module, timeout, env: ToolResult(
            f"{module}-tests", "python tests", ToolStatus.PASSED, 0, 1)
        report, _, _ = analyze_pull_request(root, base, "HEAD", timeout=5)
        self.assertEqual(report.policy["status"], "BLOCK")
        self.assertTrue(any(path.endswith("OrderDtos.java") for path in report.changed_files))
        self.assertTrue(report.api_findings)


if __name__ == "__main__":
    unittest.main()
