# Current limitations

- Scenario mode runs documented fixture scenarios. Pull-request mode now derives changed files from committed base/head refs and analyzes the head in a temporary archive workspace.
- Pull-request static analysis skips application health, API contract, and load checks because it does not automatically start a candidate runtime; skipped checks are recorded explicitly and are not treated as passed.
- Candidate deployment, automatic rollback, and production traffic are not implemented.
- The demo uses local Docker Compose, PostgreSQL, and a mock Inventory service. No cloud resources are provisioned.
- Live API and load checks are unavailable when the application is not running; ChangeLens records that as unavailable and policy normally returns `REVIEW`.
- Performance measurements are environment-dependent. The repository contains a measured local reference, but it is not a production-scale claim.
- The default analyst is deterministic mock mode. An external provider is optional and remains subordinate to deterministic policy.
- The available security validator is a small fixture validator, not a replacement for broad Trivy, Semgrep, Checkov, or OPA coverage.
- No automatic pull-request comment is posted; GitHub Actions uses the workflow summary and uploaded artifacts with `contents: read`.
- Candidate code is still executed by local test tools inside the temporary workspace. Forked or untrusted pull requests require repository-level security review; this is not a sandbox or malware boundary.
- GitHub Actions must fetch the base/head commits. Shallow or unavailable fork refs cause a clear analysis failure rather than a scenario fallback.
- The repository does not claim production availability, scale, cost savings, regression-detection time, or false-positive rates without a recorded benchmark.
