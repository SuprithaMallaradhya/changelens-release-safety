# Repository guidance

## Current scope

Phases 1–5 are complete and must remain behaviorally stable. Phase 2 adds reproducible scenario fixtures and a baseline load test; Phase 3 adds the control plane; Phase 4 adds policy and analyst output; Phase 5 adds GitHub Actions. The Spring Boot demo application, PostgreSQL configuration, mock Inventory service, Docker files, Maven configuration, resources, and tests are under `demo-app/order-api/`.

Run Phase 1 tests with `cd demo-app/order-api && mvn test`. Start the local stack with `cd demo-app/order-api && docker compose up --build`.

Do not change the Spring Boot application behavior, add cloud resources, deploy automatically, or execute rollback. Keep scenario patches outside the baseline application source. Generated evidence under `artifacts/` is ignored.

## Layout

- `docs/`: implementation and project documentation.
- `demo-app/order-api/`: Phase 1 application and its local dependencies.
- `fixtures/scenarios/`: Phase 2 change patches, security fixture, and manifest.
- `load-tests/`: Phase 2 dependency-free baseline load test and measured baseline record.
- `tests/`: Phase 2 scenario and contract/security validators.
- `changelens-agent/`, `infra/`, `scripts/`, `.github/workflows/`: reserved for later phases.
