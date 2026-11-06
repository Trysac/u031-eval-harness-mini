# Testing

## Running

```sh
uv run pytest --cov=eval_harness_mini   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Policy

- Branch coverage of `src/eval_harness_mini` must stay at or above 80 %; the gate fails below it.
- Tests exercise the public API (`import eval_harness_mini`) and assert observable effects: return values, raised exceptions and their messages.
- Each bug fix starts with a failing test that reproduces it.
- Tests are deterministic: no network, no wall clock, no dependence on test order.

## Layout

`tests/test_<module>.py` mirrors each public module. Shared fixtures go in `tests/conftest.py`. The test files present in the repository are `tests/conftest.py` (shared pytest configuration that enables the pytest plugin) and `tests/test_cli.py` (CLI tests that run `main` with a temporary dataset and check exit codes and output).
