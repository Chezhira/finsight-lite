from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.config import DB_PATH

st.set_page_config(page_title="Cash Movement", layout="wide")
st.title("Cash Movement")

if not DB_PATH.exists():
    st.warning("DuckDB finance model not found. Run `make all` before opening this page.")
    st.stop()

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    cash = con.execute("select * from mart_cash_movement").df()

if cash.empty:
    st.info("Cash movement mart is empty. Run `make all` to rebuild the finance models.")
    st.stop()

st.plotly_chart(
    px.line(
        cash,
        x="period",
        y="closing_balance",
        color="entity",
        markers=True,
        title="Closing Cash Balance",
        labels={"closing_balance": "Closing Balance (KES)"},
    ),
    use_container_width=True,
)
st.plotly_chart(
    px.bar(
        cash,
        x="period",
        y=["inflows", "outflows"],
        color="entity",
        barmode="group",
        title="Cash Inflows and Outflows",
        labels={"value": "Amount (KES)"},
    ),
    use_container_width=True,
)
st.dataframe(
    cash,
    use_container_width=True,
    hide_index=True,
    column_config={
        "opening_balance": st.column_config.NumberColumn("Opening Balance", format="KES %.0f"),
        "inflows": st.column_config.NumberColumn("Inflows", format="KES %.0f"),
        "outflows": st.column_config.NumberColumn("Outflows", format="KES %.0f"),
        "net_cash_movement": st.column_config.NumberColumn("Net Cash Movement", format="KES %.0f"),
        "closing_balance": st.column_config.NumberColumn("Closing Balance", format="KES %.0f"),
        "cash_recon_difference": st.column_config.NumberColumn(
            "Cash Recon Difference", format="KES %.0f"
        ),
    },
)
