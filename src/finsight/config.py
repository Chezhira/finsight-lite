from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = ROOT_DIR / "outputs"
DQ_DIR = OUTPUTS_DIR / "dq"
BOARD_SUMMARY_DIR = OUTPUTS_DIR / "board_summary"
DB_PATH = PROCESSED_DIR / "finsight.duckdb"

SAMPLE_FILES = {
    "gl_transactions": "gl_transactions.csv",
    "sales_invoices": "sales_invoices.csv",
    "expense_bills": "expense_bills.csv",
    "cash_movements": "cash_movements.csv",
    "budget": "budget.csv",
    "chart_of_accounts": "chart_of_accounts.csv",
}

KNOWN_ENTITIES = {"SHL", "AQL", "GCL"}
ENTITY_NAMES = {
    "SHL": "Savanna Honey Ltd",
    "AQL": "Aqua Lakes Ltd",
    "GCL": "GreenCarbon Ltd",
}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value in (None, ""):
        return default
    return float(value)
