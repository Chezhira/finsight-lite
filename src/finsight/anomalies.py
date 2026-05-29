from __future__ import annotations

from datetime import datetime

import duckdb
import pandas as pd

from finsight.config import DB_PATH, OUTPUTS_DIR, env_float

ANOMALY_COLUMNS = [
    "anomaly_id",
    "period",
    "entity",
    "anomaly_type",
    "severity",
    "metric_or_account",
    "current_value",
    "comparison_value",
    "variance_amount",
    "variance_percent",
    "explanation",
    "recommended_follow_up",
]


def generate_anomalies() -> pd.DataFrame:
    revenue_drop_threshold = env_float("REVENUE_DROP_THRESHOLD", 0.15)
    expense_increase_threshold = env_float("EXPENSE_INCREASE_THRESHOLD", 0.25)
    cash_decrease_threshold = env_float("CASH_DECREASE_THRESHOLD", 0.20)
    large_transaction_threshold = env_float("ANOMALY_LARGE_TRANSACTION_THRESHOLD", 1_000_000)

    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found: {DB_PATH}")

    rows: list[dict] = []
    with duckdb.connect(str(DB_PATH)) as con:
        pnl = con.execute("select * from mart_monthly_pnl order by entity, period").df()
        cash = con.execute("select * from mart_cash_movement order by entity, period").df()
        duplicate_refs = con.execute(
            """
            select
                reference,
                min(date) as first_date,
                string_agg(distinct entity, ', ') as entities,
                count(*) as row_count,
                sum(cast(amount_kes as double)) as total_amount_kes
            from raw_gl_transactions
            group by reference
            having count(*) > 1
            """
        ).df()
        duplicate_transactions = con.execute(
            """
            select
                a.reference as reference_a,
                b.reference as reference_b,
                a.date as date_a,
                b.date as date_b,
                a.entity,
                a.account_code,
                a.account_name,
                a.currency,
                a.amount_kes as amount_kes,
                abs(date_diff('day', cast(a.date as date), cast(b.date as date))) as days_apart
            from raw_gl_transactions a
            join raw_gl_transactions b
              on a.entity = b.entity
             and cast(a.account_code as varchar) = cast(b.account_code as varchar)
             and abs(cast(a.amount_kes as double) - cast(b.amount_kes as double)) <= 1
             and a.currency = b.currency
             and a.reference <> b.reference
             and a.reference < b.reference
             and abs(date_diff('day', cast(a.date as date), cast(b.date as date))) <= 7
             and (
                (cast(a.debit as double) > 0 and cast(b.debit as double) > 0)
                or
                (cast(a.credit as double) > 0 and cast(b.credit as double) > 0)
             )
            order by a.date, a.reference
            """
        ).df()
        round_transactions = con.execute(
            """
            select reference, date, entity, account_code, account_name, amount_kes
            from raw_gl_transactions
            where cast(amount_kes as double) >= ?
              and cast(amount_kes as double) % 1000000 = 0
            order by date, reference
            """,
            [large_transaction_threshold],
        ).df()
        suspense_entries = con.execute(
            """
            with report_date as (
                select max(cast(date as date)) as max_date from raw_gl_transactions
            )
            select
                gl.reference,
                gl.date,
                gl.entity,
                gl.account_code,
                gl.account_name,
                gl.amount_kes,
                date_diff('day', cast(gl.date as date), report_date.max_date) as age_days
            from raw_gl_transactions gl
            cross join report_date
            where cast(gl.account_code as varchar) = '12300001'
              and date_diff('day', cast(gl.date as date), report_date.max_date) > 90
            order by gl.date, gl.reference
            """
        ).df()
        reversal_pairs = con.execute(
            """
            select
                a.reference as reference_a,
                b.reference as reference_b,
                a.date as date_a,
                b.date as date_b,
                a.entity,
                a.account_code,
                a.account_name,
                a.amount_kes as amount_kes
            from raw_gl_transactions a
            join raw_gl_transactions b
              on a.entity = b.entity
             and cast(a.account_code as varchar) = cast(b.account_code as varchar)
             and a.reference < b.reference
             and abs(cast(a.amount_kes as double) - cast(b.amount_kes as double)) <= 1
             and abs(date_diff('day', cast(a.date as date), cast(b.date as date))) <= 5
             and (
                (cast(a.debit as double) > 0 and cast(b.credit as double) > 0)
                or
                (cast(a.credit as double) > 0 and cast(b.debit as double) > 0)
             )
            order by a.date, a.reference
            """
        ).df()

    def add(
        period, entity, anomaly_type, severity, metric, current, comparison, explanation, follow_up
    ):
        variance = current - comparison if pd.notna(comparison) else None
        variance_percent = (
            variance / abs(comparison)
            if comparison not in (None, 0) and pd.notna(comparison)
            else None
        )
        rows.append(
            {
                "anomaly_id": f"ANOM-{len(rows) + 1:05d}",
                "period": period,
                "entity": entity,
                "anomaly_type": anomaly_type,
                "severity": severity,
                "metric_or_account": metric,
                "current_value": current,
                "comparison_value": comparison,
                "variance_amount": variance,
                "variance_percent": variance_percent,
                "explanation": explanation,
                "recommended_follow_up": follow_up,
            }
        )

    for _, row in pnl.iterrows():
        entity_pnl = pnl[pnl["entity"] == row["entity"]].reset_index(drop=True)
        pos = entity_pnl.index[entity_pnl["period"] == row["period"]]
        if len(pos) and pos[0] > 0:
            prior = entity_pnl.iloc[pos[0] - 1]
            if prior["revenue"] and row["revenue"] < prior["revenue"] * (
                1 - revenue_drop_threshold
            ):
                add(
                    row["period"],
                    row["entity"],
                    "Revenue drop",
                    "Medium",
                    "Revenue",
                    row["revenue"],
                    prior["revenue"],
                    "Revenue declined by more than the month-on-month threshold.",
                    "Review customer, volume, pricing, and invoice timing movements.",
                )
            if prior["opex"] and row["opex"] > prior["opex"] * (1 + expense_increase_threshold):
                add(
                    row["period"],
                    row["entity"],
                    "Opex increase",
                    "Medium",
                    "Opex",
                    row["opex"],
                    prior["opex"],
                    "Operating expenses increased by more than the month-on-month threshold.",
                    "Review vendor spend and one-off operating costs.",
                )

    for _, row in cash.iterrows():
        entity_cash = cash[cash["entity"] == row["entity"]].reset_index(drop=True)
        pos = entity_cash.index[entity_cash["period"] == row["period"]]
        if len(pos) and pos[0] > 0:
            prior = entity_cash.iloc[pos[0] - 1]
            if prior["closing_balance"] and row["closing_balance"] < prior["closing_balance"] * (
                1 - cash_decrease_threshold
            ):
                add(
                    row["period"],
                    row["entity"],
                    "Cash decrease",
                    "High",
                    "Closing cash balance",
                    row["closing_balance"],
                    prior["closing_balance"],
                    "Closing cash balance decreased materially month-on-month.",
                    "Review cash inflows, supplier payments, capex, and working capital timing.",
                )
        if abs(row.get("cash_recon_difference", 0)) > 1:
            add(
                row["period"],
                row["entity"],
                "Cash reconciliation difference",
                "High",
                "Cash recon difference",
                row["cash_recon_difference"],
                0,
                "Cash movement does not reconcile to the reported closing balance.",
                "Investigate the cash movement bridge before using this period for reporting.",
            )

    time_series_rows = _deduplicate_persistent_conditions(rows)
    rows = time_series_rows

    for _, row in duplicate_refs.iterrows():
        add(
            str(row["first_date"])[:7],
            row["entities"],
            "Duplicate reference number",
            "Critical",
            row["reference"],
            row["row_count"],
            1,
            f"GL reference {row['reference']} appears more than once.",
            "Review duplicate reference usage and confirm whether the source export contains a repeated transaction.",
        )

    for _, row in duplicate_transactions.iterrows():
        add(
            str(row["date_b"])[:7],
            row["entity"],
            "Potential duplicate transaction",
            "High",
            f"{row['reference_a']} / {row['reference_b']}",
            row["amount_kes"],
            row["days_apart"],
            "Two or more transactions share the same entity, account, amount, and currency within a 7-day window but carry different reference numbers. Review for duplicate posting.",
            "Inspect the source support and reverse one transaction if this is a duplicate posting.",
        )

    for _, row in round_transactions.iterrows():
        add(
            str(row["date"])[:7],
            row["entity"],
            "Round number large transaction",
            "Medium",
            row["reference"],
            row["amount_kes"],
            large_transaction_threshold,
            f"GL transaction {row['reference']} is a large round-number amount.",
            "Review approval support and coding for this round-number transaction.",
        )

    for _, row in suspense_entries.iterrows():
        add(
            str(row["date"])[:7],
            row["entity"],
            "Aged suspense entry",
            "High",
            row["reference"],
            row["amount_kes"],
            row["age_days"],
            f"Suspense account entry {row['reference']} is older than 90 days from the report date.",
            "Clear or reclassify the suspense balance before management reporting.",
        )

    for _, row in reversal_pairs.iterrows():
        add(
            str(row["date_a"])[:7],
            row["entity"],
            "Potential reversal pair",
            "Low",
            f"{row['reference_a']} / {row['reference_b']}",
            row["amount_kes"],
            row["amount_kes"],
            f"Transactions {row['reference_a']} and {row['reference_b']} appear to reverse on the same account within 5 days.",
            "Confirm whether this is an expected accrual reversal or requires explanation.",
        )

    anomalies = pd.DataFrame(rows, columns=ANOMALY_COLUMNS)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    anomalies.to_csv(OUTPUTS_DIR / "anomalies.csv", index=False)

    with duckdb.connect(str(DB_PATH)) as con:
        con.register("anomalies_df", anomalies)
        con.execute("create or replace table anomalies as select * from anomalies_df")

    print(
        f"Anomalies generated: {len(anomalies)} at {datetime.now().isoformat(timespec='seconds')}"
    )
    return anomalies


