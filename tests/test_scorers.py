"""Tests for the built-in scorers."""

from __future__ import annotations

from typing import Any

import pytest

from eval_harness_mini.scorers import contains, exact_match, json_field_equals


def nest(depth: int) -> Any:
    value: Any = 1
    for _ in range(depth):
        value = [value]
    return value


def test_acceptance_examples() -> None:
    # exact_match('a', 'a') == 1.0, exact_match(1, 1.0) == 1.0, exact_match(True, 1) == 0.0, contains('xay', 'a') == 1.0,
    # json_field_equals('k')('{"k": [1, 2]}', {'k': [1, 2]}) == 1.0 and json_field_equals('k')('not json', {'k': 1}) == 0.0
    assert exact_match("a", "a") == 1.0
    assert exact_match(1, 1.0) == 1.0
    assert exact_match(True, 1) == 0.0
    assert contains("xay", "a") == 1.0
    assert json_field_equals("k")('{"k": [1, 2]}', {"k": [1, 2]}) == 1.0
    assert json_field_equals("k")("not json", {"k": 1}) == 0.0


@pytest.mark.parametrize(
    ("output", "expected", "score"),
    [
        ("a", "a", 1.0),
        ("a", "b", 0.0),
        (1, 1.0, 1.0),
        (1.0, 1, 1.0),
        (True, 1, 0.0),
        (1, True, 0.0),
        (True, True, 1.0),
        (False, 0, 0.0),
        (None, None, 1.0),
        (None, 0, 0.0),
        (0, None, 0.0),
        ("1", 1, 0.0),
        ([1, 2], [1, 2], 1.0),
        ([1, 2], [2, 1], 0.0),
        ([1, 2], [1.0, 2.0], 1.0),
        ([True], [1], 0.0),
        ([1], [1, 2], 0.0),
        ({"a": 1}, {"a": 1.0}, 1.0),
        ({"a": 1}, {"b": 1}, 0.0),
        ({"a": 1}, {"a": 1, "b": 2}, 0.0),
        ({"a": [{"b": None}]}, {"a": [{"b": None}]}, 1.0),
        ({"a": 1}, [1], 0.0),
        (float("nan"), float("nan"), 0.0),
        ((1, 2), [1, 2], 1.0),
    ],
)
def test_exact_match_table(output: Any, expected: Any, score: float) -> None:
    assert exact_match(output, expected) == score


def test_exact_match_handles_very_deep_values() -> None:
    assert exact_match(nest(5000), nest(5000)) == 1.0
    assert exact_match(nest(5000), nest(4999)) == 0.0


@pytest.mark.parametrize(
    ("output", "expected", "score"),
    [
        ("xay", "a", 1.0),
        ("xyz", "a", 0.0),
        (123, 2, 1.0),
        (None, "None", 1.0),
        ("abc", "abcd", 0.0),
        ("", "", 1.0),
    ],
)
def test_contains_table(output: Any, expected: Any, score: float) -> None:
    assert contains(output, expected) == score


@pytest.mark.parametrize(
    ("output", "expected", "score"),
    [
        ('{"k": 1}', {"k": 1.0}, 1.0),
        ('{"k": 1}', {"k": 2}, 0.0),
        ('{"k": true}', {"k": 1}, 0.0),
        ('{"other": 1}', {"k": 1}, 0.0),
        ('{"k": 1}', {"other": 1}, 0.0),
        ('{"k": 1}', "not a dict", 0.0),
        ("[1]", {"k": 1}, 0.0),
        ("", {"k": 1}, 0.0),
        ({"k": [1, 2]}, {"k": [1, 2]}, 1.0),
        ([1], {"k": 1}, 0.0),
        (None, {"k": 1}, 0.0),
    ],
)
def test_json_field_equals_table(output: Any, expected: Any, score: float) -> None:
    assert json_field_equals("k")(output, expected) == score


def test_json_field_equals_survives_hostile_json() -> None:
    hostile = "[" * 200_000 + "]" * 200_000
    assert json_field_equals("k")(hostile, {"k": 1}) == 0.0
