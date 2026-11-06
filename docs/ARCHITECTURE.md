# Architecture

## Purpose

`trysac-eval-harness-mini` is a small, dependency-free Python library for a CI regression gate over LLM features: it runs a target callable over a golden JSONL dataset, scores the outputs and checks mean thresholds.

## Shape

```text
caller code / CLI / pytest fixture --> eval_harness_mini (public API in __init__.py)
                    |
                    +-- dataset.py   load and validate JSONL
                    +-- runner.py    call target, score, aggregate, to_json
                    +-- scorers.py   exact_match, contains, json_field_equals
                    +-- thresholds.py  check and format thresholds
                    +-- errors.py    EvalError with stable codes
```

- **Public API**: the names listed in `__all__` of `src/eval_harness_mini/__init__.py`: `Case`, `CaseEvent`, `CaseResult`, `EvalError`, `EvalResult`, `Scorer`, `check_thresholds`, `load_dataset`, `run_eval`, `scorers`, `__version__`.
- **Entry points**: `__main__.py` provides the `eval-mini run` CLI and `main(argv)`. `pytest_plugin.py` provides the opt-in `golden_eval` fixture, imported only when enabled.
- **Errors**: invalid input raises `EvalError` with a stable `code` and an optional dataset `line`. The library functions do not print or exit; only the CLI writes to stdout or stderr.
- **Logging**: the package logger has a NullHandler; the runner logs target failures at debug level.
- **Side effects**: only reading the dataset (`load_dataset`) and writing the optional report (CLI). Anything else that needs I/O must go in its own module behind a small interface and be recorded in an ADR.

## Quality contract

`scripts/check.py` is the single definition of the gates; `fabrica.json` tells the factory and CI how to run it. See [TESTING.md](TESTING.md).

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
