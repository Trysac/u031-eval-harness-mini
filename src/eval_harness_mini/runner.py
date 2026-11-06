"""Run a target over golden cases and aggregate the scores."""

from __future__ import annotations

import json
import logging
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .dataset import Case
from .errors import EvalError, quote
from .scorers import Scorer

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass(frozen=True)
class CaseEvent:
    """Progress event for one case. It never carries inputs or outputs."""

    case_id: str
    ok: bool
    error_type: str | None


@dataclass(frozen=True)
class CaseResult:
    """Scores of one case; ``error`` is set when the target raised."""

    id: str
    scores: Mapping[str, float]
    error: str | None


@dataclass(frozen=True)
class EvalResult:
    """Outcome of :func:`run_eval`. Outputs are not retained."""

    cases: tuple[CaseResult, ...]
    means: Mapping[str, float]
    errors: int

    def to_json(self) -> str:
        """Return the stable report: sorted keys, cases sorted by id, no timestamps."""
        report = {
            "cases": [
                {"error": case.error, "id": case.id, "scores": dict(case.scores)}
                for case in sorted(self.cases, key=lambda item: item.id)
            ],
            "errors": self.errors,
            "means": dict(self.means),
        }
        return json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _checked_score(value: object, scorer: str, case_id: str) -> float:
    if isinstance(value, float) and math.isfinite(value) and 0.0 <= value <= 1.0:
        return value
    detail = f"{value!r}" if isinstance(value, float) else type(value).__name__
    raise EvalError(
        "scorer_out_of_range",
        f"scorer {quote(scorer)!r} returned an invalid score ({detail}) for case {case_id!r}: "
        "expected a finite float in [0, 1]",
    )


def run_eval(
    target: Callable[[Any], Any],
    cases: Sequence[Case],
    scorers: Mapping[str, Scorer],
    on_event: Callable[[CaseEvent], None] | None = None,
) -> EvalResult:
    """Call ``target`` once per case in order and score every output.

    A target that raises ``Exception`` records ``"Type: message"`` (message cut to 200
    characters) with score 0.0 for every scorer; the remaining cases still run.

    Raises:
        EvalError: ``scorer_out_of_range`` when a scorer does not return a finite ``float`` in
            [0, 1], or ``dataset_invalid`` when ``cases`` is empty.
    """
    if not cases:
        raise EvalError("dataset_invalid", "no cases to evaluate")
    results: list[CaseResult] = []
    for case in cases:
        error: str | None = None
        error_type: str | None = None
        scores: dict[str, float] = {}
        try:
            output = target(case.input)
        except Exception as exc:
            error_type = type(exc).__name__
            error = f"{error_type}: {quote(exc)}"
            scores = dict.fromkeys(scorers, 0.0)
            logger.debug("target failed for case %s with %s", case.id, error_type)
        else:
            for name, scorer in scorers.items():
                scores[name] = _checked_score(scorer(output, case.expected), name, case.id)
        results.append(CaseResult(case.id, scores, error))
        if on_event is not None:
            on_event(CaseEvent(case.id, error is None, error_type))
    means = {
        name: math.fsum(result.scores[name] for result in results) / len(results)
        for name in scorers
    }
    failures = sum(1 for result in results if result.error is not None)
    return EvalResult(tuple(results), means, failures)
