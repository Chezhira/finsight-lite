from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.config import DB_PATH

st.set_page_config(page_title="Sales and Receivables", layout="wide")
st.title("Sales and Receivables")

if not DB_PATH.exists():
    st.warning("DuckDB finance model not found. Run `make all` before opening this page.")
    st.stop()

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    revenue = con.execute("select * from mart_revenue_analysis").df()
    status = con.execute("select * from mart_invoice_status").df()

if revenue.empty:
    st.info("Revenue mart is empty. Run `make all` to rebuild the finance models.")
    st.stop()

st.plotly_chart(
    px.bar(
        revenue.groupby(["period", "entity"], as_index=False)["amount_kes"].sum(),
        x="period",
        y="amount_kes",
        color="entity",
        title="Sales by Entity",
        labels={"amount_kes": "Amount (KES)"},
    ),
    use_container_width=True,
)
st.plotly_chart(
    px.bar(
        revenue.groupby("customer", as_index=False)["amount_kes"].sum().nlargest(15, "amount_kes"),
        x="customer",
        y="amount_kes",
        title="Top Customers",
        labels={"amount_kes": "Amount (KES)"},
    ),
    use_container_width=True,
)
if not status.empty:
    st.plotly_chart(
        px.bar(
            status,
            x="status",
            y="invoice_amount_kes",
            color="entity",
            title="Invoice Status",
            labels={"invoice_amount_kes": "Invoice Amount (KES)"},
        ),
        use_container_width=True,
    )
st.dataframe(
    revenue,
    use_container_width=True,
    hide_index=True,
    column_config={
        "amount_kes": st.column_config.NumberColumn("Amount (KES)", format="KES %.0f"),
        "amount_usd": st.column_config.NumberColumn("Amount (USD)", format="USD %.0f"),
    },
)
