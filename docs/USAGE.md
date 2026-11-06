# Usage

## Dataset

One JSON object per line with `id` (`^[A-Za-z0-9_.:-]{1,128}$`), `input` and `expected`; an optional
`tags` list of strings is allowed. Blank lines, a UTF-8 BOM and CRLF are accepted. NaN, Infinity,
trailing data and nesting deeper than 64 levels are rejected with `EvalError` code `dataset_invalid`
and the 1-based `line`. Limits: `max_bytes`, `max_line_bytes` and `max_cases` raise
`dataset_too_large`.

## Library

```python
from pathlib import Path
from eval_harness_mini import check_thresholds, load_dataset, run_eval
from eval_harness_mini.scorers import exact_match

cases = load_dataset(Path("golden.jsonl"))
result = run_eval(lambda text: text.upper(), cases, {"exact": exact_match})
print(check_thresholds(result, {"exact": 0.9}))
```

Scorers must return a finite `float` in [0, 1]; anything else raises `scorer_out_of_range`. A target
that raises `Exception` is recorded as `"Type: message"` (message cut to 200 characters) with score
0.0 for every scorer.

## CLI

```
python -m eval_harness_mini run DATASET --target module:function --scorer exact=0.9 [--report PATH] [--format text|json]
```

Scorer names are `exact`, `contains` and `json_field:FIELD`. Exit codes: 0 thresholds met, 1 a
threshold failed, 2 usage, dataset, threshold or import error. `--target` imports and runs code:
use trusted code only, like pytest.

## pytest plugin

Enable it with `pytest -p eval_harness_mini.pytest_plugin` or `pytest_plugins =
["eval_harness_mini.pytest_plugin"]` in `conftest.py`, then call
`golden_eval(target, path, scorers, thresholds)`. A miss fails the test and lists at most 20 failing
case ids.
