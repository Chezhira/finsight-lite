from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.config import OUTPUTS_DIR

st.set_page_config(page_title="Anomalies", layout="wide")
st.title("Anomalies")

path = OUTPUTS_DIR / "anomalies.csv"
anomalies = pd.read_csv(path) if path.exists() else pd.DataFrame()

if anomalies.empty:
    st.info("No anomaly file has been generated yet, or no anomalies were found.")
else:
    severity_counts = anomalies["severity"].value_counts()
    cols = st.columns(3)
    cols[0].metric("High", int(severity_counts.get("High", 0)))
    cols[1].metric("Medium", int(severity_counts.get("Medium", 0)))
    cols[2].metric("Low", int(severity_counts.get("Low", 0)))
    st.dataframe(
        anomalies,
        use_container_width=True,
        hide_index=True,
        column_config={
            "current_value": st.column_config.NumberColumn("Current Value", format="KES %.0f"),
            "comparison_value": st.column_config.NumberColumn(
                "Comparison Value", format="KES %.0f"
            ),
            "variance_amount": st.column_config.NumberColumn("Variance Amount", format="KES %.0f"),
            "variance_percent": st.column_config.NumberColumn("Variance %", format="%.1f%%"),
        },
    )
