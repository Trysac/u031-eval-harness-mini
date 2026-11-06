"""Tests for run_eval and the result types."""

from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

import pytest

from eval_harness_mini import Case, CaseEvent, EvalError, run_eval
from eval_harness_mini.scorers import contains, exact_match


def make_cases(*items: tuple[str, Any, Any]) -> list[Case]:
    return [Case(case_id, value, expected) for case_id, value, expected in items]


def half(output: Any, expected: Any) -> float:
    return 1.0 if output == expected else 0.5


def test_calls_target_once_per_case_in_file_order() -> None:
    calls: list[Any] = []

    def target(value: Any) -> Any:
        calls.append(value)
        return value

    cases = make_cases(("c", 3, 3), ("a", 1, 1), ("b", 2, 0))
    result = run_eval(target, cases, {"exact": exact_match})
    assert calls == [3, 1, 2]
    assert [case.id for case in result.cases] == ["c", "a", "b"]
    assert result.means == {"exact": pytest.approx(2 / 3)}
    assert result.errors == 0


def test_mean_of_one_and_half_is_three_quarters() -> None:
    cases = make_cases(("a", "x", "x"), ("b", "x", "y"))
    result = run_eval(lambda value: value, cases, {"exact": half})
    assert [case.scores["exact"] for case in result.cases] == [1.0, 0.5]
    assert result.means["exact"] == 0.75


def test_target_error_is_recorded_and_remaining_cases_run() -> None:
    def target(value: Any) -> Any:
        if value == "bad":
            # A target raising ValueError('x' * 300) on one case records error 'ValueError: ' + 'x' * 200
            raise ValueError("x" * 300)
        return value

    cases = make_cases(("a", "ok", "ok"), ("b", "bad", "bad"), ("c", "ok", "ok"))
    result = run_eval(target, cases, {"exact": exact_match, "contains": contains})
    assert result.cases[1].error == "ValueError: " + "x" * 200
    assert result.cases[1].scores == {"exact": 0.0, "contains": 0.0}
    assert result.cases[0].error is None
    assert result.cases[2].scores == {"exact": 1.0, "contains": 1.0}
    assert result.errors == 1
    assert result.means["exact"] == pytest.approx(2 / 3)


@pytest.mark.parametrize(
    "value",
    [1.5, float("nan"), True, 1, -0.1, float("inf"), "0.5", None],
)
def test_scorer_out_of_range(value: Any) -> None:
    def my_scorer(output: Any, expected: Any) -> Any:
        return value

    with pytest.raises(EvalError) as info:
        run_eval(lambda x: x, make_cases(("case-7", 1, 1)), {"my_scorer": my_scorer})
    assert info.value.code == "scorer_out_of_range"
    assert "my_scorer" in str(info.value)
    assert "case-7" in str(info.value)


def test_scorer_exception_propagates() -> None:
    def broken(output: Any, expected: Any) -> float:
        raise RuntimeError("scorer bug")

    with pytest.raises(RuntimeError):
        run_eval(lambda x: x, make_cases(("a", 1, 1)), {"broken": broken})


def test_empty_cases_are_rejected() -> None:
    with pytest.raises(EvalError) as info:
        run_eval(lambda x: x, [], {"exact": exact_match})
    assert info.value.code == "dataset_invalid"


def test_events_carry_no_inputs_or_outputs() -> None:
    def target(value: Any) -> Any:
        if value == "SECRET-INPUT":
            raise ValueError("boom")
        return value

    events: list[CaseEvent] = []
    cases = make_cases(("a", "fine", "fine"), ("b", "SECRET-INPUT", "x"))
    run_eval(target, cases, {"exact": exact_match}, on_event=events.append)
    assert events == [CaseEvent("a", True, None), CaseEvent("b", False, "ValueError")]
    assert "SECRET-INPUT" not in repr(events)
    assert [field.name for field in dataclasses.fields(CaseEvent)] == [
        "case_id",
        "ok",
        "error_type",
    ]


def test_logging_never_contains_inputs(caplog: pytest.LogCaptureFixture) -> None:
    def target(value: Any) -> Any:
        raise ValueError(value)

    caplog.set_level(logging.DEBUG, logger="eval_harness_mini")
    run_eval(target, make_cases(("a", "SECRET-INPUT", "x")), {"exact": exact_match})
    assert "SECRET-INPUT" not in caplog.text


def test_to_json_shape_and_stability() -> None:
    def target(value: Any) -> Any:
        return value

    items = [("b", 2, 2), ("a", 1, 0), ("c", 3, 3)]
    first = run_eval(target, make_cases(*items), {"exact": exact_match})
    second = run_eval(target, make_cases(*reversed(items)), {"exact": exact_match})
    assert first.to_json() == second.to_json()
    report = json.loads(first.to_json())
    assert set(report) == {"cases", "errors", "means"}
    assert set(report["cases"][0]) == {"error", "id", "scores"}
    assert [case["id"] for case in report["cases"]] == ["a", "b", "c"]
    expected = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert first.to_json() == expected


def test_results_are_immutable() -> None:
    result = run_eval(lambda x: x, make_cases(("a", 1, 1)), {"exact": exact_match})
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.errors = 5  # type: ignore[misc]
