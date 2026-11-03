# ChangeLens control plane

This package runs the deterministic checks, evaluates release policy, and writes a versioned evidence report with a provider-neutral evidence analyst. It uses only the Python standard library.

From the repository root:

```bash
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

Each run creates `artifacts/<run-id>/evidence.json` and `artifacts/<run-id>/report.md`. The output records unavailable tools explicitly.

For actual committed pull-request analysis, provide the base and head commits:

```bash
PYTHONPATH=changelens-agent python3 -m changelens analyze-pr \
  --base-ref <base-commit> --head-ref <head-commit>
```

`analyze-diff` is the equivalent local name. The command computes the real git diff, exports the head commit to a temporary archive workspace, runs Maven and relevant Python/security checks there, and cleans the workspace afterward. Missing runtime services are recorded as `skipped`, never as passed. Deleted and binary files are represented in the diff metadata without being opened as text.

The default analyst is deterministic mock mode. It cites only fields present in the evidence report and cannot override the deterministic policy. To use an explicitly configured OpenAI-compatible endpoint:

```bash
CHANGELENS_MODEL_ENDPOINT=http://localhost:8000/v1/chat/completions \
CHANGELENS_MODEL=local-model \
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

Policy rules are configured in `changelens.policy.PolicyConfig`: critical security findings, failed required tests/contracts, error rate over 2%, and p95 latency over 1.5x baseline block; moderate latency increases and missing evidence require review. Rollback plans are recommendations only. The control plane does not apply scenario patches, alter the working tree, deploy anything, or execute rollback.

The GitHub Actions workflow at `.github/workflows/changelens.yml` uses actual base/head diff analysis for pull requests and supports selecting a manifest scenario through manual dispatch. It uploads the generated `artifacts/` directory and writes a workflow summary. It uses mock analyst mode, needs no API key, and enforces only the deterministic policy result. Candidate code is executed from a temporary archive, not the developer's worktree; untrusted forked code still requires caution.
