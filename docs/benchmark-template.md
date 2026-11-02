# ChangeLens benchmark record

Copy this template for a measured baseline/candidate comparison. Replace every bracketed value with a recorded value; do not fill it with estimates.

## Workload

- Scenario: `[scenario]`
- Requests: `[POST /orders, GET /orders/{id}, POST /orders/{id}/reserve]`
- Concurrency: `[N]`
- Duration: `[N seconds]`
- Application commit: `[SHA]`
- Baseline definition: `[clean checkout or baseline SHA]`
- Candidate definition: `[candidate SHA or fixture]`

## Environment

- Operating system: `[recorded output]`
- Python: `[recorded version]`
- Java: `[recorded version]`
- Maven: `[recorded version]`
- Docker/Compose: `[recorded versions]`
- PostgreSQL: `[image/version]`
- CPU/memory: `[recorded host details]`
- Analyst mode: `[mock/local/external]`

## Results

| Metric | Baseline | Candidate | Regression result |
|---|---:|---:|---|
| p50 latency (ms) | `[value]` | `[value]` | `[pass/review/block]` |
| p95 latency (ms) | `[value]` | `[value]` | `[pass/review/block]` |
| p99 latency (ms) | `[value]` | `[value]` | `[pass/review/block]` |
| Throughput (requests/sec) | `[value]` | `[value]` | `[pass/review/block]` |
| Error rate | `[value]` | `[value]` | `[pass/review/block]` |

## Evidence

- Baseline artifact: `[path]`
- Candidate artifact: `[path]`
- Evidence report: `[path]`
- Markdown report: `[path]`
- Deterministic policy: `[APPROVE/REVIEW/BLOCK]`
- Limitations: `[measured limitations]`
