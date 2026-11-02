# Why the analyst is not authoritative

ChangeLens separates facts from explanation.

The deterministic tools produce the factual evidence: command exit codes, captured output, security findings, API findings, and measured performance values. The policy engine evaluates those facts using explicit thresholds. Its `APPROVE`, `REVIEW`, or `BLOCK` result is authoritative.

The analyst receives a bounded, sanitized copy of the evidence and the policy result. It may summarize the change, prioritize findings, cite evidence fields, and propose a rollback plan. It may not execute commands, modify files, deploy anything, or replace measured values.

Analyst output is validated before it enters the report. Unsupported evidence references cause the output to be rejected and replaced with a deterministic fallback. A model decision cannot weaken a policy decision: a policy `BLOCK` remains `BLOCK`, and an unavailable model preserves the policy result.

The default provider is deterministic mock mode. An external OpenAI-compatible endpoint is only used when `CHANGELENS_MODEL_ENDPOINT` is explicitly set. Captured output is truncated and common credential patterns are redacted before model input. API keys are read only for the outbound request and are not recorded in reports.
