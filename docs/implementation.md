# ChangeLens Implementation Plan

## Handoff objective

Build ChangeLens, an AI-assisted production-change safety platform. ChangeLens reviews a pull request, runs deterministic engineering checks, deploys a candidate version of a small demo service, compares runtime behavior with a baseline, and produces an evidence-backed approve, review, or block decision with a rollback plan.

This document is intended as a direct handoff to another Codex agent. Implement the MVP first; do not expand scope until the end-to-end workflow works.

## Product boundaries

### In scope for the MVP

- A small Spring Boot Order API used as the system under test.
- A mock Inventory service and PostgreSQL database.
- Docker Compose-based local execution.
- Pull-request-style diff analysis.
- Unit and integration tests.
- OpenAPI compatibility checks.
- Trivy, Semgrep, and Checkov integration where practical.
- Baseline versus candidate load testing.
- Prometheus/OpenTelemetry metrics or a simple compatible metrics interface.
- A Python/FastAPI ChangeLens control plane.
- An AI evidence analyst with structured JSON output.
- Explicit deterministic release gates.
- A GitHub Actions workflow or a local equivalent.
- Five reproducible change scenarios: safe, performance regression, API break, reliability regression, and infrastructure/security regression.

### Out of scope for the MVP

- Autonomous production deployments.
- Automatic destructive rollback.
- Real AWS, Azure, or Google Cloud resources.
- Managed Kubernetes.
- A custom workflow engine.
- A generic RAG chatbot.
- Treating LLM output as the source of truth for metrics or security findings.

## Core principle

Deterministic tools produce facts. The AI agent explains, correlates, prioritizes, and recommends. The final block/approve decision must be enforceable by deterministic policy rules.

## Target repository layout

```text
changelens/
├── demo-app/
│   └── order-api/
│       ├── inventory-mock/
│       ├── Dockerfile
│       └── docker-compose.yml
├── changelens-agent/
│   ├── app/
│   ├── analyzers/
│   ├── tools/
│   ├── policies/
│   ├── models/
│   └── reports/
├── tests/
├── load-tests/
├── fixtures/
├── infra/
├── .github/workflows/
├── architecture.md
├── README.md
└── pyproject.toml
```

The exact layout may change if a simpler structure is more maintainable, but keep the demo application and ChangeLens control plane clearly separated.

## Functional requirements

### Demo application

Create a small Spring Boot service with:

- `POST /orders`
- `GET /orders/{id}`
- `POST /orders/{id}/reserve`
- PostgreSQL persistence
- one downstream Inventory service
- OpenAPI specification
- health endpoint
- application metrics
- Docker Compose startup

The application must have a clean baseline that passes tests and produces repeatable latency measurements.

### Change scenarios

Create reproducible branches or fixture patches for:

1. **Safe change:** add an optional response field or improve a log message.
2. **Performance regression:** introduce an inefficient database query or remove an index.
3. **API regression:** rename or remove a required response field.
4. **Reliability regression:** remove a downstream timeout or failure handling.
5. **Infrastructure/security regression:** introduce an unsafe Terraform/Kubernetes setting.

Each scenario must include the expected outcome and the evidence that should cause it.

### Analysis pipeline

The control plane should support these operations:

```text
analyze_diff
run_tests
run_security_scans
run_contract_checks
deploy_candidate
run_synthetic_traffic
collect_metrics
compare_baseline
evaluate_policy
generate_explanation
generate_rollback_plan
```

Use subprocesses carefully, capture exit codes, stdout, stderr, timeouts, and tool versions. Never silently treat a failed scanner as a clean result.

### Evidence schema

Use a versioned, typed schema similar to:

```json
{
  "run_id": "string",
  "commit_sha": "string",
  "changed_files": [],
  "tests": {
    "passed": 0,
    "failed": 0,
    "exit_code": 0
  },
  "security_findings": [],
  "api_findings": [],
  "infrastructure_findings": [],
  "baseline_metrics": {
    "p95_latency_ms": 0,
    "error_rate": 0.0,
    "throughput_rps": 0.0
  },
  "candidate_metrics": {
    "p95_latency_ms": 0,
    "error_rate": 0.0,
    "throughput_rps": 0.0
  },
  "policy_decision": {
    "status": "APPROVE|REVIEW|BLOCK",
    "reasons": []
  }
}
```

