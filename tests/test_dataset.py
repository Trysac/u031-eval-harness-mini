"""Tests for load_dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval_harness_mini import Case, EvalError, load_dataset

GOOD = '{"id": "a", "input": 1, "expected": 1}'


def row(**fields: object) -> str:
    return json.dumps(fields)


def write(tmp_path: Path, data: bytes | str) -> Path:
    path = tmp_path / "dataset.jsonl"
    path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
    return path


def nested(depth: int) -> str:
    return "[" * depth + "]" * depth


def nested_dict(depth: int) -> str:
    return '{"k": ' * depth + "1" + "}" * depth


def test_loads_cases_in_file_order(tmp_path: Path) -> None:
    lines = [
        row(id="a", input={"q": 1}, expected="x"),
        row(id="b.1:x-y_z", input=[1], expected=None, tags=["t1", "t2"]),
    ]
    cases = load_dataset(write(tmp_path, "\n".join(lines) + "\n"))
    assert cases == [
        Case("a", {"q": 1}, "x"),
        Case("b.1:x-y_z", [1], None, ("t1", "t2")),
    ]


def test_accepts_str_path(tmp_path: Path) -> None:
    path = write(tmp_path, GOOD)
    assert load_dataset(str(path))[0].id == "a"


def test_skips_blank_lines_and_accepts_bom_and_crlf(tmp_path: Path) -> None:
    data = b"\xef\xbb\xbf" + GOOD.encode() + b"\r\n\r\n   \r\n"
    data += row(id="b", input=2, expected=2).encode() + b"\r\n"
    cases = load_dataset(write(tmp_path, data))
    assert [case.id for case in cases] == ["a", "b"]


INVALID = [
    ("not json\n", 1),
    (GOOD + "\n{bad\n", 2),
    (row(id="a", input=1), 1),
    (GOOD + "\n\n" + row(id="b", input=1) + "\n", 3),
    (GOOD + "\n" + GOOD, 2),
    ("[1]", 1),
    (GOOD + "\n[1]\n", 2),
    ('{"id": "a", "input": 1, "expected": 1}{}', 1),
    (GOOD + " " + GOOD, 1),
    ('{"id": "a", "input": NaN, "expected": 1}', 1),
    ('{"id": "a", "input": 1, "expected": Infinity}', 1),
    ('{"id": "a", "input": [-Infinity], "expected": 1}', 1),
    ('{"id": "a", "input": 1e999, "expected": 1}', 1),
    ('"just a string"', 1),
    ('{"id": "a", "input": 1, "expected": 1,}', 1),
    (GOOD[:-1], 1),
    (row(id="bad id", input=1, expected=1), 1),
    (row(id=5, input=1, expected=1), 1),
    (row(id="", input=1, expected=1), 1),
    (row(id="x" * 129, input=1, expected=1), 1),
    (row(id="a\n", input=1, expected=1), 1),
    (row(id="caf\u00e9", input=1, expected=1), 1),
    (row(id="a", input=1, expected=1, tags="t"), 1),
    (row(id="a", input=1, expected=1, tags=[1]), 1),
    (row(input=1, expected=1), 1),
]


@pytest.mark.parametrize(("text", "line"), INVALID)
def test_invalid_lines_report_their_line(tmp_path: Path, text: str, line: int) -> None:
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, text))
    assert info.value.code == "dataset_invalid"
    assert info.value.line == line


def test_id_of_128_characters_is_accepted(tmp_path: Path) -> None:
    cases = load_dataset(write(tmp_path, row(id="x" * 128, input=1, expected=1)))
    assert len(cases[0].id) == 128


def test_invalid_utf8_is_dataset_invalid(tmp_path: Path) -> None:
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, GOOD.encode() + b"\n\xff\xfe\n"))
    assert info.value.code == "dataset_invalid"
    assert info.value.line == 2


def test_messages_quote_at_most_200_characters(tmp_path: Path) -> None:
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, row(id="!" * 5000, input=1, expected=1)))
    assert len(str(info.value)) < 300


@pytest.mark.parametrize("text", ["", "\n\n   \r\n"])
def test_empty_dataset_is_invalid(tmp_path: Path, text: str) -> None:
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, text))
    assert info.value.code == "dataset_invalid"
    assert info.value.line is None


def test_unreadable_path_is_invalid(tmp_path: Path) -> None:
    for path in (tmp_path / "missing.jsonl", tmp_path):
        with pytest.raises(EvalError) as info:
            load_dataset(path)
        assert info.value.code == "dataset_invalid"


def test_max_bytes_limit(tmp_path: Path) -> None:
    size = len(GOOD.encode())
    assert len(load_dataset(write(tmp_path, GOOD), max_bytes=size)) == 1
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, b"x" * 11), max_bytes=10)
    assert info.value.code == "dataset_too_large"
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, GOOD), max_bytes=size - 1)
    assert info.value.code == "dataset_too_large"


def test_max_line_bytes_limit(tmp_path: Path) -> None:
    base = len(row(id="a", input="", expected=1))
    exact = row(id="a", input="x" * (100 - base), expected=1)
    assert len(exact) == 100
    assert len(load_dataset(write(tmp_path, exact + "\r\n"), max_line_bytes=100)) == 1
    too_long = row(id="a", input="x" * (101 - base), expected=1)
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, GOOD + "\n" + too_long), max_line_bytes=100)
    assert info.value.code == "dataset_too_large"
    assert info.value.line == 2
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, b"x" * 101), max_line_bytes=100)
    assert info.value.code == "dataset_too_large"


def test_max_cases_limit(tmp_path: Path) -> None:
    lines = [row(id=f"c{i}", input=i, expected=i) for i in range(3)]
    path = write(tmp_path, "\n".join(lines))
    assert len(load_dataset(path, max_cases=3)) == 3
    with pytest.raises(EvalError) as info:
        load_dataset(path, max_cases=2)
    assert info.value.code == "dataset_too_large"
    assert info.value.line == 3


def test_depth_limit_for_lists(tmp_path: Path) -> None:
    # An input value '[' * 63 + ']' * 63 loads; '[' * 64 + ']' * 64 is rejected.
    ok = '{"id": "a", "input": ' + nested(63) + ', "expected": 1}'
    assert len(load_dataset(write(tmp_path, ok))) == 1
    bad = '{"id": "a", "input": ' + nested(64) + ', "expected": 1}'
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, bad))
    assert info.value.code == "dataset_invalid"
    assert info.value.line == 1


def test_depth_limit_for_objects_and_expected(tmp_path: Path) -> None:
    ok = '{"id": "a", "input": ' + nested_dict(63) + ', "expected": ' + nested(63) + "}"
    assert len(load_dataset(write(tmp_path, ok))) == 1
    bad_input = '{"id": "a", "input": ' + nested_dict(64) + ', "expected": 1}'
    bad_expected = '{"id": "a", "input": 1, "expected": ' + nested(64) + "}"
    for text in (bad_input, bad_expected):
        with pytest.raises(EvalError) as info:
            load_dataset(write(tmp_path, text))
        assert info.value.code == "dataset_invalid"


def test_recursion_error_maps_to_dataset_invalid(tmp_path: Path) -> None:
    text = '{"id": "a", "input": ' + nested(100_000) + ', "expected": 1}'
    with pytest.raises(EvalError) as info:
        load_dataset(write(tmp_path, text))
    assert info.value.code == "dataset_invalid"
    assert info.value.line == 1
