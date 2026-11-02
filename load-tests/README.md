# Baseline load test

`baseline.py` uses only the Python standard library. It runs a fixed workload with four concurrent workers for thirty seconds. Each worker repeatedly performs:

1. `POST /orders`
2. `GET /orders/{id}`
3. `POST /orders/{id}/reserve`

It reports request count, p50/p95/p99 latency, throughput, and error rate as JSON. The exact baseline command is:

```bash
python3 load-tests/baseline.py \
  --base-url http://localhost:8080 \
  --concurrency 4 \
  --duration 30 \
  --output artifacts/baseline.json
```

Run it after starting the application from `demo-app/order-api/` with Docker Compose. Do not compare results across different workload, host, Docker, database, or application versions without recording those differences.

## Baseline record

The following baseline was measured on 2026-11-01/02 in the local Docker Compose environment. It is a reference point for later candidate comparisons, not a universal performance claim.

| Field | Value |
|---|---|
| Workload | `POST /orders`, `GET /orders/{id}`, `POST /orders/{id}/reserve` |
| Concurrency | `4` |
| Duration | `30 seconds` |
| Requests | `31,620` |
| p50 latency | `3.38 ms` |
| p95 latency | `6.33 ms` |
| p99 latency | `10.09 ms` |
| Throughput | `1,053.66 requests/sec` |
| Error rate | `0.0` |
| Environment | `Docker Server 29.4.0; PostgreSQL 16-alpine; Order API Java 11 container; local developer machine; host CPU/memory not captured` |

The exact output was written during the run to `artifacts/baseline.json` (ignored as generated output). Repeat the documented command after changing the application and record the candidate environment before comparing values.
