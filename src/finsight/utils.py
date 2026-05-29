from __future__ import annotations


def format_kes(value: float | int | None) -> str:
    if value is None:
        return "KES 0"
    return f"KES {value:,.0f}"
