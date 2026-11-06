# Project record

## Objective

Provide a dependency-free regression gate for LLM features: run a target function over a golden JSONL dataset, score each output, and fail CI when a scorer's mean is below its threshold.

## Scope

- In scope: the public API documented in [README.md](../README.md): strict JSONL loading with size and depth limits, built-in scorers (exact_match, contains, json_field_equals), run_eval, a stable JSON report, check_thresholds, the `eval-mini run` CLI and the opt-in `golden_eval` pytest fixture.
- Out of scope: LLM-as-judge scoring, dashboards, async runs and dataset versioning. Anything that needs runtime dependencies or I/O without an accepted ADR is also out of scope.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | pending measurement |
| Hours (human) | pending measurement |
| Cost (USD) | pending measurement |
