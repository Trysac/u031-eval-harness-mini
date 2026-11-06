"""Typed errors raised by eval_harness_mini."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal[
    "dataset_invalid",
    "dataset_too_large",
    "scorer_out_of_range",
    "threshold_invalid",
    "target_not_found",
]

MAX_QUOTE = 200


def quote(value: object) -> str:
    """Return ``value`` as text truncated to at most 200 characters."""
    return str(value)[:MAX_QUOTE]


class EvalError(Exception):
    """Base error of the library.

    Attributes:
        code: Stable machine-readable error code.
        line: 1-based dataset line the error refers to, or ``None``.
    """

    def __init__(self, code: ErrorCode, message: str, line: int | None = None) -> None:
        prefix = f"line {line}: " if line is not None else ""
        super().__init__(prefix + message)
        self.code: ErrorCode = code
        self.line: int | None = line
