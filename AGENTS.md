# Repository guidance

## Current scope

Phase 1 is complete and must remain behaviorally stable. Phase 2 adds reproducible scenario fixtures and a baseline load test without changing the baseline application. The Spring Boot demo application, PostgreSQL configuration, mock Inventory service, Docker files, Maven configuration, resources, and tests are under `demo-app/order-api/`.

Run Phase 1 tests with `cd demo-app/order-api && mvn test`. Start the local stack with `cd demo-app/order-api && docker compose up --build`.

Do not implement the ChangeLens control plane, AI agent, cloud resources, or Phase 3+ work unless explicitly requested. Keep scenario patches outside the baseline application source.

## Layout

- `docs/`: implementation and project documentation.
- `demo-app/order-api/`: Phase 1 application and its local dependencies.
- `fixtures/scenarios/`: Phase 2 change patches, security fixture, and manifest.
- `load-tests/`: Phase 2 dependency-free baseline load test and measured baseline record.
- `tests/`: Phase 2 scenario and contract/security validators.
- `changelens-agent/`, `infra/`, `scripts/`, `.github/workflows/`: reserved for later phases.
