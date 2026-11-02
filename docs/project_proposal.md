# ChangeLens: AI-Powered Production Change Safety Platform

## Project summary

ChangeLens is an AI-assisted release-engineering platform that evaluates whether a software, database, or infrastructure change is safe to deploy.

Instead of relying on a single test suite or an LLM-generated opinion, ChangeLens combines deterministic engineering evidence—tests, security scans, API compatibility checks, infrastructure policies, load-test results, and runtime telemetry—and uses an AI agent to correlate the evidence, explain the risk, prioritize findings, and generate a rollback plan.

The system produces an approval-gated decision:

- **APPROVE:** required checks pass and no high-risk condition is present;
- **REVIEW:** evidence is ambiguous or risk is moderate;
- **BLOCK:** a release policy is violated.

## Problem statement

Modern software teams release frequently across microservices and cloud infrastructure. A change can pass unit tests while still causing:

- latency regressions;
- API incompatibilities;
- downstream timeouts;
- database performance problems;
- insecure cloud configuration;
- container vulnerabilities;
- unexpected operational impact.

Existing tools often produce disconnected findings. Engineers must manually correlate code changes, scanner output, test failures, infrastructure changes, and runtime behavior before deciding whether to release.

ChangeLens addresses this problem by creating a single, evidence-backed release assessment.

## Target users

- software engineers reviewing pull requests;
- platform and DevOps engineers;
- SRE teams;
- security engineers;
- release managers;
- teams operating microservices and cloud infrastructure.

## Example user story

An engineer submits a pull request that changes an order-processing endpoint.

ChangeLens:

1. identifies the changed code and affected service;
2. runs unit, integration, and API contract tests;
3. scans the container and infrastructure configuration;
4. deploys the candidate version in an isolated local environment;
5. runs synthetic traffic;
6. compares latency and error rate with the baseline;
7. identifies a database query regression;
8. blocks the release;
9. explains the evidence;
10. recommends a rollback and corrective action.

Example result:

> **BLOCKED:** Candidate p95 latency increased from [baseline value] ms to [candidate value] ms under [concurrency] concurrent requests. The regression affects the checkout path. Contract tests passed, but the database query count increased from [value] to [value]. Recommended action: restore the previous query plan, add the required index, and rerun the performance test.

## Product behavior

```text
Pull request
    |
    v
ChangeLens control plane
    |
    ├── code and diff analysis
    ├── unit/integration tests
    ├── API contract validation
    ├── security scanning
    ├── infrastructure policy checks
    ├── candidate deployment
    ├── synthetic traffic
    ├── runtime telemetry
    └── baseline comparison
            |
            v
      AI evidence analyst
            |
            v
   APPROVE / REVIEW / BLOCK
            |
            v
      Rollback plan + audit report
```

## Technical design

### Demo application

The system is demonstrated against a small Spring Boot Order Fulfillment API with:

- order creation and retrieval;
- inventory reservation through a mock downstream service;
- PostgreSQL persistence;
- OpenAPI documentation;
- health and metrics endpoints;
- Docker Compose execution;
- intentionally seeded safe and unsafe changes.

The demo application is a controlled system under test, not the primary portfolio project.

### ChangeLens control plane

The control plane is implemented in Python and exposes a CLI or FastAPI interface for running an assessment. It invokes tools, captures evidence, evaluates policies, calls the AI analyst, and produces reports.

### Deterministic tools

- Maven/Spring tests
- OpenAPI contract checks
- k6 or Locust load tests
- Trivy container scanning
- Semgrep code scanning
- Checkov Terraform scanning
- OPA/Rego policy evaluation
- OpenTelemetry and Prometheus metrics

### AI agent

The AI agent does not replace tests or scanners. It receives structured evidence and:

- summarizes the change;
- correlates findings across tools;
- identifies affected services;
- prioritizes risks;
- explains the release decision;
- proposes remediation;
- generates a rollback plan.

The deterministic policy engine remains authoritative for approval and blocking decisions.

## Example change scenarios

### Performance regression

An inefficient database query or removed index causes p95 latency to increase under load.

### API compatibility regression

A required response field is renamed or removed, causing consumer contract tests to fail.

### Reliability regression

A downstream request timeout or failure-handling path is removed.

### Security/infrastructure regression

A Terraform or Kubernetes change introduces public access, excessive IAM permissions, an insecure container, or an unsafe network rule.

### Safe change

An optional response field or non-functional logging change passes all checks.

## Skills demonstrated

### Software engineering

- Python and FastAPI
- Java and Spring Boot
- REST APIs
- PostgreSQL
- Docker
- automated testing
- typed schemas and structured outputs

### Cloud and platform engineering

- Terraform and infrastructure policy
- Kubernetes deployment concepts
- CI/CD with GitHub Actions
- container security
- service dependencies
- canary-style comparison
- release gates

### Reliability and observability

- OpenTelemetry
- Prometheus
- latency and error-rate analysis
- baseline comparison
- synthetic traffic
- rollback planning
- reproducible failure scenarios

### AI engineering

- tool-using AI agent
- structured model output
- evidence-grounded reasoning
- model fallback behavior
- evaluation of agent decisions
- human review for ambiguous outcomes

### Security

- Trivy and Semgrep
- Terraform security checks
- OPA/Rego policy-as-code
- IAM-aware risk analysis
- auditability
- least-privilege deployment decisions

