# Current limitations

- The control plane runs documented scenarios; it does not yet derive and apply an arbitrary pull-request candidate diff.
- The pull-request workflow uses `safe-change` by default. Other scenarios are selected through manual workflow dispatch.
- Candidate deployment, automatic rollback, and production traffic are not implemented.
- The demo uses local Docker Compose, PostgreSQL, and a mock Inventory service. No cloud resources are provisioned.
- Live API and load checks are unavailable when the application is not running; ChangeLens records that as unavailable and policy normally returns `REVIEW`.
- Performance measurements are environment-dependent. The repository contains a measured local reference, but it is not a production-scale claim.
- The default analyst is deterministic mock mode. An external provider is optional and remains subordinate to deterministic policy.
- The available security validator is a small fixture validator, not a replacement for broad Trivy, Semgrep, Checkov, or OPA coverage.
- No automatic pull-request comment is posted; GitHub Actions uses the workflow summary and uploaded artifacts with `contents: read`.
- The repository does not claim production availability, scale, cost savings, regression-detection time, or false-positive rates without a recorded benchmark.
