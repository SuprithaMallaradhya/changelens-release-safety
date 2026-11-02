# ChangeLens control plane

This package runs the deterministic Phase 3 checks and writes a versioned evidence report. It uses only the Python standard library.

From the repository root:

```bash
PYTHONPATH=changelens-agent python3 -m changelens run --scenario safe-change
```

Each run creates `artifacts/<run-id>/evidence.json` and `artifacts/<run-id>/report.md`. The output records unavailable tools explicitly. The control plane does not apply scenario patches, alter the working tree, implement AI analysis, or make release-policy decisions.
