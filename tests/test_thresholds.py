"""Tests for threshold checks and text formatting."""

from __future__ import annotations

from typing import Any

import pytest

from eval_harness_mini import Case, EvalError, EvalResult, check_thresholds, run_eval
from eval_harness_mini.scorers import exact_match
from eval_harness_mini.thresholds import failing_case_ids, format_text, validate_thresholds


def half(output: Any, expected: Any) -> float:
    return 1.0 if output == expected else 0.5


def half_result() -> EvalResult:
    cases = [Case("a", "x", "x"), Case("b", "x", "y")]
    return run_eval(lambda value: value, cases, {"exact": half})


def failing_result() -> EvalResult:
    cases = [Case(f"c{i:02d}", i, 1) for i in range(30)]
    return run_eval(lambda value: 1 if value >= 25 else 0, cases, {"exact": exact_match})


def test_mean_equal_to_threshold_passes() -> None:
    result = half_result()
    assert result.means["exact"] == 0.75
    assert check_thresholds(result, {"exact": 0.75}) == []


def test_mean_below_threshold_fails() -> None:
    failures = check_thresholds(half_result(), {"exact": 0.7501})
    assert failures == ["exact mean=0.7500 threshold=0.7501 FAIL"]


def test_integer_thresholds_and_empty_thresholds() -> None:
    assert check_thresholds(half_result(), {"exact": 0}) == []
    failures = check_thresholds(half_result(), {"exact": 1})
    assert failures == ["exact mean=0.7500 threshold=1.0000 FAIL"]
    assert check_thresholds(half_result(), {}) == []


@pytest.mark.parametrize(
    "thresholds",
    [
        {"nope": 0.5},
        {"exact": 1.5},
        {"exact": -0.1},
        {"exact": float("nan")},
        {"exact": float("inf")},
        {"exact": True},
        {"exact": "0.5"},
        {"exact": None},
    ],
)
def test_invalid_thresholds(thresholds: Any) -> None:
    with pytest.raises(EvalError) as info:
        check_thresholds(half_result(), thresholds)
    assert info.value.code == "threshold_invalid"


def test_validate_thresholds_accepts_known_names() -> None:
    validate_thresholds(["exact", "contains"], {"exact": 0.5, "contains": 1.0})
    with pytest.raises(EvalError):
        validate_thresholds(["exact"], {"contains": 0.5})


def test_format_text_lists_pass_and_fail_lines() -> None:
    assert format_text(half_result(), {"exact": 0.75}) == "exact mean=0.7500 threshold=0.7500 PASS"
    lines = format_text(half_result(), {"exact": 0.7501}).splitlines()
    assert lines == [
        "exact mean=0.7500 threshold=0.7501 FAIL",
        "failing cases:",
        "  b",
    ]


def test_format_text_caps_failing_ids_at_20() -> None:
    lines = format_text(failing_result(), {"exact": 1.0}).splitlines()
    assert lines[0] == "exact mean=0.1667 threshold=1.0000 FAIL"
    assert lines[1] == "failing cases:"
    assert lines[2:22] == [f"  c{i:02d}" for i in range(20)]
    assert lines[22] == "  ... and 5 more"
    assert len(lines) == 23


def test_format_text_custom_cap_and_exact_cap() -> None:
    lines = format_text(failing_result(), {"exact": 1.0}, max_ids=2).splitlines()
    assert lines[2:] == ["  c00", "  c01", "  ... and 23 more"]
    assert "more" not in format_text(failing_result(), {"exact": 1.0}, max_ids=25)


def test_failing_case_ids() -> None:
    assert failing_case_ids(half_result(), {"exact": 1.0}) == ["b"]
    assert failing_case_ids(half_result(), {"exact": 0.5}) == []

    def target(value: Any) -> Any:
        if value == "boom":
            raise ValueError("x")
        return value

    cases = [Case("a", "ok", "ok"), Case("b", "boom", "boom")]
    result = run_eval(target, cases, {"exact": exact_match})
    assert failing_case_ids(result, {"exact": 1.0}) == ["b"]
    assert failing_case_ids(result, {"exact": 0.5}) == []
