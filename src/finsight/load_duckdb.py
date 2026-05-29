from __future__ import annotations

import duckdb
import pandas as pd

from finsight.config import DB_PATH, DQ_DIR, PROCESSED_DIR, SAMPLE_DIR, SAMPLE_FILES
from finsight.validate import validate_sample_data

RAW_TABLES = {
    "gl_transactions": "raw_gl_transactions",
    "sales_invoices": "raw_sales_invoices",
    "expense_bills": "raw_expense_bills",
    "cash_movements": "raw_cash_movements",
    "budget": "raw_budget",
    "chart_of_accounts": "raw_chart_of_accounts",
}


def load_to_duckdb() -> None:
    validate_sample_data()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DB_PATH)) as con:
        for source_name, table_name in RAW_TABLES.items():
            csv_path = SAMPLE_DIR / SAMPLE_FILES[source_name]
            df = pd.read_csv(csv_path)
            con.register("source_df", df)
            con.execute(f"create or replace table {table_name} as select * from source_df")
            con.unregister("source_df")

        for csv_name, table_name in {
            "dq_exceptions.csv": "dq_exceptions",
            "dq_summary.csv": "dq_summary",
        }.items():
            df = pd.read_csv(DQ_DIR / csv_name)
            con.register("dq_df", df)
            con.execute(f"create or replace table {table_name} as select * from dq_df")
            con.unregister("dq_df")

    print("DuckDB loaded: data/processed/finsight.duckdb")


def main() -> None:
    load_to_duckdb()


if __name__ == "__main__":
    main()
