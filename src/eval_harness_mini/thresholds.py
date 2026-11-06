"""Pass/fail thresholds over the mean score of each scorer."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

from .errors import EvalError, quote
from .runner import EvalResult


def validate_thresholds(names: Iterable[str], thresholds: Mapping[str, float]) -> None:
    """Raise ``threshold_invalid`` for an unknown scorer or a value outside [0, 1]."""
    known = set(names)
    for name, value in thresholds.items():
        if name not in known:
            raise EvalError("threshold_invalid", f"unknown scorer {quote(name)!r}")
        is_number = isinstance(value, int | float) and not isinstance(value, bool)
        if not is_number or not math.isfinite(value) or not 0.0 <= value <= 1.0:
            message = f"threshold for {quote(name)!r} must be a number in [0, 1]"
            raise EvalError("threshold_invalid", message)


def _outcomes(result: EvalResult, thresholds: Mapping[str, float]) -> list[tuple[str, float, float]]:
    validate_thresholds(result.means, thresholds)
    return [(name, result.means[name], float(value)) for name, value in thresholds.items()]


def _line(name: str, mean: float, threshold: float) -> str:
    verdict = "PASS" if mean >= threshold else "FAIL"
    return f"{name} mean={mean:.4f} threshold={threshold:.4f} {verdict}"


def _failed(outcomes: list[tuple[str, float, float]]) -> set[str]:
    return {name for name, mean, threshold in outcomes if mean < threshold}


def _failing_ids(result: EvalResult, scorers: set[str]) -> list[str]:
    return [
        case.id
        for case in result.cases
        if case.error is not None or any(case.scores.get(name, 0.0) < 1.0 for name in scorers)
    ]


def check_thresholds(result: EvalResult, thresholds: Mapping[str, float]) -> list[str]:
    """Return one ``FAIL`` line per scorer whose mean is below its threshold.

    A mean equal to the threshold passes.

    Raises:
        EvalError: ``threshold_invalid`` for an unknown scorer or a threshold outside [0, 1].
    """
    return [
        _line(name, mean, threshold)
        for name, mean, threshold in _outcomes(result, thresholds)
        if mean < threshold
    ]


def failing_case_ids(result: EvalResult, thresholds: Mapping[str, float]) -> list[str]:
    """Return ids (in file order) of cases that explain a failed threshold.

    A case is listed when its target raised or it scored below 1.0 on a scorer whose mean
    missed its threshold. Nothing is listed when every threshold is met.
    """
    failed = _failed(_outcomes(result, thresholds))
    return _failing_ids(result, failed) if failed else []


def format_text(result: EvalResult, thresholds: Mapping[str, float], max_ids: int = 20) -> str:
    """Render one PASS/FAIL line per scorer, then at most ``max_ids`` failing case ids."""
    outcomes = _outcomes(result, thresholds)
    lines = [_line(name, mean, threshold) for name, mean, threshold in outcomes]
    failed = _failed(outcomes)
    if failed:
        ids = _failing_ids(result, failed)
        lines.append("failing cases:")
        lines.extend(f"  {case_id}" for case_id in ids[:max_ids])
        if len(ids) > max_ids:
            lines.append(f"  ... and {len(ids) - max_ids} more")
    return "\n".join(lines)
