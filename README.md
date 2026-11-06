# eval-harness-mini

[![PyPI version](https://img.shields.io/pypi/v/trysac-eval-harness-mini)](https://pypi.org/project/trysac-eval-harness-mini/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-eval-harness-mini)](LICENSE)
[![CI](https://github.com/Trysac/u031-eval-harness-mini/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u031-eval-harness-mini/actions/workflows/ci.yml)

Minimal evaluation harness: golden JSONL datasets, built-in scorers, CI pass thresholds, a stable JSON report and an opt-in pytest plugin

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-eval-harness-mini
# or
uv add trysac-eval-harness-mini
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import eval_harness_mini

# normalize() trims surrounding whitespace and lower-cases the text.
print(eval_harness_mini.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    eval_harness_mini.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