def _deduplicate_persistent_conditions(rows: list[dict]) -> list[dict]:
    if not rows:
        return rows

    deduped: list[dict] = []
    df = pd.DataFrame(rows)

    for _, group in df.sort_values(["entity", "anomaly_type", "period"]).groupby(
        ["entity", "anomaly_type"], dropna=False
    ):
        current_run: list[dict] = []

        for row in group.to_dict("records"):
            if not current_run:
                current_run = [row]
                continue

            previous_period = pd.Period(current_run[-1]["period"], freq="M")
            current_period = pd.Period(row["period"], freq="M")
            if current_period.ordinal - previous_period.ordinal == 1:
                current_run.append(row)
            else:
                deduped.extend(_compact_run(current_run))
                current_run = [row]

        deduped.extend(_compact_run(current_run))

    for idx, row in enumerate(deduped, start=1):
        row["anomaly_id"] = f"ANOM-{idx:05d}"
    return deduped


def _compact_run(run: list[dict]) -> list[dict]:
    if len(run) <= 2:
        return run

    severity_rank = {"Low": 1, "Medium": 2, "High": 3}
    max_severity = max(run, key=lambda row: severity_rank.get(row["severity"], 0))["severity"]
    first = run[0]
    last = run[-1]
    suppressed_count = len(run) - 2

    return [
        *run[:2],
        {
            "anomaly_id": "",
            "period": last["period"],
            "entity": last["entity"],
            "anomaly_type": "Persistent condition",
            "severity": max_severity,
            "metric_or_account": first["anomaly_type"],
            "current_value": last["current_value"],
            "comparison_value": first["current_value"],
            "variance_amount": last["current_value"] - first["current_value"],
            "variance_percent": (
                (last["current_value"] - first["current_value"]) / abs(first["current_value"])
                if first["current_value"] not in (None, 0) and pd.notna(first["current_value"])
                else None
            ),
            "explanation": (
                f"{first['anomaly_type']} persisted for {len(run)} consecutive periods; "
                f"{suppressed_count} repeat alerts were consolidated."
            ),
            "recommended_follow_up": "Review the underlying driver as an ongoing condition rather than isolated monthly exceptions.",
        },
    ]


def main() -> None:
    generate_anomalies()


if __name__ == "__main__":
    main()
