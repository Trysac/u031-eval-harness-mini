"""Built-in scorers. Each scorer takes ``(output, expected)`` and returns 1.0 or 0.0."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

Scorer = Callable[[Any, Any], float]


def _step(left: Any, right: Any, stack: list[tuple[Any, Any]]) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, int | float) and isinstance(right, int | float):
        return bool(left == right)
    if left is None or right is None:
        return left is right
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if isinstance(left, list | tuple) and isinstance(right, list | tuple):
        if len(left) != len(right):
            return False
        stack.extend(zip(left, right, strict=True))
        return True
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return False
        stack.extend((left[key], right[key]) for key in left)
        return True
    return False


def json_equal(left: Any, right: Any) -> bool:
    """Compare two decoded JSON values (iteratively, so depth cannot overflow the stack).

    Numbers compare numerically (``1 == 1.0``), booleans only equal booleans, ``None`` only
    equals ``None``, lists compare by order and dicts by key set and values.
    """
    stack: list[tuple[Any, Any]] = [(left, right)]
    while stack:
        current_left, current_right = stack.pop()
        if not _step(current_left, current_right, stack):
            return False
    return True


def exact_match(output: Any, expected: Any) -> float:
    """Return 1.0 when ``output`` equals ``expected`` as a JSON value, else 0.0."""
    return 1.0 if json_equal(output, expected) else 0.0


def contains(output: Any, expected: Any) -> float:
    """Return 1.0 when ``str(expected)`` is a substring of ``str(output)``, else 0.0."""
    return 1.0 if str(expected) in str(output) else 0.0


def json_field_equals(field: str) -> Scorer:
    """Build a scorer comparing ``output[field]`` with ``expected[field]``.

    A ``str`` output is parsed with ``json.loads``. Unparseable output, a non-object output or
    expected value, or a missing field scores 0.0.
    """

    def scorer(output: Any, expected: Any) -> float:
        data = output
        if isinstance(output, str):
            try:
                data = json.loads(output)
            except (ValueError, RecursionError):
                return 0.0
        if not isinstance(data, dict) or not isinstance(expected, dict):
            return 0.0
        if field not in data or field not in expected:
            return 0.0
        return 1.0 if json_equal(data[field], expected[field]) else 0.0

    return scorer
