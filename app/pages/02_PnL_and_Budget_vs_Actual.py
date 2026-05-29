from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.config import DB_PATH

st.set_page_config(page_title="P&L and Budget vs Actual", layout="wide")
st.title("P&L and Budget vs Actual")

if not DB_PATH.exists():
    st.warning("DuckDB finance model not found. Run `make all` before opening this page.")
    st.stop()

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    pnl = con.execute("select * from mart_monthly_pnl").df()
    bva = con.execute("select * from mart_budget_vs_actual").df()

if pnl.empty or bva.empty:
    st.info(
        "P&L and budget vs actual marts are empty. Run `make all` to rebuild the finance models."
    )
    st.stop()

periods = sorted(bva["period"].unique())
period = st.selectbox("Period", periods, index=len(periods) - 1)
view = bva[bva["period"] == period]

fig = px.bar(
    view,
    x="category",
    y=["actual_amount", "budget_amount"],
    color="entity",
    barmode="group",
    title="Budget vs Actual",
    labels={"value": "Amount (KES)", "category": "Finance Category"},
)
st.plotly_chart(fig, use_container_width=True)
st.dataframe(
    view.sort_values(["variance_status", "variance_amount"]),
    use_container_width=True,
    hide_index=True,
    column_config={
        "actual_amount": st.column_config.NumberColumn("Actual Amount", format="KES %.0f"),
        "budget_amount": st.column_config.NumberColumn("Budget Amount", format="KES %.0f"),
        "variance_amount": st.column_config.NumberColumn("Variance Amount", format="KES %.0f"),
        "variance_percent": st.column_config.NumberColumn("Variance %", format="%.1f%%"),
    },
)
st.subheader("Monthly P&L")
st.dataframe(
    pnl,
    use_container_width=True,
    hide_index=True,
    column_config={
        "revenue": st.column_config.NumberColumn("Revenue", format="KES %.0f"),
        "cogs": st.column_config.NumberColumn("COGS", format="KES %.0f"),
        "gross_profit": st.column_config.NumberColumn("Gross Profit", format="KES %.0f"),
        "gross_margin_percent": st.column_config.NumberColumn("Gross Margin %", format="%.1f%%"),
        "opex": st.column_config.NumberColumn("Opex", format="KES %.0f"),
        "operating_profit_proxy": st.column_config.NumberColumn(
            "Operating Profit Proxy", format="KES %.0f"
        ),
    },
)
