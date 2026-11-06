"""Tests for the command line interface."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

from eval_harness_mini.__main__ import main

ROWS = [("a", "a", "a"), ("b", "b", "b"), ("c", "c", "c"), ("d", "d", "z")]


def write_dataset(path: Path, rows: list[tuple[str, Any, Any]]) -> Path:
    lines = [json.dumps({"id": i, "input": x, "expected": y}) for i, x, y in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def argv(dataset: Path, *scorers: str, target: str = "builtins:str") -> list[str]:
    return ["run", str(dataset), "--target", target, "--scorer", *scorers]


def run_cli(capsys: pytest.CaptureFixture[str], args: list[str]) -> tuple[int, str, str]:
    code = main(args)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


@pytest.fixture
def dataset(tmp_path: Path) -> Path:
    return write_dataset(tmp_path / "golden.jsonl", ROWS)


def test_threshold_met_exits_0(dataset: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _err = run_cli(capsys, argv(dataset, "exact=0.75"))
    assert code == 0
    assert "exact mean=0.7500 threshold=0.7500 PASS" in out


def test_threshold_missed_exits_1(dataset: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _err = run_cli(capsys, argv(dataset, "exact=0.7501"))
    assert code == 1
    assert "exact mean=0.7500 threshold=0.7501 FAIL" in out
    assert "failing cases:" in out
    assert "  d" in out.splitlines()


def test_json_format(dataset: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _err = run_cli(capsys, [*argv(dataset, "exact=0.5"), "--format", "json"])
    assert code == 0
    assert json.loads(out)["means"] == {"exact": 0.75}


def test_several_scorers_and_json_field(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rows = [("a", {"k": 1}, {"k": 1}), ("b", {"k": 2}, {"k": 1})]
    path = write_dataset(tmp_path / "fields.jsonl", rows)
    args = argv(path, "json_field:k=0.5", "exact=0.0", target="json:dumps")
    code, out, _err = run_cli(capsys, args)
    assert code == 0
    assert "json_field:k mean=0.5000 threshold=0.5000 PASS" in out
    assert "exact mean=0.0000 threshold=0.0000 PASS" in out


def test_contains_scorer(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_dataset(tmp_path / "contains.jsonl", [("a", "xay", "a")])
    code, out, _err = run_cli(capsys, argv(path, "contains=1.0"))
    assert code == 0
    assert "contains mean=1.0000 threshold=1.0000 PASS" in out


def test_target_errors_count_as_failures(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = write_dataset(tmp_path / "ints.jsonl", [("a", "1", 1), ("b", "zz", 1)])
    code, out, _err = run_cli(capsys, argv(path, "exact=0.9", target="builtins:int"))
    assert code == 1
    assert "exact mean=0.5000 threshold=0.9000 FAIL" in out
    assert "  b" in out.splitlines()


def test_report_is_byte_identical_for_reordered_dataset(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = write_dataset(tmp_path / "first.jsonl", ROWS)
    second = write_dataset(tmp_path / "second.jsonl", ROWS[::-1])
    report_a = tmp_path / "report-a.json"
    report_b = tmp_path / "report-b.json"
    for data, report in ((first, report_a), (second, report_b)):
        code, _out, _err = run_cli(capsys, [*argv(data, "exact=0.5"), "--report", str(report)])
        assert code == 0
    assert report_a.read_bytes() == report_b.read_bytes()
    expected = {
        "cases": [
            {"error": None, "id": name, "scores": {"exact": 0.0 if name == "d" else 1.0}}
            for name in "abcd"
        ],
        "errors": 0,
        "means": {"exact": 0.75},
    }
    text = json.dumps(expected, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    assert report_a.read_bytes() == text.encode("utf-8")


def test_report_keeps_non_ascii_characters(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = write_dataset(tmp_path / "unicode.jsonl", [("a", "\u00e9", 1)])
    report = tmp_path / "report.json"
    args = [*argv(path, "exact=0.0", target="builtins:int"), "--report", str(report)]
    code, _out, _err = run_cli(capsys, args)
    assert code == 0
    data = report.read_bytes()
    assert "\u00e9".encode() in data
    assert b"\\u00e9" not in data
    assert data.endswith(b"\n")


def test_missing_dataset_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _out, err = run_cli(capsys, argv(tmp_path / "missing.jsonl", "exact=0.5"))
    assert code == 2
    assert "dataset_invalid" in err


def test_invalid_dataset_line_is_reported(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id": "a", "input": 1, "expected": 1}\n{bad\n', encoding="utf-8")
    code, _out, err = run_cli(capsys, argv(path, "exact=0.5"))
    assert code == 2
    assert "line 2" in err


@pytest.mark.parametrize(
    "target",
    ["no_such_module_xyz:f", "builtins:no_such_attr", "nocolon", "builtins:__name__", ":f", "m:"],
)
def test_target_not_found_exits_2(
    dataset: Path, capsys: pytest.CaptureFixture[str], target: str
) -> None:
    code, _out, err = run_cli(capsys, argv(dataset, "exact=0.5", target=target))
    assert code == 2
    assert "target_not_found" in err


@pytest.mark.parametrize(
    "spec",
    ["exact", "=0.5", "exact=abc", "unknown=0.5", "json_field:=0.5"],
)
def test_bad_scorer_specs_exit_2(
    dataset: Path, capsys: pytest.CaptureFixture[str], spec: str
) -> None:
    code, _out, err = run_cli(capsys, argv(dataset, spec))
    assert code == 2
    assert err.startswith("error:")


def test_duplicate_scorer_exits_2(dataset: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, _out, err = run_cli(capsys, argv(dataset, "exact=0.5", "exact=0.6"))
    assert code == 2
    assert "more than once" in err


@pytest.mark.parametrize("spec", ["exact=1.5", "exact=nan", "exact=-0.1"])
def test_invalid_threshold_exits_2(
    dataset: Path, capsys: pytest.CaptureFixture[str], spec: str
) -> None:
    code, _out, err = run_cli(capsys, argv(dataset, spec))
    assert code == 2
    assert "threshold_invalid" in err


def test_unwritable_report_exits_2(
    dataset: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report = tmp_path / "missing-dir" / "report.json"
    code, _out, err = run_cli(capsys, [*argv(dataset, "exact=0.5"), "--report", str(report)])
    assert code == 2
    assert err.startswith("error:")


@pytest.mark.parametrize("args", [["run"], [], ["nope"], ["run", "x", "--target", "a:b"]])
def test_usage_errors_exit_2(capsys: pytest.CaptureFixture[str], args: list[str]) -> None:
    code, _out, _err = run_cli(capsys, args)
    assert code == 2


def test_help_exits_0(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _err = run_cli(capsys, ["--help"])
    assert code == 0
    assert "eval-mini" in out


def test_main_reads_sys_argv(
    dataset: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["eval-mini", *argv(dataset, "exact=0.5")])
    assert main() == 0
    assert "PASS" in capsys.readouterr().out


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_module_entry_point(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["eval-mini", "--help"])
    with pytest.raises(SystemExit) as info:
        runpy.run_module("eval_harness_mini.__main__", run_name="__main__")
    assert info.value.code == 0
    assert "eval-mini" in capsys.readouterr().out
