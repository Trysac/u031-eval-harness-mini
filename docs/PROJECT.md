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
| Tokens (input / output) | 271406 / 88356 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.6098 |

## Factory run u031 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2716 | 78615 | 0 | 4246 | 0.3962 |
| fix-1 | claude-sonnet-5-5 | no | 4 | 834 | 7009 | 24995 | 0.0284 |
| fix-2 | claude-sonnet-5-5 | no | 8 | 2368 | 11136 | 58336 | 0.0574 |
| fix-3 | claude-sonnet-5-5 | no | 6 | 1374 | 8314 | 42144 | 0.0388 |
| fix-4 | claude-sonnet-5-5 | no | 4 | 261 | 5849 | 24623 | 0.0197 |
| docs | claude-haiku-5-5 | no | 114324 | 4904 | 0 | 0 | 0.0694 |

Total: $0.6098. Prices: Anthropic list prices.
