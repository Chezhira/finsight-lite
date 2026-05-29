from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR / "src"))
from finsight.commentary import generate_commentary
from finsight.config import BOARD_SUMMARY_DIR, DB_PATH

st.set_page_config(page_title="CFO Commentary", layout="wide")
st.title("CFO Commentary")

if not DB_PATH.exists():
    st.warning("DuckDB finance model not found. Run `make all` before opening this page.")
    st.stop()

if st.button("Regenerate commentary"):
    generate_commentary()

md_path = BOARD_SUMMARY_DIR / "monthly_cfo_commentary.md"
commentary = (
    md_path.read_text(encoding="utf-8")
    if md_path.exists()
    else "Run `make commentary` to generate the monthly commentary."
)
st.markdown(commentary)
st.download_button("Download Markdown", commentary, file_name="monthly_cfo_commentary.md")
st.download_button("Download Text", commentary, file_name="monthly_cfo_commentary.txt")
