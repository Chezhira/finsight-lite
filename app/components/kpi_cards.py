from __future__ import annotations

import streamlit as st


def money_metric(label: str, value: float | int | None) -> None:
    value = 0 if value is None else value
    st.metric(label, f"KES {value:,.0f}")


def percent_metric(label: str, value: float | None) -> None:
    if value is None:
        st.metric(label, "n/a")
    else:
        st.metric(label, f"{value:.1%}")