Do not allow the model to invent evidence. The model receives this structured evidence and must cite evidence fields in its explanation.

### Deterministic release policy

Start with explicit configurable rules:

- Block if a critical security finding exists.
- Block if required contract tests fail.
- Block if error rate exceeds 2% in the test workload.
- Block if candidate p95 latency exceeds 1.5 times the baseline.
- Require review for medium/high findings or latency increases between 10% and 50%.
- Approve only when required checks pass and no block condition exists.

Make thresholds configuration-driven. Include the threshold values in the final report.

### AI evidence analyst

Implement a provider-neutral model interface. It should support:

- local/mock mode for no-cost development;
- an OpenAI-compatible endpoint later, if desired;
- strict structured output validation;
- prompt/version recording;
- evidence references;
- graceful fallback when the model is unavailable.

The agent should answer:

- What changed?
- Which components are affected?
- What evidence indicates risk?
- What is the recommended decision?
- What should be fixed?
- What is the rollback plan?

The deterministic policy decision remains authoritative.

## Implementation phases

### Phase 0: Repository and design setup

- Create the repository structure.
- Add a root README and architecture diagram.
- Add `.gitignore`, formatting, linting, and test commands.
- Record assumptions and local prerequisites.

### Phase 1: Demo service

- Generate the Spring Boot project.
- Add PostgreSQL persistence.
- Add Inventory mock service.
- Add API and OpenAPI schema.
- Add unit and integration tests.
- Add Docker Compose and health checks.

Exit criterion: the baseline service starts locally and passes all tests.

### Phase 2: Reproducible regressions

- Implement each of the five change scenarios.
- Add a scenario manifest with expected outcome and evidence.
- Add baseline load-test script.
- Record baseline metrics under a fixed workload.

Exit criterion: each scenario can be reproduced from a clean checkout.

### Phase 3: Control plane and tools

- Implement FastAPI endpoints or a CLI entry point.
- Add diff, test, scanner, contract, load-test, and metrics tools.
- Normalize outputs into the evidence schema.
- Add timeouts and failure handling.

Exit criterion: one command produces a complete evidence report.

### Phase 4: Policy and AI analysis

- Implement deterministic policy evaluation.
- Add structured model interface.
- Add evidence-grounded explanation and rollback plan.
- Validate model output with Pydantic or equivalent.

Exit criterion: safe, review, and block scenarios produce the expected decision.

### Phase 5: CI integration

- Add GitHub Actions pull-request workflow.
- Upload evidence as an artifact.
- Add a pull-request comment or generated Markdown report.
- Make the policy result the required check.

Exit criterion: a test pull request receives a reproducible ChangeLens report.

### Phase 6: Hardening and documentation

- Add unit tests for parsers and policies.
- Add integration tests for the end-to-end flow.
- Add negative tests for missing tools, malformed model output, and timeouts.
- Add benchmark methodology.
- Add screenshots and a short demo recording.
- Document limitations and what was not tested.

## Suggested first milestone

Before adding AI, complete this command:

```text
python -m changelens run --scenario performance-regression
```

It should:

1. start the demo service;
2. run tests;
3. run the load test;
4. collect baseline and candidate metrics;
5. evaluate deterministic policy;
6. write `artifacts/report.json` and `artifacts/report.md`.

Only add the AI analyst after this works.

## Verification requirements

For every reported metric, record:

- workload size;
- concurrency;
- test duration;
- machine/runtime details;
- application commit;
- tool versions;
- baseline and candidate definitions;
- whether the result is local, mocked, or live.

Do not claim production scale, cloud deployment, or autonomous remediation unless it has actually been implemented and measured.

## Final MVP acceptance criteria

The project is ready for portfolio use when:

- a fresh clone can run the baseline locally;
- the test scenarios are documented and repeatable;
- at least three regressions are detected;
- the safe scenario is not incorrectly blocked;
- the evidence report contains measured values;
- the AI explanation cites those values;
- deterministic policy rules remain authoritative;
- the pull-request workflow works or a local equivalent is documented;
- tests cover the core analyzers and policy engine;
- README explains architecture, tradeoffs, limitations, and reproducibility.
