from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "src"))

from app.components.charts import bar_chart, line_chart
from app.components.kpi_cards import money_metric, percent_metric, status_metric

from finsight.config import DB_PATH

st.set_page_config(page_title="FinSight Lite", layout="wide")

KES_FORMAT = "KES %.0f"


@st.cache_data(show_spinner=False)
def read_table(table_name: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(f"select * from {table_name}").df()


st.title("FinSight Lite")
st.caption(
    "AI finance intelligence dashboard for validated finance models and CFO-style reporting."
)

if not DB_PATH.exists():
    st.warning(
        "DuckDB finance model not found. Run `make all` or `python -m finsight.load_duckdb` followed by `dbt run` first."
    )
    st.stop()

kpi = read_table("mart_kpi_summary")
dq = read_table("dq_summary")

if kpi.empty:
    st.warning("KPI mart is empty. Run the dbt models before launching the dashboard.")
    st.stop()

periods = sorted(kpi["period"].dropna().unique())
entities = ["Group"] + sorted(kpi["entity"].dropna().unique())

left, right = st.columns([1, 1])
selected_period = left.selectbox("Period", periods, index=len(periods) - 1)
selected_entity = right.selectbox("Entity", entities)

filtered = kpi[kpi["period"] == selected_period]
if selected_entity != "Group":
    filtered = filtered[filtered["entity"] == selected_entity]

totals = filtered[
    [
        "revenue",
        "cogs",
        "gross_profit",
        "opex",
        "operating_profit_proxy",
        "closing_cash_balance",
        "open_invoice_amount",
        "open_bill_amount",
        "anomaly_count",
        "dq_exception_count",
    ]
].sum(numeric_only=True)
gross_margin = totals["gross_profit"] / totals["revenue"] if totals["revenue"] else None

cards = st.columns(5)
with cards[0]:
    money_metric("Revenue", totals["revenue"])
with cards[1]:
    money_metric("Gross Profit", totals["gross_profit"])
with cards[2]:
    percent_metric("Gross Margin", gross_margin)
with cards[3]:
    money_metric("Operating Profit Proxy", totals["operating_profit_proxy"])
with cards[4]:
    money_metric("Closing Cash", totals["closing_cash_balance"])

cards = st.columns(5)
with cards[0]:
    money_metric("COGS", totals["cogs"])
with cards[1]:
    money_metric("Opex", totals["opex"])
with cards[2]:
    money_metric("Open Invoices", totals["open_invoice_amount"])
with cards[3]:
    money_metric("Open Bills", totals["open_bill_amount"])
with cards[4]:
    dq_status = (
        "Fail"
        if (dq["validation_status"] == "Fail").any()
        else ("Warnings" if (dq["validation_status"] == "Pass with warnings").any() else "Pass")
    )
    status_metric("Data Quality", dq_status)

trend = kpi if selected_entity == "Group" else kpi[kpi["entity"] == selected_entity]
trend_grouped = trend.groupby(["period", "entity"], as_index=False)[
    ["revenue", "opex", "operating_profit_proxy", "closing_cash_balance"]
].sum()

st.divider()
col1, col2 = st.columns(2)
with col1:
    line_chart(trend_grouped, "period", "revenue", "entity", "Revenue by Month")
with col2:
    line_chart(trend_grouped, "period", "opex", "entity", "Operating Expenses by Month")

col1, col2 = st.columns(2)
with col1:
    line_chart(
        trend_grouped,
        "period",
        "operating_profit_proxy",
        "entity",
        "Operating Profit Proxy by Month",
    )
with col2:
    line_chart(
        trend_grouped, "period", "closing_cash_balance", "entity", "Closing Cash Balance by Month"
    )

entity_revenue = (
    kpi[kpi["period"] == selected_period].groupby("entity", as_index=False)["revenue"].sum()
)
bar_chart(entity_revenue, "entity", "revenue", "entity", "Revenue by Entity")

st.subheader("Monthly Finance Model")
st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True,
    column_config={
        "revenue": st.column_config.NumberColumn("Revenue", format=KES_FORMAT),
        "cogs": st.column_config.NumberColumn("COGS", format=KES_FORMAT),
        "gross_profit": st.column_config.NumberColumn("Gross Profit", format=KES_FORMAT),
        "opex": st.column_config.NumberColumn("Opex", format=KES_FORMAT),
        "operating_profit_proxy": st.column_config.NumberColumn(
            "Operating Profit Proxy", format=KES_FORMAT
        ),
        "closing_cash_balance": st.column_config.NumberColumn("Closing Cash", format=KES_FORMAT),
        "open_invoice_amount": st.column_config.NumberColumn("Open Invoices", format=KES_FORMAT),
        "open_bill_amount": st.column_config.NumberColumn("Open Bills", format=KES_FORMAT),
    },
)
