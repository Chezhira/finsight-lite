from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.config import DB_PATH

st.set_page_config(page_title="Data Quality", layout="wide")
st.title("Data Quality")

if not DB_PATH.exists():
    st.warning("DuckDB finance model not found. Run `make all` before opening this page.")
    st.stop()

with duckdb.connect(str(DB_PATH), read_only=True) as con:
    summary = con.execute("select * from dq_summary").df()
    exceptions = con.execute("select * from dq_exceptions").df()

if summary.empty:
    st.info("Data quality summary is empty. Run `make all` to rebuild validation outputs.")
    st.stop()

st.dataframe(summary, use_container_width=True, hide_index=True)
st.subheader("Exceptions")
if exceptions.empty:
    st.success("No data quality exceptions were found.")
else:
    st.dataframe(exceptions, use_container_width=True, hide_index=True)
