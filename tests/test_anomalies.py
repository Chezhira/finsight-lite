from __future__ import annotations

from finsight.anomalies import ANOMALY_COLUMNS


def test_anomaly_columns_are_stable():
    assert "anomaly_id" in ANOMALY_COLUMNS
    assert "recommended_follow_up" in ANOMALY_COLUMNS
