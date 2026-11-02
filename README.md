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

Scenario definitions and expected evidence are in `fixtures/scenarios/manifest.json`. The ChangeLens control plane, AI agent, cloud resources, and frontend remain intentionally unimplemented.
