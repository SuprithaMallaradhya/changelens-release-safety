# Phase 2 scenarios

Each scenario is a patch or fixture that is applied to a clean Phase 1 checkout. The patches intentionally live outside the application source so the baseline behavior remains unchanged on the default checkout.

From the repository root, apply one code scenario with:

```bash
git apply fixtures/scenarios/<scenario-name>/change.patch
```

Run the validation command in `manifest.json`, capture the evidence, then return to a clean checkout before applying another scenario. Do not apply multiple scenario patches at once.

The infrastructure/security scenario is a standalone candidate manifest and does not change the local Compose deployment.

The manifest is the source of truth for changed files, setup, expected outcomes, evidence, and commands.
