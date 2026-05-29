from __future__ import annotations

import pandas as pd
import streamlit as st


def finance_table(df: pd.DataFrame) -> None:
    st.dataframe(df, use_container_width=True, hide_index=True)
