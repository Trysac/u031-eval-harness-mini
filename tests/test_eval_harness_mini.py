"""Tests for the package surface."""

from __future__ import annotations

import logging

import eval_harness_mini
from eval_harness_mini import scorers


def test_public_names() -> None:
    expected = {
        "Case",
        "CaseEvent",
        "CaseResult",
        "EvalError",
        "EvalResult",
        "Scorer",
        "__version__",
        "check_thresholds",
        "load_dataset",
        "run_eval",
        "scorers",
    }
    assert set(eval_harness_mini.__all__) == expected
    assert eval_harness_mini.__version__ == "0.1.0"
    assert eval_harness_mini.scorers is scorers


def test_package_logger_has_null_handler() -> None:
    handlers = logging.getLogger("eval_harness_mini").handlers
    assert any(isinstance(handler, logging.NullHandler) for handler in handlers)


def test_error_carries_code_and_line() -> None:
    error = eval_harness_mini.EvalError("dataset_invalid", "boom", 3)
    assert error.code == "dataset_invalid"
    assert error.line == 3
    assert str(error) == "line 3: boom"
    assert eval_harness_mini.EvalError("threshold_invalid", "x").line is None
