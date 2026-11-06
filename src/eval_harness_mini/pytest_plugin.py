"""Opt-in pytest plugin providing the ``golden_eval`` fixture.

Enable it with ``pytest -p eval_harness_mini.pytest_plugin`` or
``pytest_plugins = ["eval_harness_mini.pytest_plugin"]`` in ``conftest.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from .dataset import load_dataset
from .runner import EvalResult, run_eval
from .scorers import Scorer
from .thresholds import check_thresholds, format_text, validate_thresholds

GoldenEval = Callable[
    [Callable[[Any], Any], str | Path, Mapping[str, Scorer], Mapping[str, float]],
    EvalResult,
]


@pytest.fixture
def golden_eval() -> GoldenEval:
    """Return a callable ``(target, path, scorers, thresholds)`` that fails the test on a miss.

    The failure message lists the missed thresholds and at most 20 failing case ids.
    """

    def run(
        target: Callable[[Any], Any],
        path: str | Path,
        scorers: Mapping[str, Scorer],
        thresholds: Mapping[str, float],
    ) -> EvalResult:
        validate_thresholds(scorers, thresholds)
        result = run_eval(target, load_dataset(Path(path)), scorers)
        if check_thresholds(result, thresholds):
            pytest.fail(format_text(result, thresholds), pytrace=False)
        return result

    return run
