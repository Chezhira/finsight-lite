from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from finsight.config import DQ_DIR, KNOWN_ENTITIES, SAMPLE_DIR, SAMPLE_FILES


@dataclass
class ValidationResult:
    exceptions: pd.DataFrame
    summary: pd.DataFrame


EXCEPTION_COLUMNS = [
    "exception_id",
    "source_file",
    "severity",
    "rule_name",
    "row_identifier",
    "field_name",
    "issue_description",
    "suggested_action",
]

SUMMARY_COLUMNS = [
    "run_date",
    "source_file",
    "total_rows",
    "exception_count",
    "critical_count",
    "warning_count",
    "info_count",
    "validation_status",
]


def _read_csv(name: str, sample_dir: Path) -> pd.DataFrame:
    path = sample_dir / SAMPLE_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Missing required sample file: {path}")
    return pd.read_csv(path)


def _is_blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def _add(
    rows: list[dict],
    source_file: str,
    severity: str,
    rule_name: str,
    row_identifier: object,
    field_name: str,
    issue_description: str,
    suggested_action: str,
) -> None:
    rows.append(
        {
            "exception_id": f"DQ-{len(rows) + 1:05d}",
            "source_file": source_file,
            "severity": severity,
            "rule_name": rule_name,
            "row_identifier": str(row_identifier),
            "field_name": field_name,
            "issue_description": issue_description,
            "suggested_action": suggested_action,
        }
    )


def _flag_mask(
    rows: list[dict],
    df: pd.DataFrame,
    source_file: str,
    mask: pd.Series,
    severity: str,
    rule_name: str,
    id_col: str,
    field_name: str,
    issue_description: str,
    suggested_action: str,
) -> None:
    for idx, row in df.loc[mask.fillna(False)].iterrows():
        _add(
            rows,
            source_file,
            severity,
            rule_name,
            row.get(id_col, idx),
            field_name,
            issue_description,
            suggested_action,
        )


def _summary_for(source_file: str, total_rows: int, exceptions: pd.DataFrame) -> dict:
    source_exceptions = exceptions[exceptions["source_file"] == source_file]
    critical_count = int((source_exceptions["severity"] == "Critical").sum())
    warning_count = int((source_exceptions["severity"] == "Warning").sum())
    info_count = int((source_exceptions["severity"] == "Info").sum())
    if critical_count:
        status = "Fail"
    elif warning_count:
        status = "Pass with warnings"
    else:
        status = "Pass"
    return {
        "run_date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        "source_file": source_file,
        "total_rows": total_rows,
        "exception_count": int(len(source_exceptions)),
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "validation_status": status,
    }


