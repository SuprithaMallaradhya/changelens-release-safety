# ChangeLens demo script

This script is a repeatable portfolio demonstration. Run it from a clean checkout and record actual run IDs and measured values instead of copying example numbers.

## Phase 8 verified decision matrix

The following results were verified locally on 2026-11-04 using an isolated baseline archive for safe and scenario validation. The intentionally breaking branch was not modified.

| Validation | Result | Process outcome |
|---|---|---:|
| Safe fixture applied to the `origin/main` baseline and analyzed as a real base/head diff | `APPROVE` | exit 0 |
| `test/phase7-breaking-api` analyzed from `main` to `HEAD` | `BLOCK` | exit 1 |
| Performance scenario without a running candidate stack | `REVIEW` | exit 0 |
| Reliability scenario without a running candidate stack | `REVIEW` | exit 0 |
| Infrastructure/security scenario | `BLOCK` | exit 1 |

`REVIEW` is successful but emits a human-review warning in GitHub Actions. `BLOCK` publishes the summary and uploads the evidence artifact before the final enforcement step fails. Runtime-dependent performance and reliability behavior still requires Docker Compose and a measured candidate workload.

## 1. Prepare

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
(cd demo-app/order-api && mvn test)
```

If demonstrating live health and load evidence, start the local stack:

```bash
cd demo-app/order-api
docker compose up --build
cd ../..
curl http://localhost:8080/actuator/health
```

## 2. Safe change

Run the control plane with the default mock analyst:

```bash
PYTHONPATH=changelens-agent CHANGELENS_MODEL_PROVIDER=mock \
python3 -m changelens run --scenario safe-change
```

With complete passing evidence, show `policy.status = APPROVE`. Without a running application, show that the honest result is `REVIEW` because health and candidate performance evidence are unavailable.

## 3. Breaking API change

```bash
PYTHONPATH=changelens-agent CHANGELENS_MODEL_PROVIDER=mock \
python3 -m changelens run --scenario api-compatibility-regression
```

Show the static patch evidence that removes the required `status` field, the deterministic `BLOCK`, and the analyst explanation that also remains `BLOCK`.

For actual pull-request analysis, use committed branches instead of a manifest scenario:

```bash
PYTHONPATH=changelens-agent python3 -m changelens analyze-diff \
  --base-ref main --head-ref test/safe-change
PYTHONPATH=changelens-agent python3 -m changelens analyze-diff \
  --base-ref main --head-ref test/api-breaking-change-v2
```

The first report should say `Analysis mode: pull_request`, list the real changed files, and produce `APPROVE`. The second should identify `OrderDtos.java` and produce `BLOCK`. Runtime checks that are not started are shown as skipped.

## 4. Inspect reports

For the run ID printed by the command:

```bash
python3 -m json.tool artifacts/<run-id>/evidence.json
less artifacts/<run-id>/report.md
```

Point out that `policy` is authoritative, while `ai_analysis` contains explanation, references, recommendation, and proposed rollback only.

## 5. GitHub Actions

Open a pull request containing a small safe documentation or fixture change. In **Checks**, open `ChangeLens pull-request safety` and show:

- the workflow summary;
- the mock provider status;
- the deterministic policy result;
- the uploaded `changelens-evidence-<run-id>` artifact.

Confirm that the summary says `Analysis mode: pull_request` and shows the actual base/head commits and changed files; it should not select `safe-change` for the pull-request event.

After the safe workflow has run, use **Actions → Run workflow** and select `infrastructure-security-regression` to demonstrate a blocking result. The artifact should still be available after the check fails.

## Screenshot checklist

Capture real screenshots only after running the workflow:

- [ ] pull request Checks tab showing the workflow;
- [ ] successful safe workflow summary;
- [ ] downloaded evidence artifact contents;
- [ ] blocking security workflow summary;
- [ ] policy `BLOCK` alongside the preserved artifact.

No screenshots or metrics are included here until they are actually captured.
