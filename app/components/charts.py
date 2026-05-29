from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def line_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str) -> None:
    if df.empty:
        st.info(f"No data available for {title}.")
        return
    fig = px.line(df, x=x, y=y, color=color, markers=True, title=title)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(df: pd.DataFrame, x: str, y: str, color: str | None, title: str) -> None:
    if df.empty:
        st.info(f"No data available for {title}.")
        return
    fig = px.bar(df, x=x, y=y, color=color, title=title)
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    st.plotly_chart(fig, use_container_width=True)
