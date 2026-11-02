# ChangeLens

ChangeLens is an AI-assisted production-change safety platform. The current repository contains the Phase 1 demo service: a small Spring Boot Order API used as the system under test. It persists orders in PostgreSQL and reserves inventory through a separate local mock service.

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

The current phase intentionally does not include the ChangeLens control plane, AI agent, cloud resources, regression fixtures, or frontend.
