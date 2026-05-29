from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.config import DB_PATH

st.set_page_config(page_title="Expenses and Payables", layout="wide")
st.title("Expenses and Payables")

if not DB_PATH.exists():
    st.warning("DuckDB finance model not found. Run `make all` before opening this page.")
    st.stop()

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    expenses = con.execute("select * from mart_expense_analysis").df()
    vendors = con.execute("select * from mart_vendor_spend").df()

if expenses.empty:
    st.info("Expense mart is empty. Run `make all` to rebuild the finance models.")
    st.stop()

st.plotly_chart(
    px.bar(
        expenses.groupby(["period", "entity"], as_index=False)["amount_kes"].sum(),
        x="period",
        y="amount_kes",
        color="entity",
        title="Expenses by Entity",
        labels={"amount_kes": "Amount (KES)"},
    ),
    use_container_width=True,
)
if not vendors.empty:
    st.plotly_chart(
        px.bar(
            vendors.groupby("vendor", as_index=False)["amount_kes"]
            .sum()
            .nlargest(15, "amount_kes"),
            x="vendor",
            y="amount_kes",
            title="Top Vendors",
            labels={"amount_kes": "Amount (KES)"},
        ),
        use_container_width=True,
    )
st.plotly_chart(
    px.bar(
        expenses.groupby(["expense_category", "status"], as_index=False)["amount_kes"].sum(),
        x="expense_category",
        y="amount_kes",
        color="status",
        title="Spend by Category and Status",
        labels={"amount_kes": "Amount (KES)"},
    ),
    use_container_width=True,
)
st.dataframe(
    expenses,
    use_container_width=True,
    hide_index=True,
    column_config={"amount_kes": st.column_config.NumberColumn("Amount (KES)", format="KES %.0f")},
)
