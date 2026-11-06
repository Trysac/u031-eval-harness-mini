# Dependency-free golden-dataset gate with strict score validation

Status: accepted (generated, pending human review)

## Context

Teams need a CI regression check for LLM features without accounts, servers or heavy dependencies. Full platforms such as promptfoo and DeepEval are large. The gate must be deterministic, bounded in memory and safe to run on untrusted dataset files.

## Decision

Use only the standard library. Datasets are JSONL parsed with json.loads, rejecting NaN, Infinity and trailing data, with byte, line, case and nesting limits, the nesting check done iteratively. Equality is JSON-value equality computed iteratively. Scorers must return a finite float in [0, 1] and anything else is an error rather than being clamped. Outputs are not retained, only scores. Reports use sorted keys with cases sorted by id so they are byte-stable. The pytest plugin is opt-in and the only module importing pytest.

## Consequences

The library has zero runtime dependencies and predictable memory use. A buggy scorer fails loudly instead of skewing means, and the same dataset in any line order produces an identical report. Out of scope: LLM-as-judge, dashboards, async runs and dataset versioning. The CLI target import executes trusted code, which is documented. The plugin needs -p or pytest_plugins because the factory owns the package manifest.
