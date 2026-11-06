"""Minimal evaluation harness for golden JSONL datasets with CI pass thresholds."""

from __future__ import annotations

import logging

from . import scorers
from .dataset import Case, load_dataset
from .errors import EvalError
from .runner import CaseEvent, CaseResult, EvalResult, run_eval
from .scorers import Scorer
from .thresholds import check_thresholds

__all__ = [
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
]

__version__ = "0.1.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