## Why the project is distinctive

ChangeLens is not:

- a generic chatbot;
- a basic RAG application;
- a second workflow engine;
- a simple Terraform parser;
- an LLM wrapper that invents deployment decisions.

Its distinctive feature is the combination of:

1. deterministic engineering checks;
2. controlled candidate deployment;
3. runtime evidence;
4. AI-assisted cross-signal analysis;
5. approval-gated release policy;
6. rollback verification.

The AI reduces the human effort required to interpret fragmented engineering evidence, while deterministic tools protect correctness.

## Measurement plan

Every result should be reproducible and should record workload and environment details.

Measure:

- baseline and candidate p50/p95/p99 latency;
- baseline and candidate error rate;
- throughput under fixed concurrency;
- regression-detection latency;
- security findings detected;
- API compatibility failures detected;
- false-positive release decisions;
- agent evidence-citation accuracy;
- rollback-plan completeness;
- pipeline execution time.

Resume metrics should use placeholders until measured:

- `[N]` scenarios;
- `[N]/[N]` regressions detected;
- `[measured detection time]`;
- `[baseline p95]` ms versus `[candidate p95]` ms;
- `[measured false-positive rate]`;
- `[measured throughput]` requests/sec.

## Scope and cost

The MVP runs locally using Docker, Docker Compose, and optionally `kind` Kubernetes. It does not require AWS, Azure, or Google Cloud resources.

Potential no-cost components include:

- local PostgreSQL;
- local Docker containers;
- local Prometheus and Grafana;
- local OpenTelemetry Collector;
- local security scanners;
- GitHub Actions for a public repository;
- a local or mocked model provider.

Cloud adapters can be added later, but cloud deployment is not required to validate the core project.

## Delivery plan

### MVP: three focused days

**Day 1:** Build the Spring Boot application, PostgreSQL persistence, mock Inventory service, Docker Compose setup, tests, OpenAPI schema, and seeded regressions.

**Day 2:** Add security scanners, contract checks, load tests, candidate deployment, baseline comparison, and deterministic release policies.

**Day 3:** Add the AI evidence analyst, GitHub Actions integration, pull-request report, rollback-plan generation, documentation, and demo scenarios.

### Optional polish

- Kubernetes execution using `kind`;
- dependency graph visualization;
- historical regression dashboard;
- provider-specific AWS/Azure/Google Cloud Terraform checks;
- human approval workflow;
- agent evaluation dataset;
- cloud deployment adapters;
- canary traffic routing.

## Interview discussion points

### Why not let the LLM make the final decision?

LLMs can hallucinate and are not the correct source of truth for measured latency, security findings, or policy thresholds. ChangeLens uses deterministic gates for enforcement and the model for interpretation and communication.

### How do you know the agent is useful?

Compare static-pipeline-only results with agent-assisted results using time to understand failures, finding prioritization, evidence-citation accuracy, and rollback-plan completeness.

### How do you prevent fabricated evidence?

The agent receives a typed evidence object, must reference evidence fields, and cannot create metrics. Invalid output is rejected and the deterministic report is retained.

### How do you prevent unsafe rollback?

The MVP generates rollback plans but does not execute destructive actions automatically. Any future execution would require authorization, approval, idempotency, and post-action verification.

### Why is the demo application small?

The application is deliberately controlled so regressions are reproducible. The engineering challenge is the release-safety system, not implementing a large business domain.

## Resume-ready project description

### Short version

**ChangeLens — AI-Powered Production Change Safety Platform**

Built an AI-assisted release-engineering platform that combines code analysis, security scanning, API compatibility checks, infrastructure policy, synthetic load testing, and runtime telemetry to produce approval-gated deployment decisions and rollback plans.

### Resume bullets

- Built ChangeLens, an AI-assisted release safety platform that correlated code diffs, test results, security scans, API contracts, infrastructure policies, and runtime telemetry before deployment.
- Deployed candidate Spring Boot service versions in Docker/Kubernetes and compared OpenTelemetry/Prometheus metrics under synthetic load, detecting `[N]/[N]` intentionally injected regressions.
- Integrated Trivy, Semgrep, Checkov, OPA/Rego, and GitHub Actions to enforce security, API compatibility, and infrastructure quality gates on pull requests.
- Implemented a structured AI evidence analyst that generated release explanations, affected-component analysis, and rollback plans without allowing model output to override deterministic policy gates.
- Measured `[baseline p95]` ms versus `[candidate p95]` ms latency, `[measured throughput]` requests/sec, and `[measured detection time]` regression-detection latency across `[N]` release scenarios.

### Compact one-line version

AI-powered release safety platform combining deterministic CI/CD, security, performance, observability, and rollback analysis for microservice deployments.

## Portfolio description

ChangeLens treats software delivery as an evidence problem. Before a release is promoted, it combines what changed, what tests found, what security scanners detected, how the candidate behaves under load, and which services may be affected. An AI agent turns that evidence into an understandable release assessment, while deterministic policies keep the final decision safe and reproducible.

## Honest limitations

- The MVP validates local or simulated deployments rather than production traffic.
- The demo application is intentionally small.
- Cloud-provider adapters are optional extensions.
- AI explanations are not independently authoritative.
- Performance results depend on the documented local environment and workload.
- No resume metric should be published until it has been measured and recorded.
