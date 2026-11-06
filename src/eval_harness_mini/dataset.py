"""Golden JSONL dataset loading with strict size and depth limits."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from .errors import EvalError, quote

MAX_DEPTH = 64
_BOM = b"\xef\xbb\xbf"
_ID_RE = re.compile(r"[A-Za-z0-9_.:-]{1,128}")


@dataclass(frozen=True)
class Case:
    """One golden example: ``input`` goes to the target, ``expected`` to the scorers."""

    id: str
    input: Any
    expected: Any
    tags: tuple[str, ...] = ()


def _reject_constant(name: str) -> NoReturn:
    raise ValueError(f"non-finite constant {name} is not allowed")


def _parse_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("non-finite number is not allowed")
    return value


def _check_depth(obj: Any, line: int) -> None:
    stack: list[tuple[Any, int]] = [(obj, 1)]
    while stack:
        value, depth = stack.pop()
        if depth > MAX_DEPTH:
            raise EvalError("dataset_invalid", f"nesting deeper than {MAX_DEPTH} levels", line)
        children = value.values() if isinstance(value, dict) else value
        stack.extend((child, depth + 1) for child in children if isinstance(child, dict | list))


def _parse_line(text: str, line: int, seen: set[str]) -> Case:
    try:
        obj = json.loads(text, parse_constant=_reject_constant, parse_float=_parse_float)
    except (ValueError, RecursionError) as exc:
        raise EvalError("dataset_invalid", f"invalid JSON: {quote(exc)}", line) from exc
    if not isinstance(obj, dict):
        raise EvalError("dataset_invalid", "each line must be a JSON object", line)
    _check_depth(obj, line)
    for key in ("id", "input", "expected"):
        if key not in obj:
            raise EvalError("dataset_invalid", f"missing required field {key!r}", line)
    case_id = obj["id"]
    if not isinstance(case_id, str) or _ID_RE.fullmatch(case_id) is None:
        raise EvalError("dataset_invalid", f"invalid id {quote(case_id)!r}", line)
    if case_id in seen:
        raise EvalError("dataset_invalid", f"duplicate id {case_id!r}", line)
    tags = obj.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise EvalError("dataset_invalid", "tags must be a list of strings", line)
    seen.add(case_id)
    return Case(case_id, obj["input"], obj["expected"], tuple(tags))


def load_dataset(
    path: Path | str,
    max_bytes: int = 50_000_000,
    max_line_bytes: int = 1_048_576,
    max_cases: int = 100_000,
) -> list[Case]:
    """Load a JSONL dataset: one object per line with ``id``, ``input`` and ``expected``.

    Blank lines are skipped; a UTF-8 BOM and CRLF line endings are accepted. NaN, Infinity and
    trailing data after the object are rejected.

    Raises:
        EvalError: ``dataset_invalid`` (with the 1-based ``line``) for malformed content, or
            ``dataset_too_large`` when a size limit is exceeded.
    """
    try:
        with Path(path).open("rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as exc:
        raise EvalError("dataset_invalid", f"cannot read dataset: {type(exc).__name__}") from exc
    if len(data) > max_bytes:
        raise EvalError("dataset_too_large", f"dataset is larger than {max_bytes} bytes")
    data = data.removeprefix(_BOM)
    cases: list[Case] = []
    seen: set[str] = set()
    for number, raw in enumerate(data.split(b"\n"), start=1):
        line_bytes = raw.removesuffix(b"\r")
        if len(line_bytes) > max_line_bytes:
            raise EvalError("dataset_too_large", f"line exceeds {max_line_bytes} bytes", number)
        if not line_bytes.strip():
            continue
        if len(cases) >= max_cases:
            raise EvalError("dataset_too_large", f"more than {max_cases} cases", number)
        try:
            text = line_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvalError("dataset_invalid", "line is not valid UTF-8", number) from exc
        cases.append(_parse_line(text, number, seen))
    if not cases:
        raise EvalError("dataset_invalid", "dataset contains no cases")
    return cases
