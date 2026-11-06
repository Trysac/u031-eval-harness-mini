"""Tests for the opt-in pytest plugin, run through pytester."""

from __future__ import annotations

import re

import pytest

PLUGIN = "eval_harness_mini.pytest_plugin"

INNER = """
import json

from eval_harness_mini.scorers import exact_match


def test_gate(golden_eval, tmp_path):
    path = tmp_path / "golden.jsonl"
    rows = [{"id": "c%02d" % i, "input": i, "expected": 1} for i in range(30)]
    path.write_text("".join(json.dumps(row) + chr(10) for row in rows))
    golden_eval(lambda x: @OUT@, path, {"exact": exact_match}, {"exact": @THR@})
"""


def run_inner(pytester: pytest.Pytester, output: str, threshold: str) -> pytest.RunResult:
    source = INNER.replace("@OUT@", output).replace("@THR@", threshold)
    pytester.makepyfile(test_gate=source)
    return pytester.runpytest_inprocess("-p", PLUGIN)


def test_fixture_fails_listing_at_most_20_ids(pytester: pytest.Pytester) -> None:
    result = run_inner(pytester, "1 if x >= 25 else 0", "1.0")
    result.assert_outcomes(failed=1)
    out = result.stdout.str()
    assert "exact mean=0.1667 threshold=1.0000 FAIL" in out
    assert "... and 5 more" in out
    ids = set(re.findall(r"\bc\d\d\b", out))
    assert len(ids) == 20
    assert "c19" in ids
    assert "c20" not in ids


def test_fixture_passes_when_thresholds_are_met(pytester: pytest.Pytester) -> None:
    result = run_inner(pytester, "1", "1.0")
    result.assert_outcomes(passed=1)


def test_fixture_passes_with_lower_threshold(pytester: pytest.Pytester) -> None:
    result = run_inner(pytester, "1 if x >= 25 else 0", "0.1")
    result.assert_outcomes(passed=1)


def test_fixture_rejects_invalid_thresholds(pytester: pytest.Pytester) -> None:
    result = run_inner(pytester, "1", "1.5")
    result.assert_outcomes(failed=1)
    assert "threshold_invalid" in result.stdout.str()
