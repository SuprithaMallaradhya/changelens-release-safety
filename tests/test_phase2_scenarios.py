import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "fixtures/scenarios/manifest.json"
ORDER_DTO = ROOT / "demo-app/order-api/src/main/java/com/changelens/orderapi/order/OrderDtos.java"
INVENTORY_CLIENT = ROOT / "demo-app/order-api/src/main/java/com/changelens/orderapi/inventory/InventoryClient.java"


class Phase2ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.by_name = {scenario["name"]: scenario for scenario in cls.manifest["scenarios"]}

    def test_manifest_has_all_five_scenarios_and_required_metadata(self):
        self.assertEqual(
            set(self.by_name),
            {
                "safe-change",
                "performance-regression",
                "api-compatibility-regression",
                "reliability-regression",
                "infrastructure-security-regression",
            },
        )
        for scenario in self.manifest["scenarios"]:
            for field in ("changed_files", "setup", "expected_outcome", "expected_evidence", "validation_command"):
                self.assertTrue(scenario[field], f"{scenario['name']} is missing {field}")

    def test_safe_patch_preserves_required_response_fields_and_is_additive(self):
        patch = (ROOT / "fixtures/scenarios/safe-change/change.patch").read_text()
        baseline = ORDER_DTO.read_text()
        self.assertIn("public OrderStatus status;", baseline)
        self.assertIn("+        public String confirmationMessage;", patch)
        self.assertNotIn("-        public OrderStatus status;", patch)

    def test_api_patch_removes_a_field_required_by_contract(self):
        patch = (ROOT / "fixtures/scenarios/api-compatibility-regression/change.patch").read_text()
        contract = json.loads((ROOT / "tests/contracts/order-response.json").read_text())
        self.assertIn("-        public OrderStatus status;", patch)
        self.assertIn("status", contract["required"])

    def test_reliability_patch_removes_downstream_failure_handling(self):
        patch = (ROOT / "fixtures/scenarios/reliability-regression/change.patch").read_text()
        baseline = INVENTORY_CLIENT.read_text()
        self.assertIn("catch (RestClientException ex)", baseline)
        self.assertIn("-        } catch (RestClientException ex) {", patch)
        self.assertIn("-            return false;", patch)

    def test_security_validator_detects_insecure_fixture(self):
        validator = ROOT / "tests/check_security_fixture.py"
        fixture = ROOT / "fixtures/scenarios/infrastructure-security-regression/kubernetes.yaml"
        result = subprocess.run([sys.executable, str(validator), str(fixture)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("3 finding(s)", result.stdout)


if __name__ == "__main__":
    unittest.main()
