# eval-harness-mini

[![PyPI version](https://img.shields.io/pypi/v/trysac-eval-harness-mini)](https://pypi.org/project/trysac-eval-harness-mini/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-eval-harness-mini)](LICENSE)
[![CI](https://github.com/Trysac/u031-eval-harness-mini/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u031-eval-harness-mini/actions/workflows/ci.yml)

Minimal evaluation harness: golden JSONL datasets, built-in scorers, CI pass thresholds, a stable JSON report and an opt-in pytest plugin

## Problem

Teams shipping LLM features need a regression check in CI, but full evaluation platforms require accounts, servers or heavy dependencies. Without a gate, prompt or model changes silently reduce quality. This harness runs a target function over a golden JSONL dataset, scores each output and fails CI when a mean score is below its threshold.

## Install

```sh
pip install trysac-eval-harness-mini
# or
uv add trysac-eval-harness-mini
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from pathlib import Path
from eval_harness_mini import check_thresholds, load_dataset, run_eval
from eval_harness_mini.scorers import exact_match

cases = load_dataset(Path("golden.jsonl"))
result = run_eval(lambda text: text.upper(), cases, {"exact": exact_match})
print(result.to_json())
print(check_thresholds(result, {"exact": 0.9}))
```

## Public API

- `Case(id, input, expected, tags=())`: frozen dataclass, one golden example.
- `load_dataset(path, max_bytes=50_000_000, max_line_bytes=1_048_576, max_cases=100_000)`: reads one JSON object per line with `id`, `input` and `expected`. Blank lines are skipped; a UTF-8 BOM and CRLF are accepted. NaN, Infinity and trailing data are rejected. Ids match `[A-Za-z0-9_.:-]{1,128}`. Nesting deeper than 64 levels is rejected.
- `run_eval(target, cases, scorers, on_event=None)`: calls the target once per case in order and returns an `EvalResult` with `cases`, `means` and `errors`. Outputs are not retained.
- `EvalResult.to_json()`: stable report with sorted keys, cases sorted by id and no timestamps.
- `check_thresholds(result, thresholds)`: returns one FAIL line per scorer whose mean is below its threshold. A mean equal to the threshold passes.
- `eval_harness_mini.scorers`: `exact_match`, `contains`, `json_field_equals(field)`. Built-in scorers return 1.0 or 0.0.
- `eval_harness_mini.pytest_plugin`: opt-in `golden_eval` fixture, enabled with `pytest -p eval_harness_mini.pytest_plugin`.
- CLI: `eval-mini run DATASET --target module:function --scorer NAME=THRESHOLD [--report PATH] [--format text|json]`. Exit codes: 0 thresholds met, 1 a threshold failed, 2 usage, dataset or import error. Scorer names are `exact`, `contains` or `json_field:FIELD`.

Errors: `EvalError` carries `code` (`dataset_invalid`, `dataset_too_large`, `scorer_out_of_range`, `threshold_invalid`, `target_not_found`) and `line` (1-based dataset line, or None). Error messages quote at most 200 characters.

Limits: a target that raises `Exception` is recorded as an error with score 0.0 for every scorer; other cases still run. Scorer exceptions propagate unchanged. The default dataset limits are 50 MB, 1 MiB per line and 100,000 cases.

## Why not promptfoo

promptfoo is a larger evaluation platform with its own configuration and runtime. This harness is a dependency-free CI gate over a Python callable.

## Security

See [docs/SECURITY.md](docs/SECURITY.md). The `--target` option imports and runs code: use only trusted code.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
