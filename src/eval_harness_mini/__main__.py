"""Command line interface: ``eval-mini run DATASET --target module:function --scorer N=T``.

The ``--target`` option imports and runs code: only use trusted code, like pytest does.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .dataset import load_dataset
from .errors import EvalError, quote
from .runner import run_eval
from .scorers import Scorer, contains, exact_match, json_field_equals
from .thresholds import check_thresholds, format_text, validate_thresholds

_BUILTIN: dict[str, Scorer] = {"exact": exact_match, "contains": contains}
_JSON_PREFIX = "json_field:"


class _UsageError(Exception):
    """Raised for malformed command line values."""


def _scorer_for(name: str) -> Scorer:
    if name in _BUILTIN:
        return _BUILTIN[name]
    if name.startswith(_JSON_PREFIX) and len(name) > len(_JSON_PREFIX):
        return json_field_equals(name[len(_JSON_PREFIX) :])
    raise _UsageError(f"unknown scorer {quote(name)!r}; use exact, contains or json_field:FIELD")


def _build_scorers(specs: list[str]) -> tuple[dict[str, Scorer], dict[str, float]]:
    scorers: dict[str, Scorer] = {}
    thresholds: dict[str, float] = {}
    for spec in specs:
        name, separator, raw = spec.rpartition("=")
        if not separator or not name:
            raise _UsageError(f"invalid --scorer {quote(spec)!r}, expected NAME=THRESHOLD")
        if name in scorers:
            raise _UsageError(f"scorer {quote(name)!r} given more than once")
        try:
            threshold = float(raw)
        except ValueError as exc:
            raise _UsageError(f"threshold {quote(raw)!r} is not a number") from exc
        scorers[name] = _scorer_for(name)
        thresholds[name] = threshold
    return scorers, thresholds


def _resolve_target(spec: str) -> Callable[[Any], Any]:
    module_name, separator, attribute = spec.partition(":")
    if not separator or not module_name or not attribute:
        raise EvalError("target_not_found", f"target must be module:function, got {quote(spec)!r}")
    try:
        target = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as exc:
        message = f"cannot import {quote(spec)!r}: {type(exc).__name__}"
        raise EvalError("target_not_found", message) from exc
    if not callable(target):
        raise EvalError("target_not_found", f"{quote(spec)!r} is not callable")
    resolved: Callable[[Any], Any] = target
    return resolved


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="eval-mini", description="Golden dataset gate.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run a target over a dataset and check thresholds")
    run.add_argument("dataset", help="path to the JSONL dataset")
    run.add_argument("--target", required=True, help="module:function (trusted code)")
    run.add_argument(
        "--scorer",
        nargs="+",
        action="extend",
        required=True,
        metavar="NAME=THRESHOLD",
        help="exact, contains or json_field:FIELD with a minimum mean in [0, 1]",
    )
    run.add_argument("--report", help="write the stable JSON report to this path")
    run.add_argument("--format", choices=["text", "json"], default="text", help="stdout format")
    return parser


def _run(args: argparse.Namespace) -> int:
    scorers, thresholds = _build_scorers(args.scorer)
    validate_thresholds(scorers, thresholds)
    cases = load_dataset(Path(args.dataset))
    target = _resolve_target(args.target)
    result = run_eval(target, cases, scorers)
    if args.report:
        Path(args.report).write_bytes(result.to_json().encode("utf-8"))
    if args.format == "json":
        sys.stdout.write(result.to_json())
    else:
        print(format_text(result, thresholds))
    return 1 if check_thresholds(result, thresholds) else 0


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the exit code.

    Returns:
        0 when every threshold is met, 1 when a threshold failed, 2 for usage, dataset,
        scorer, threshold or import errors.
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        return _run(args)
    except (EvalError, _UsageError, OSError) as exc:
        code = f"[{exc.code}] " if isinstance(exc, EvalError) else ""
        print(f"error: {code}{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
