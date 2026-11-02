# Reproducible evaluation

The evaluation separates deterministic correctness from performance measurement. A result is only comparable when the workload, application version, environment, and tool versions are recorded together.

## Environment record

Record the output of:

```bash
uname -a
python3 --version
java -version
mvn --version
docker version
docker compose version
```

The local Compose database is PostgreSQL `16-alpine` as declared by `demo-app/order-api/docker-compose.yml`. Record the actual Docker engine and host CPU/memory for every benchmark; they are not inferred by ChangeLens.

## Test procedure

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
(cd demo-app/order-api && mvn test)
for patch in fixtures/scenarios/*/change.patch; do git apply --check "$patch"; done
```

Run the control plane from the repository root:

```bash
PYTHONPATH=changelens-agent CHANGELENS_MODEL_PROVIDER=mock \
python3 -m changelens run --scenario <scenario>
```

The command does not apply patches or alter the working tree. To measure a candidate, use a temporary checkout or branch, apply the selected fixture there, and record the candidate commit separately.

## Load-test procedure

Start Compose and wait for the health endpoint, then run the fixed workload:

```bash
python3 load-tests/baseline.py \
  --base-url http://localhost:8080 \
  --concurrency 4 \
  --duration 30 \
  --output artifacts/<run-id>/baseline.json
```

The workload exercises order creation, retrieval, and reservation with concurrency `4` for `30` seconds. Do not compare baseline and candidate values when these parameters or the environment differ. The script reports p50, p95, p99, throughput, and error rate.

## Inspecting artifacts

```bash
python3 -m json.tool artifacts/<run-id>/evidence.json
less artifacts/<run-id>/report.md
```

Check the commit SHA, tool statuses, workload details, and limitations before interpreting a policy result. `REVIEW` is the honest outcome when required evidence is missing.
