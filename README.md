# ChangeLens

ChangeLens is an AI-assisted production-change safety platform. The current repository contains the Phase 1 demo service plus Phase 2 scenario fixtures and a baseline load-test workflow. The small Spring Boot Order API is the system under test; it persists orders in PostgreSQL and reserves inventory through a separate local mock service.

The Phase 1 application lives in [`demo-app/order-api/`](demo-app/order-api/). Future ChangeLens components have reserved top-level directories but are not implemented yet.

## Run locally

From the Phase 1 application directory:

```bash
cd demo-app/order-api
docker compose up --build
curl -X POST http://localhost:8080/orders -H 'Content-Type: application/json' \
  -d '{"customerId":"customer-1","sku":"sku-1","quantity":2}'
curl http://localhost:8080/actuator/health
```

OpenAPI UI is available at http://localhost:8080/swagger-ui.html and the JSON document at http://localhost:8080/v3/api-docs.

Run the Phase 1 tests from `demo-app/order-api/` with:

```bash
mvn test
```

Run Phase 2 scenario tests and validate the scenario patches from the repository root:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
for patch in fixtures/scenarios/*/change.patch; do git apply --check "$patch"; done
```

Run the baseline load test after the Compose stack is healthy:

```bash
python3 load-tests/baseline.py \
  --base-url http://localhost:8080 \
  --concurrency 4 \
  --duration 30 \
  --output artifacts/baseline.json
```

Scenario definitions and expected evidence are in `fixtures/scenarios/manifest.json`.

## Run the ChangeLens control plane

The Phase 3 control plane is a small standard-library Python package. From the repository root, run a scenario without applying its patch:

```bash
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

Replace `safe-change` with any scenario name in the manifest. Each run creates ignored artifacts at `artifacts/<run-id>/evidence.json` and `artifacts/<run-id>/report.md`. The report records command output, exit codes, durations, timeouts, unavailable services, test results, security findings, API findings, and load-test metrics when the application is reachable.

Run the Phase 3 unit and integration tests with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

The integration test runs the infrastructure-security scenario and expects its intentionally unsafe fixture to be detected.

## Evaluate policy and evidence explanations

The control-plane run now evaluates deterministic release rules and adds an evidence-grounded analyst section to the same reports. The mock analyst is the default and requires no API key:

```bash
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

The report contains a deterministic `APPROVE`, `REVIEW`, or `BLOCK` decision, triggered rules, thresholds, measured values, evidence references, an explanation, and a proposed rollback plan. The policy result is authoritative. The analyst cannot turn a deterministic `BLOCK` into `APPROVE`, and its output never replaces factual tool results.

An optional OpenAI-compatible JSON endpoint is used only when explicitly configured:

```bash
CHANGELENS_MODEL_ENDPOINT=http://localhost:8000/v1/chat/completions \
CHANGELENS_MODEL=local-model \
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

`CHANGELENS_MODEL_API_KEY` may be supplied for providers that require it; it is never written to reports. If the provider is unavailable or returns invalid JSON, ChangeLens preserves the deterministic decision and writes a fallback explanation.

Run all tests, including policy and analyst tests, with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Rollback is proposed as text only. ChangeLens does not execute rollback, deploy candidates, or integrate with GitHub Actions yet. See [`changelens-agent/README.md`](changelens-agent/README.md) and [`docs/ai-evidence-safety.md`](docs/ai-evidence-safety.md) for details.
