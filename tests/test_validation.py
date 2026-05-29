from __future__ import annotations

from finsight.validate import EXCEPTION_COLUMNS, validate_sample_data


def test_validation_outputs_expected_columns():
    result = validate_sample_data()
    assert list(result.exceptions.columns) == EXCEPTION_COLUMNS
    assert "validation_status" in result.summary.columns
    assert set(result.summary["source_file"]).issuperset({"gl_transactions.csv", "budget.csv"})
