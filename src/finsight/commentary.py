from __future__ import annotations

import duckdb

from finsight.config import BOARD_SUMMARY_DIR, DB_PATH, ENTITY_NAMES


def _money(value: float) -> str:
    return f"KES {value:,.0f}"


def generate_commentary() -> str:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found: {DB_PATH}")

    with duckdb.connect(str(DB_PATH)) as con:
        kpi = con.execute("select * from mart_kpi_summary order by period, entity").df()
        dq = con.execute("select * from dq_summary").df()
        anomalies = (
            con.execute("select * from anomalies order by severity, period, entity").df()
            if "anomalies" in [r[0] for r in con.execute("show tables").fetchall()]
            else None
        )

    latest_period = kpi["period"].max()
    latest = kpi[kpi["period"] == latest_period]
    group = latest[
        [
            "revenue",
            "cogs",
            "gross_profit",
            "opex",
            "operating_profit_proxy",
            "closing_cash_balance",
            "open_invoice_amount",
            "open_bill_amount",
        ]
    ].sum()
    dq_counts = dq[["exception_count", "critical_count", "warning_count", "info_count"]].sum()
    dq_status = (
        "Fail"
        if (dq["validation_status"] == "Fail").any()
        else (
            "Pass with warnings"
            if (dq["validation_status"] == "Pass with warnings").any()
            else "Pass"
        )
    )
    with duckdb.connect(str(DB_PATH)) as con:
        dq_exceptions = con.execute("select * from dq_exceptions").df()

    if dq_exceptions.empty:
        top_exception_lines = ["- No exception types found."]
    else:
        top_exception_lines = [
            f"- {row['rule_name']}: {row['count']}"
            for _, row in (
                dq_exceptions.groupby("rule_name")
                .size()
                .reset_index(name="count")
                .sort_values(["count", "rule_name"], ascending=[False, True])
                .head(3)
            ).iterrows()
        ]

    lines = [
        f"# Monthly CFO Commentary - {latest_period}",
        "",
        "## Group Performance",
        f"Group revenue for {latest_period} was {_money(group['revenue'])}, with gross profit of {_money(group['gross_profit'])} and operating profit proxy of {_money(group['operating_profit_proxy'])}. Closing cash balance was {_money(group['closing_cash_balance'])}.",
        "",
        "## Entity Highlights",
    ]
    for _, row in latest.iterrows():
        lines.append(
            f"- {ENTITY_NAMES.get(row['entity'], row['entity'])}: revenue {_money(row['revenue'])}, operating profit proxy {_money(row['operating_profit_proxy'])}, closing cash {_money(row['closing_cash_balance'])}."
        )

    lines.extend(
        [
            "",
            "## Working Capital Exposure",
            f"Open invoice exposure was {_money(group['open_invoice_amount'])}. Open bill exposure was {_money(group['open_bill_amount'])}.",
            "",
            "## Data Quality",
            f"- Validation status: {dq_status}",
            f"- Total exceptions: {int(dq_counts['exception_count'])}",
            f"- Critical: {int(dq_counts['critical_count'])}",
            f"- Warnings: {int(dq_counts['warning_count'])}",
            f"- Info: {int(dq_counts['info_count'])}",
            "- Top exception types:",
            *top_exception_lines,
            "",
        ]
    )

    if anomalies is not None and not anomalies.empty:
        latest_anomalies = anomalies[anomalies["period"] == latest_period].head(5)
        lines.extend(["## Key Anomalies"])
        if latest_anomalies.empty:
            lines.append("- No anomaly records were generated for the latest reporting period.")
        else:
            for _, row in latest_anomalies.iterrows():
                lines.append(
                    f"- {row['entity']} {row['anomaly_type']}: {row['explanation']} {row['recommended_follow_up']}",
                )
        lines.append("")

    lines.extend(
        [
            "Commentary is based on validated finance marts and should be read with the listed data quality exceptions.",
            "",
            "## Recommended Follow-up Questions",
            "- Which customers or products explain the largest revenue movements?",
            "- Which vendor or account categories explain the largest Opex movements?",
            "- Are open invoices and bills concentrated in one entity or counterparty?",
        ]
    )

    commentary = "\n".join(lines) + "\n"
    BOARD_SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    (BOARD_SUMMARY_DIR / "monthly_cfo_commentary.md").write_text(commentary, encoding="utf-8")
    (BOARD_SUMMARY_DIR / "monthly_cfo_commentary.txt").write_text(commentary, encoding="utf-8")
    print("Commentary written to outputs/board_summary")
    return commentary


def main() -> None:
    generate_commentary()


if __name__ == "__main__":
    main()
