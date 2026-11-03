# ChangeLens architecture

ChangeLens is a local-first release-safety workflow. The demo application is deliberately small; the engineering focus is collecting trustworthy evidence around a change.

```text
Pull request or selected scenario
              |
              v
      GitHub Actions / CLI
              |
   +----------+-----------+
   | deterministic tools  |
   | patch, Maven, API,   |
   | security, health,    |
   | load test            |
   +----------+-----------+
              |
              v
        evidence.json
              |
       deterministic policy
              |
      APPROVE / REVIEW / BLOCK
              |
        evidence analyst
              |
          report.md
```

## Components

- **Demo application:** `demo-app/order-api/` contains the Spring Boot Order API, PostgreSQL persistence, and local Inventory mock. Docker Compose supplies the local runtime.
- **Control plane:** `changelens-agent/changelens/` provides the CLI, safe subprocess runner, scenario discovery, tool adapters, evidence models, and report writers.
- **Deterministic tools:** patch validation, Maven tests, the existing security fixture validator, the OpenAPI contract check, health validation, and the fixed baseline load test. Tool output includes status, exit code, duration, stdout, stderr, and timeout state.
- **Evidence schema:** `EvidenceReport` is serialized as version `1.0` JSON. Factual tool output is retained in `artifacts/<run-id>/evidence.json`; generated reports are ignored by Git.
- **Policy engine:** `policy.py` applies explicit thresholds and produces a typed policy result with reasons, measured values, thresholds, and evidence references.
- **AI analyst:** the mock provider is the default. An explicitly configured OpenAI-compatible provider may summarize bounded evidence, but its structured output is validated and cannot weaken a deterministic decision.
- **GitHub Actions:** `.github/workflows/changelens.yml` runs actual base/head PR analysis, uploads artifacts, and writes `GITHUB_STEP_SUMMARY`. Manual dispatch retains selected scenario mode. It uses `contents: read` and does not comment, deploy, merge, or roll back.

## Analysis modes

Scenario mode (`run --scenario`) reads a documented fixture manifest and is used for repeatable regression demonstrations. Pull-request mode (`analyze-pr` or `analyze-diff`) resolves actual base/head commits, computes the real diff, and uses the head commit as the candidate. It does not use the scenario manifest to decide which files changed.

The candidate is exported with `git archive` into a temporary directory. Maven, Python tests, and applicable fixture checks run there. The developer's working tree is not changed, archive links and traversal paths are rejected, and cleanup status is recorded. Runtime checks that require a separately started candidate service are explicitly skipped in static PR mode.

## Artifact flow

Each CLI run creates:

```text
artifacts/<run-id>/
├── evidence.json   # factual evidence plus policy and analyst sections
├── report.md       # human-readable report
└── baseline.json   # present when the live load test runs
```

The workflow uploads the `artifacts/` directory before enforcing the policy result. A `BLOCK` therefore preserves its evidence even though the final check fails.

## Why the AI is not authoritative

Tests, scanners, and measurements are facts. The policy engine enforces the release decision. The analyst only explains those facts, cites known evidence fields, and proposes a rollback plan. Invalid or unavailable model output falls back to the deterministic policy result. No model output is executed as a command or allowed to modify files.

## Current integration boundary

Scenario mode validates documented fixture patches. Pull-request mode analyzes committed base/head diffs in an isolated temporary archive, but does not deploy candidates or run production traffic. This is an explicit local limitation, not a production deployment mechanism.
