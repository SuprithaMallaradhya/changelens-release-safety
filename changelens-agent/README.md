# ChangeLens control plane

This package runs the deterministic checks, evaluates release policy, and writes a versioned evidence report with a provider-neutral evidence analyst. It uses only the Python standard library.

From the repository root:

```bash
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

Each run creates `artifacts/<run-id>/evidence.json` and `artifacts/<run-id>/report.md`. The output records unavailable tools explicitly.

The default analyst is deterministic mock mode. It cites only fields present in the evidence report and cannot override the deterministic policy. To use an explicitly configured OpenAI-compatible endpoint:

```bash
CHANGELENS_MODEL_ENDPOINT=http://localhost:8000/v1/chat/completions \
CHANGELENS_MODEL=local-model \
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

Policy rules are configured in `changelens.policy.PolicyConfig`: critical security findings, failed required tests/contracts, error rate over 2%, and p95 latency over 1.5x baseline block; moderate latency increases and missing evidence require review. Rollback plans are recommendations only. The control plane does not apply scenario patches, alter the working tree, deploy anything, or execute rollback.

The GitHub Actions workflow at `.github/workflows/changelens.yml` uses `safe-change` by default for pull requests and supports selecting another manifest scenario through manual dispatch. It uploads the generated `artifacts/` directory and writes a workflow summary. It uses mock analyst mode, needs no API key, and enforces only the deterministic policy result. Arbitrary pull-request diff analysis and candidate patch application are not yet supported by the CLI, so the selected scenario limitation is intentional.
