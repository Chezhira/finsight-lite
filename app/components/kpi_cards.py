from __future__ import annotations

import streamlit as st


def _inject_card_css() -> None:
    st.markdown(
        """
        <style>
        .finsight-kpi-card {
            border: 1px solid rgba(49, 51, 63, 0.16);
            border-radius: 8px;
            padding: 0.8rem 0.85rem;
            background: #ffffff;
            min-height: 92px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.25rem;
        }
        .finsight-kpi-label {
            color: rgba(49, 51, 63, 0.72);
            font-size: 0.78rem;
            font-weight: 600;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        .finsight-kpi-value {
            color: #111827;
            font-size: 1.35rem;
            font-weight: 700;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _card(label: str, value: str) -> None:
    _inject_card_css()
    st.markdown(
        f"""
        <div class="finsight-kpi-card">
            <div class="finsight-kpi-label">{label}</div>
            <div class="finsight-kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compact_kes(value: float | int | None) -> str:
    value = 0 if value is None else float(value)
    sign = "-" if value < 0 else ""
    value_abs = abs(value)

    if value_abs >= 1_000_000_000:
        compact = f"{value_abs / 1_000_000_000:.1f}B"
    elif value_abs >= 1_000_000:
        compact = f"{value_abs / 1_000_000:.1f}M"
    elif value_abs >= 1_000:
        compact = f"{value_abs / 1_000:.1f}K"
    else:
        compact = f"{value_abs:,.0f}"

    compact = compact.replace(".0B", "B").replace(".0M", "M").replace(".0K", "K")
    return f"KES {sign}{compact}"


def money_metric(label: str, value: float | int | None) -> None:
    _card(label, compact_kes(value))


def percent_metric(label: str, value: float | None) -> None:
    if value is None:
        _card(label, "n/a")
    else:
        _card(label, f"{value:.1%}")


def status_metric(label: str, value: str) -> None:
    _card(label, value)