def validate_sample_data(
    sample_dir: Path = SAMPLE_DIR, output_dir: Path = DQ_DIR
) -> ValidationResult:
    gl = _read_csv("gl_transactions", sample_dir)
    sales = _read_csv("sales_invoices", sample_dir)
    expenses = _read_csv("expense_bills", sample_dir)
    cash = _read_csv("cash_movements", sample_dir)
    budget = _read_csv("budget", sample_dir)
    coa = _read_csv("chart_of_accounts", sample_dir)

    rows: list[dict] = []
    account_codes = set(coa["account_code"].astype(str))

    gl["account_code_str"] = gl["account_code"].astype(str)
    gl_date = pd.to_datetime(gl["date"], errors="coerce")
    debit = pd.to_numeric(gl["debit"], errors="coerce").fillna(0)
    credit = pd.to_numeric(gl["credit"], errors="coerce").fillna(0)
    amount = pd.to_numeric(gl["amount_kes"], errors="coerce")
    gl_category = gl["category"].astype(str).str.lower()
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        ~gl["account_code_str"].isin(account_codes),
        "Critical",
        "gl_account_in_chart",
        "reference",
        "account_code",
        "GL account code is not present in the chart of accounts.",
        "Map the account or update chart_of_accounts.csv.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        gl_date.isna(),
        "Critical",
        "valid_gl_date",
        "reference",
        "date",
        "GL transaction date is missing or invalid.",
        "Correct the transaction date.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        _is_blank(gl["entity"]),
        "Critical",
        "gl_entity_required",
        "reference",
        "entity",
        "GL transaction has no entity.",
        "Populate the entity code.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        (debit == 0) & (credit == 0),
        "Critical",
        "gl_debit_or_credit_required",
        "reference",
        "debit/credit",
        "GL row has neither debit nor credit populated.",
        "Populate the transaction amount.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        (debit > 0) & (credit > 0),
        "Warning",
        "gl_both_debit_and_credit",
        "reference",
        "debit/credit",
        "GL row has both debit and credit populated.",
        "Review whether this should be split into separate lines.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        (amount - debit.where(debit > 0, credit)).abs() > 1,
        "Warning",
        "gl_amount_reconciliation",
        "reference",
        "amount_kes",
        "amount_kes does not reconcile to the populated debit or credit value.",
        "Review source export amount fields.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        _is_blank(gl["currency"]),
        "Critical",
        "gl_currency_required",
        "reference",
        "currency",
        "GL currency is missing.",
        "Populate currency.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        _is_blank(gl["category"]),
        "Warning",
        "gl_category_required",
        "reference",
        "category",
        "GL category is missing.",
        "Map account category from chart of accounts.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        gl_category.eq("revenue") & (debit > 0),
        "Warning",
        "revenue_debit_balance",
        "reference",
        "debit",
        "Revenue account appears with a debit balance.",
        "Review for reversal, refund, or coding issue.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        gl_category.isin(["cogs", "cost of sales", "opex", "operating expenses"]) & (credit > 0),
        "Warning",
        "expense_credit_balance",
        "reference",
        "credit",
        "Expense account appears with a credit balance.",
        "Review for reversal, accrual release, or coding issue.",
    )
    _flag_mask(
        rows,
        gl,
        "gl_transactions.csv",
        gl.duplicated(["reference", "date", "entity", "account_code", "amount_kes"], keep=False),
        "Info",
        "suspicious_duplicate_gl_reference",
        "reference",
        "reference",
        "Potential duplicate GL line detected.",
        "Confirm whether the duplicate is expected.",
    )

    sales_date = pd.to_datetime(sales["invoice_date"], errors="coerce")
    sales_amount = pd.to_numeric(sales["amount_kes"], errors="coerce")
    sales_usd = pd.to_numeric(sales["amount_usd"], errors="coerce").fillna(0)
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        _is_blank(sales["invoice_ref"]),
        "Critical",
        "invoice_ref_required",
        "invoice_ref",
        "invoice_ref",
        "Invoice reference is missing.",
        "Populate invoice reference.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        sales_date.isna(),
        "Critical",
        "invoice_date_required",
        "invoice_ref",
        "invoice_date",
        "Invoice date is missing or invalid.",
        "Correct invoice date.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        _is_blank(sales["entity"]),
        "Critical",
        "invoice_entity_required",
        "invoice_ref",
        "entity",
        "Invoice entity is missing.",
        "Populate entity.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        _is_blank(sales["customer"]),
        "Warning",
        "customer_required",
        "invoice_ref",
        "customer",
        "Customer is missing.",
        "Populate customer.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        sales_amount <= 0,
        "Critical",
        "positive_invoice_amount",
        "invoice_ref",
        "amount_kes",
        "Invoice amount is not positive.",
        "Correct invoice amount.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        _is_blank(sales["currency"]),
        "Critical",
        "invoice_currency_required",
        "invoice_ref",
        "currency",
        "Invoice currency is missing.",
        "Populate currency.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        ~sales["status"].isin(["Paid", "Partial", "Outstanding"]),
        "Warning",
        "valid_invoice_status",
        "invoice_ref",
        "status",
        "Invoice status is not recognised.",
        "Use Paid, Partial, or Outstanding.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        sales["currency"].eq("USD") & (sales_usd <= 0),
        "Warning",
        "usd_invoice_amount_usd_required",
        "invoice_ref",
        "amount_usd",
        "USD invoice has no USD amount.",
        "Populate amount_usd.",
    )
    _flag_mask(
        rows,
        sales,
        "sales_invoices.csv",
        sales["currency"].eq("KES") & (sales_usd > 0),
        "Info",
        "kes_invoice_usd_blank",
        "invoice_ref",
        "amount_usd",
        "KES invoice has a USD amount.",
        "Leave amount_usd blank or zero for KES invoices.",
    )

    expense_date = pd.to_datetime(expenses["bill_date"], errors="coerce")
    expense_amount = pd.to_numeric(expenses["amount_kes"], errors="coerce")
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        _is_blank(expenses["bill_ref"]),
        "Critical",
        "bill_ref_required",
        "bill_ref",
        "bill_ref",
        "Bill reference is missing.",
        "Populate bill reference.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        expense_date.isna(),
        "Critical",
        "bill_date_required",
        "bill_ref",
        "bill_date",
        "Bill date is missing or invalid.",
        "Correct bill date.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        _is_blank(expenses["entity"]),
        "Critical",
        "bill_entity_required",
        "bill_ref",
        "entity",
        "Bill entity is missing.",
        "Populate entity.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        _is_blank(expenses["vendor"]),
        "Warning",
        "vendor_required",
        "bill_ref",
        "vendor",
        "Vendor is missing.",
        "Populate vendor.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        ~expenses["account_code"].astype(str).isin(account_codes),
        "Critical",
        "expense_account_in_chart",
        "bill_ref",
        "account_code",
        "Expense account code is not present in the chart of accounts.",
        "Map the account or update chart_of_accounts.csv.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        expense_amount <= 0,
        "Critical",
        "positive_bill_amount",
        "bill_ref",
        "amount_kes",
        "Bill amount is not positive.",
        "Correct bill amount.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        _is_blank(expenses["currency"]),
        "Critical",
        "bill_currency_required",
        "bill_ref",
        "currency",
        "Bill currency is missing.",
        "Populate currency.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        ~expenses["status"].isin(["Paid", "Partial", "Outstanding"]),
        "Warning",
        "valid_bill_status",
        "bill_ref",
        "status",
        "Bill status is not recognised.",
        "Use Paid, Partial, or Outstanding.",
    )
    _flag_mask(
        rows,
        expenses,
        "expense_bills.csv",
        _is_blank(expenses["expense_category"]),
        "Warning",
        "expense_category_required",
        "bill_ref",
        "expense_category",
        "Expense category is missing.",
        "Populate expense category.",
    )

    cash_numeric = cash[["opening_balance", "inflows", "outflows", "closing_balance"]].apply(
        pd.to_numeric, errors="coerce"
    )
    cash_diff = (
        cash_numeric["opening_balance"]
        + cash_numeric["inflows"]
        - cash_numeric["outflows"]
        - cash_numeric["closing_balance"]
    )
    _flag_mask(
        rows,
        cash,
        "cash_movements.csv",
        cash.duplicated(["period", "entity"], keep=False),
        "Critical",
        "one_cash_row_per_period_entity",
        "period",
        "period/entity",
        "Duplicate cash movement period/entity row.",
        "Keep one cash movement row per entity and period.",
    )
    _flag_mask(
        rows,
        cash,
        "cash_movements.csv",
        cash_diff.abs() > 1,
        "Critical",
        "cash_reconciliation",
        "period",
        "closing_balance",
        "Cash movement does not reconcile to closing balance.",
        "Review opening balance, inflows, outflows, and closing balance.",
    )
    _flag_mask(
        rows,
        cash,
        "cash_movements.csv",
        _is_blank(cash["currency"]),
        "Critical",
        "cash_currency_required",
        "period",
        "currency",
        "Cash movement currency is missing.",
        "Populate currency.",
    )
    _flag_mask(
        rows,
        cash,
        "cash_movements.csv",
        cash_numeric["closing_balance"] < 0,
        "Warning",
        "negative_cash_balance",
        "period",
        "closing_balance",
        "Closing cash balance is negative.",
        "Confirm overdraft or correct cash data.",
    )
    cash_sorted = cash.assign(closing_balance_num=cash_numeric["closing_balance"]).sort_values(
        ["entity", "period"]
    )
    prior_cash = cash_sorted.groupby("entity")["closing_balance_num"].shift(1)
    cash_drop = (prior_cash > 0) & (
        (cash_sorted["closing_balance_num"] - prior_cash) / prior_cash < -0.2
    )
    _flag_mask(
        rows,
        cash_sorted,
        "cash_movements.csv",
        cash_drop,
        "Info",
        "large_cash_decrease",
        "period",
        "closing_balance",
        "Closing cash decreased by more than 20% month-on-month.",
        "Review cash drivers and large payments.",
    )

    budget_period = pd.to_datetime(budget["period"].astype(str) + "-01", errors="coerce")
    b = budget[["budget_revenue", "budget_cogs", "budget_opex", "budget_ebitda"]].apply(
        pd.to_numeric, errors="coerce"
    )
    budget_diff = b["budget_revenue"] - b["budget_cogs"] - b["budget_opex"] - b["budget_ebitda"]
    _flag_mask(
        rows,
        budget,
        "budget.csv",
        budget.duplicated(["period", "entity"], keep=False),
        "Critical",
        "one_budget_row_per_period_entity",
        "period",
        "period/entity",
        "Duplicate budget period/entity row.",
        "Keep one budget row per entity and period.",
    )
    for col in b.columns:
        _flag_mask(
            rows,
            budget,
            "budget.csv",
            b[col].isna(),
            "Critical",
            f"{col}_required",
            "period",
            col,
            f"{col} is missing.",
            "Populate budget field.",
        )
    _flag_mask(
        rows,
        budget,
        "budget.csv",
        budget_diff.abs() > 1,
        "Warning",
        "budget_ebitda_formula",
        "period",
        "budget_ebitda",
        "Budget EBITDA does not equal revenue minus COGS minus Opex.",
        "Review budget formula.",
    )
    _flag_mask(
        rows,
        budget,
        "budget.csv",
        budget_period.isna(),
        "Critical",
        "valid_budget_period",
        "period",
        "period",
        "Budget period format is invalid.",
        "Use YYYY-MM period format.",
    )
    _flag_mask(
        rows,
        budget,
        "budget.csv",
        ~budget["entity"].isin(KNOWN_ENTITIES),
        "Critical",
        "valid_budget_entity",
        "period",
        "entity",
        "Budget entity is not recognised.",
        "Use SHL, AQL, or GCL.",
    )

    exceptions = pd.DataFrame(rows, columns=EXCEPTION_COLUMNS)
    summary_rows = [
        _summary_for("gl_transactions.csv", len(gl), exceptions),
        _summary_for("sales_invoices.csv", len(sales), exceptions),
        _summary_for("expense_bills.csv", len(expenses), exceptions),
        _summary_for("cash_movements.csv", len(cash), exceptions),
        _summary_for("budget.csv", len(budget), exceptions),
        _summary_for("chart_of_accounts.csv", len(coa), exceptions),
    ]
    summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)

    output_dir.mkdir(parents=True, exist_ok=True)
    exceptions.to_csv(output_dir / "dq_exceptions.csv", index=False)
    summary.to_csv(output_dir / "dq_summary.csv", index=False)
    return ValidationResult(exceptions=exceptions, summary=summary)


def main() -> None:
    result = validate_sample_data()
    print(f"Validation complete: {len(result.exceptions)} exceptions written to outputs/dq")


if __name__ == "__main__":
    main()
