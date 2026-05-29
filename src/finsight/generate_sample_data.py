"""
FinSight — Synthetic Sample Data Generator
==========================================
Generates realistic multi-entity, multi-currency finance data for demo purposes.

Fictional company: Savanna Group Holdings
  - SHL  : Savanna Honey Ltd          (honey processing & export)
  - AQL  : Aqua Lakes Ltd             (fish farming & processing)
  - GCL  : GreenCarbon Ltd            (carbon credits & agroforestry)

Currency: KES (primary), USD (secondary)
Period  : 24 months — Jan 2024 to Dec 2025
Anomalies: planted intentionally for demo purposes
"""

import os
import random
from datetime import date

import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

OUT = os.path.join(os.path.dirname(__file__), "sample")

# ── REFERENCE DATA ────────────────────────────────────────────────────────────

ENTITIES = ["SHL", "AQL", "GCL"]

ENTITY_NAMES = {
    "SHL": "Savanna Honey Ltd",
    "AQL": "Aqua Lakes Ltd",
    "GCL": "GreenCarbon Ltd",
}

CURRENCIES = ["KES", "USD"]

FX_RATES = {  # KES per 1 USD (approximate 2024-2025 range)
    2024: 133.0,
    2025: 129.0,
}

CHART_OF_ACCOUNTS = [
    # ASSETS
    ("11000001", "Cash & Bank — KES", "Asset", "Cash"),
    ("11000002", "Cash & Bank — USD", "Asset", "Cash"),
    ("12100001", "Trade Receivables — Domestic", "Asset", "Receivables"),
    ("12100002", "Trade Receivables — Export", "Asset", "Receivables"),
    ("12300001", "Suspense / Clearing", "Asset", "Suspense"),
    ("12500001", "PPE — Cost", "Asset", "Fixed Assets"),
    ("12600001", "PPE — Accumulated Depreciation", "Asset", "Fixed Assets"),
    ("13100001", "Inventory — Raw Materials", "Asset", "Inventory"),
    ("13100002", "Inventory — Finished Goods", "Asset", "Inventory"),
    ("13200001", "Employee Loans & Advances", "Asset", "Other Current"),
    ("13400001", "Intercompany — Receivable", "Asset", "Intercompany"),
    # LIABILITIES
    ("21000001", "Trade Payables — Domestic", "Liability", "Payables"),
    ("21000002", "Trade Payables — Import", "Liability", "Payables"),
    ("22000001", "VAT Control", "Liability", "Tax"),
    ("22000002", "PAYE Payable", "Liability", "Tax"),
    ("23000001", "Bank Loan — Long Term", "Liability", "Debt"),
    ("31200001", "Intercompany — Payable", "Liability", "Intercompany"),
    # EQUITY
    ("40000001", "Share Capital", "Equity", "Equity"),
    ("40000002", "Retained Earnings", "Equity", "Equity"),
    # REVENUE
    ("50000001", "Revenue — Domestic Sales", "Revenue", "Revenue"),
    ("50000002", "Revenue — Export Sales", "Revenue", "Revenue"),
    ("50000003", "Revenue — Carbon Credits", "Revenue", "Revenue"),
    ("50000004", "Other Income", "Revenue", "Other Income"),
    # COGS
    ("60000001", "COGS — Raw Materials", "COGS", "COGS"),
    ("60000002", "COGS — Processing Labour", "COGS", "COGS"),
    ("60000003", "COGS — Packaging", "COGS", "COGS"),
    # OPERATING EXPENSES
    ("70000001", "Salaries & Wages", "Expense", "Payroll"),
    ("70000002", "Rent & Utilities", "Expense", "Facilities"),
    ("70000003", "Logistics & Transport", "Expense", "Logistics"),
    ("70000004", "Repairs & Maintenance", "Expense", "Maintenance"),
    ("70000005", "Marketing & Promotions", "Expense", "Marketing"),
    ("70000006", "Professional Fees", "Expense", "Admin"),
    ("70000007", "Bank Charges & FX", "Expense", "Finance"),
    ("70000008", "Depreciation", "Expense", "Depreciation"),
    ("70000009", "Insurance", "Expense", "Admin"),
    ("70000010", "Sundry Expenses", "Expense", "Admin"),
]

COA_DF = pd.DataFrame(
    CHART_OF_ACCOUNTS, columns=["account_code", "account_name", "account_type", "category"]
)

# ── SEASONAL REVENUE PROFILES (monthly multipliers, index 0=Jan) ──────────────

SEASONALITY = {
    "SHL": [
        0.6,
        0.5,
        0.7,
        0.9,
        1.1,
        1.3,
        1.4,
        1.3,
        1.1,
        0.9,
        0.8,
        1.3,
    ],  # honey peaks mid-year + Dec
    "AQL": [1.1, 1.0, 1.2, 1.3, 1.1, 0.9, 0.8, 0.9, 1.1, 1.2, 1.1, 1.0],  # fish steady, peaks Q1/Q2
    "GCL": [0.4, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.4, 1.2, 1.0, 0.8, 0.8],  # carbon peaks mid-year
}

BASE_REVENUE_MONTHLY = {  # KES '000
    "SHL": 12_500,
    "AQL": 8_200,
    "GCL": 4_800,
}

BASE_COGS_RATIO = {
    "SHL": 0.58,
    "AQL": 0.65,
    "GCL": 0.30,
}

BASE_OPEX_MONTHLY = {  # KES '000
    "SHL": 3_800,
    "AQL": 2_900,
    "GCL": 1_600,
}

VENDORS = {
    "SHL": [
        "Apex Packaging Co",
        "TransRoute Logistics",
        "Beekeeper Co-op Central",
        "SunPower Utilities",
        "Nairobi Legal Partners",
        "ClearBank Ltd",
    ],
    "AQL": [
        "AquaFeed Suppliers",
        "ColdChain Express",
        "LakeView Processing",
        "EastAfrica Power",
        "Meridian Accountants",
        "Harbour Finance",
    ],
    "GCL": [
        "GreenSeed Nurseries",
        "SurveyTech Africa",
        "EcoMap Consultants",
        "Solar Connect Ltd",
        "Frontier Legal",
        "Unity Bank",
    ],
}

CUSTOMERS = {
    "SHL": [
        "EuroHoney GmbH",
        "NatureMart UK",
        "Savanna Domestic Wholesale",
        "Gulf Foods LLC",
        "Organic Direct Ltd",
    ],
    "AQL": [
        "FreshFish Nairobi",
        "Hotel Chain East Africa",
        "Export Buyers Ltd",
        "Retail Net KE",
        "AquaPro Processors",
    ],
    "GCL": [
        "ClimateBridge AG",
        "CarbonMarket Partners",
        "Green Invest Fund",
        "ESG Holdings Ltd",
        "Voluntary Carbon Exchange",
    ],
}


def date_range_monthly(start_year=2024, months=24):
    dates = []
    y, m = start_year, 1
    for _ in range(months):
        dates.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return dates


def random_business_day(year, month):
    """Return a random business day within the given month."""
    from calendar import monthrange

    _, last = monthrange(year, month)
    days = [d for d in range(1, last + 1) if date(year, month, d).weekday() < 5]
    return random.choice(days)


def jitter(base, pct=0.12):
    return base * (1 + np.random.uniform(-pct, pct))


# ── GENERATORS ────────────────────────────────────────────────────────────────


def generate_gl(months=24):
    rows = []
    ref_counter = [1000]

    def ref():
        ref_counter[0] += 1
        return f"JNL/{ref_counter[0]:05d}"

    period_list = date_range_monthly(2024, months)

    for year, month in period_list:
        season_idx = month - 1

        for entity in ENTITIES:
            rev_base = BASE_REVENUE_MONTHLY[entity] * SEASONALITY[entity][season_idx]
            cogs_base = rev_base * BASE_COGS_RATIO[entity]
            opex_base = BASE_OPEX_MONTHLY[entity]

            # ── Revenue lines ──────────────────────────────────────────────
            rev_dom = jitter(rev_base * 0.6) * 1000
            rev_exp = jitter(rev_base * 0.4) * 1000
            rev_acc = "50000003" if entity == "GCL" else "50000002"

            rows.append(
                {
                    "reference": ref(),
                    "date": date(year, month, random_business_day(year, month)).isoformat(),
                    "entity": entity,
                    "account_code": "50000001",
                    "account_name": "Revenue — Domestic Sales",
                    "category": "Revenue",
                    "description": f"Domestic sales — {CUSTOMERS[entity][0]}",
                    "debit": 0,
                    "credit": round(rev_dom, 2),
                    "currency": "KES",
                    "amount_kes": round(rev_dom, 2),
                }
            )
            rows.append(
                {
                    "reference": ref(),
                    "date": date(year, month, random_business_day(year, month)).isoformat(),
                    "entity": entity,
                    "account_code": rev_acc,
                    "account_name": (
                        "Revenue — Export Sales" if entity != "GCL" else "Revenue — Carbon Credits"
                    ),
                    "category": "Revenue",
                    "description": f"Export/carbon revenue — {CUSTOMERS[entity][2]}",
                    "debit": 0,
                    "credit": round(rev_exp, 2),
                    "currency": "KES",
                    "amount_kes": round(rev_exp, 2),
                }
            )

            # ── COGS ───────────────────────────────────────────────────────
            for acc, acc_name, share in [
                ("60000001", "COGS — Raw Materials", 0.60),
                ("60000002", "COGS — Processing Labour", 0.25),
                ("60000003", "COGS — Packaging", 0.15),
            ]:
                amt = jitter(cogs_base * share) * 1000
                rows.append(
                    {
                        "reference": ref(),
                        "date": date(year, month, random_business_day(year, month)).isoformat(),
                        "entity": entity,
                        "account_code": acc,
                        "account_name": acc_name,
                        "category": "COGS",
                        "description": f"{acc_name} — {month:02d}/{year}",
                        "debit": round(amt, 2),
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": round(amt, 2),
                    }
                )

            # ── Operating Expenses ─────────────────────────────────────────
            opex_split = {
                "70000001": ("Salaries & Wages", 0.38, "Payroll"),
                "70000002": ("Rent & Utilities", 0.12, "Facilities"),
                "70000003": ("Logistics & Transport", 0.18, "Logistics"),
                "70000004": ("Repairs & Maintenance", 0.08, "Maintenance"),
                "70000006": ("Professional Fees", 0.07, "Admin"),
                "70000007": ("Bank Charges & FX", 0.04, "Finance"),
                "70000008": ("Depreciation", 0.08, "Depreciation"),
                "70000009": ("Insurance", 0.05, "Admin"),
            }
            for acc, (acc_name, share, cat) in opex_split.items():
                amt = jitter(opex_base * share) * 1000
                vendor = random.choice(VENDORS[entity])
                rows.append(
                    {
                        "reference": ref(),
                        "date": date(year, month, random_business_day(year, month)).isoformat(),
                        "entity": entity,
                        "account_code": acc,
                        "account_name": acc_name,
                        "category": cat,
                        "description": f"{acc_name} — {vendor}",
                        "debit": round(amt, 2),
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": round(amt, 2),
                    }
                )

            # ── Intercompany ───────────────────────────────────────────────
            if entity == "SHL" and month % 2 == 0:
                ic_amt = jitter(500_000)
                rows.append(
                    {
                        "reference": ref(),
                        "date": date(year, month, random_business_day(year, month)).isoformat(),
                        "entity": "SHL",
                        "account_code": "13400001",
                        "account_name": "Intercompany — Receivable",
                        "category": "Intercompany",
                        "description": "Intercompany loan advance — AQL",
                        "debit": round(ic_amt, 2),
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": round(ic_amt, 2),
                    }
                )
                rows.append(
                    {
                        "reference": ref(),
                        "date": date(year, month, random_business_day(year, month)).isoformat(),
                        "entity": "AQL",
                        "account_code": "31200001",
                        "account_name": "Intercompany — Payable",
                        "category": "Intercompany",
                        "description": "Intercompany loan received — SHL",
                        "debit": 0,
                        "credit": round(ic_amt, 2),
                        "currency": "KES",
                        "amount_kes": round(ic_amt, 2),
                    }
                )

    df = pd.DataFrame(rows)

    # ══ PLANT ANOMALIES ═══════════════════════════════════════════════════════

    # 1. Exact duplicate entry
    dup = df[df["account_code"] == "70000003"].iloc[0].copy()
    dup["reference"] = "JNL/DUPE01"
    dup["description"] = dup["description"] + " [duplicate]"
    df = pd.concat([df, pd.DataFrame([dup])], ignore_index=True)

    # 2. Round-number large expense (suspicious)
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    {
                        "reference": "JNL/ROUND01",
                        "date": "2024-07-15",
                        "entity": "SHL",
                        "account_code": "70000010",
                        "account_name": "Sundry Expenses",
                        "category": "Admin",
                        "description": "Miscellaneous operational cost — unspecified",
                        "debit": 5_000_000.00,
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": 5_000_000.00,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    # 3. Suspense account — old uncleared (aged >90 days)
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    {
                        "reference": "JNL/SUSP01",
                        "date": "2024-01-08",
                        "entity": "GCL",
                        "account_code": "12300001",
                        "account_name": "Suspense / Clearing",
                        "category": "Suspense",
                        "description": "Unallocated receipt — TXN-GCL-00441",
                        "debit": 780_000.00,
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": 780_000.00,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    # 4. Reversal pair — accrual then reversal
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    {
                        "reference": "JNL/ACC01",
                        "date": "2025-03-31",
                        "entity": "AQL",
                        "account_code": "50000001",
                        "account_name": "Revenue — Domestic Sales",
                        "category": "Revenue",
                        "description": "Accrual — March revenue recognition",
                        "debit": 0,
                        "credit": 1_200_000.00,
                        "currency": "KES",
                        "amount_kes": 1_200_000.00,
                    },
                    {
                        "reference": "JNL/REV01",
                        "date": "2025-04-01",
                        "entity": "AQL",
                        "account_code": "50000001",
                        "account_name": "Revenue — Domestic Sales",
                        "category": "Revenue",
                        "description": "Reversal — March revenue accrual",
                        "debit": 1_200_000.00,
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": 1_200_000.00,
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    # 5. Spike expense — logistics 3× normal in one month
    df = pd.concat(
        [
            df,
            pd.DataFrame(
                [
                    {
                        "reference": "JNL/SPIKE01",
                        "date": "2025-09-12",
                        "entity": "AQL",
                        "account_code": "70000003",
                        "account_name": "Logistics & Transport",
                        "category": "Logistics",
                        "description": "Emergency cold-chain transport — Lake Victoria",
                        "debit": 4_800_000.00,
                        "credit": 0,
                        "currency": "KES",
                        "amount_kes": 4_800_000.00,
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["entity", "date"]).reset_index(drop=True)
    return df


def generate_budget(months=24):
    rows = []
    period_list = date_range_monthly(2024, months)
    for year, month in period_list:
        season_idx = month - 1
        for entity in ENTITIES:
            rev = BASE_REVENUE_MONTHLY[entity] * SEASONALITY[entity][season_idx] * 1000
            cogs = rev * BASE_COGS_RATIO[entity]
            opex = BASE_OPEX_MONTHLY[entity] * 1000
            rows.append(
                {
                    "year": year,
                    "month": month,
                    "period": f"{year}-{month:02d}",
                    "entity": entity,
                    "budget_revenue": round(rev, 0),
                    "budget_cogs": round(cogs, 0),
                    "budget_opex": round(opex, 0),
                    "budget_ebitda": round(rev - cogs - opex, 0),
                }
            )
    return pd.DataFrame(rows)


def generate_cash(months=24):
    rows = []
    period_list = date_range_monthly(2024, months)
    opening = {"SHL": 8_500_000, "AQL": 5_200_000, "GCL": 2_100_000}

    for year, month in period_list:
        season_idx = month - 1
        for entity in ENTITIES:
            bal = opening[entity]
            inflow = (
                jitter(BASE_REVENUE_MONTHLY[entity] * SEASONALITY[entity][season_idx] * 0.85) * 1000
            )
            outflow = (
                jitter(
                    (
                        BASE_COGS_RATIO[entity] * BASE_REVENUE_MONTHLY[entity]
                        + BASE_OPEX_MONTHLY[entity]
                    )
                    * SEASONALITY[entity][season_idx]
                    * 0.90
                )
                * 1000
            )
            closing = bal + inflow - outflow
            rows.append(
                {
                    "period": f"{year}-{month:02d}",
                    "entity": entity,
                    "opening_balance": round(bal, 2),
                    "inflows": round(inflow, 2),
                    "outflows": round(outflow, 2),
                    "closing_balance": round(closing, 2),
                    "currency": "KES",
                }
            )
            opening[entity] = closing

    # Plant cash anomaly: GCL large outflow Sept 2025
    df = pd.DataFrame(rows)
    idx = df[(df["entity"] == "GCL") & (df["period"] == "2025-09")].index
    if len(idx):
        df.loc[idx, "outflows"] += 3_000_000
        df.loc[idx, "closing_balance"] -= 3_000_000

    # Keep AQL cash realistic: one planted negative month, then recovery.
    aql_targets = {
        "2024-11": -768_177.86,
        "2024-12": 950_000.00,
        "2025-01": 1_300_000.00,
        "2025-02": 1_800_000.00,
        "2025-03": 2_200_000.00,
        "2025-04": 2_000_000.00,
        "2025-05": 2_400_000.00,
        "2025-06": 2_800_000.00,
        "2025-07": 2_500_000.00,
        "2025-08": 3_000_000.00,
        "2025-09": 3_300_000.00,
        "2025-10": 3_100_000.00,
        "2025-11": 3_600_000.00,
        "2025-12": 4_100_000.00,
    }
    prior_close = None
    for period, target_close in aql_targets.items():
        idx = df[(df["entity"] == "AQL") & (df["period"] == period)].index
        if not len(idx):
            continue
        row_idx = idx[0]
        if prior_close is not None:
            df.loc[row_idx, "opening_balance"] = prior_close
        opening_balance = df.loc[row_idx, "opening_balance"]
        inflow = df.loc[row_idx, "inflows"]
        df.loc[row_idx, "closing_balance"] = round(target_close, 2)
        df.loc[row_idx, "outflows"] = round(opening_balance + inflow - target_close, 2)
        prior_close = target_close
    return df


def generate_sales(months=24):
    rows = []
    period_list = date_range_monthly(2024, months)
    inv_counter = [5000]

    def inv_ref(entity):
        inv_counter[0] += 1
        return f"INV/{entity}/{inv_counter[0]:05d}"

    for year, month in period_list:
        season_idx = month - 1
        for entity in ENTITIES:
            rev_base = BASE_REVENUE_MONTHLY[entity] * SEASONALITY[entity][season_idx] * 1000
            n_invoices = random.randint(3, 7)
            for _ in range(n_invoices):
                customer = random.choice(CUSTOMERS[entity])
                is_usd = random.random() < 0.35
                amt_kes = jitter(rev_base / n_invoices)
                fx = FX_RATES[year]
                rows.append(
                    {
                        "invoice_ref": inv_ref(entity),
                        "invoice_date": date(
                            year, month, random_business_day(year, month)
                        ).isoformat(),
                        "entity": entity,
                        "customer": customer,
                        "revenue_category": (
                            "Carbon Credits"
                            if entity == "GCL"
                            else ("Export" if is_usd else "Domestic")
                        ),
                        "amount_kes": round(amt_kes, 2),
                        "amount_usd": round(amt_kes / fx, 2) if is_usd else 0,
                        "currency": "USD" if is_usd else "KES",
                        "status": random.choice(["Paid", "Paid", "Paid", "Outstanding", "Partial"]),
                    }
                )
    return pd.DataFrame(rows)


def generate_expenses(months=24):
    rows = []
    period_list = date_range_monthly(2024, months)
    bill_counter = [8000]

    def bill_ref(entity):
        bill_counter[0] += 1
        return f"BILL/{entity}/{bill_counter[0]:05d}"

    expense_map = {
        "70000001": ("Salaries & Wages", "Payroll"),
        "70000002": ("Rent & Utilities", "Facilities"),
        "70000003": ("Logistics & Transport", "Logistics"),
        "70000004": ("Repairs & Maintenance", "Maintenance"),
        "70000006": ("Professional Fees", "Admin"),
        "70000009": ("Insurance", "Admin"),
        "70000010": ("Sundry Expenses", "Admin"),
    }

    for year, month in period_list:
        for entity in ENTITIES:
            opex = BASE_OPEX_MONTHLY[entity] * 1000
            for acc, (acc_name, cat) in expense_map.items():
                share = {
                    "70000001": 0.38,
                    "70000002": 0.12,
                    "70000003": 0.18,
                    "70000004": 0.08,
                    "70000006": 0.07,
                    "70000009": 0.05,
                    "70000010": 0.04,
                }[acc]
                amt = jitter(opex * share)
                vendor = random.choice(VENDORS[entity])
                rows.append(
                    {
                        "bill_ref": bill_ref(entity),
                        "bill_date": date(
                            year, month, random_business_day(year, month)
                        ).isoformat(),
                        "entity": entity,
                        "vendor": vendor,
                        "expense_category": cat,
                        "account_code": acc,
                        "account_name": acc_name,
                        "amount_kes": round(amt, 2),
                        "currency": "KES",
                        "status": random.choice(["Paid", "Paid", "Outstanding"]),
                    }
                )
    return pd.DataFrame(rows)


# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)

    print("Generating chart of accounts...")
    COA_DF.to_csv(f"{OUT}/chart_of_accounts.csv", index=False)

    print("Generating GL transactions (24 months, 3 entities)...")
    gl = generate_gl(24)
    gl.to_csv(f"{OUT}/gl_transactions.csv", index=False)
    print(f"  → {len(gl):,} rows")

    print("Generating budget...")
    budget = generate_budget(24)
    budget.to_csv(f"{OUT}/budget.csv", index=False)
    print(f"  → {len(budget):,} rows")

    print("Generating cash movements...")
    cash = generate_cash(24)
    cash.to_csv(f"{OUT}/cash_movements.csv", index=False)
    print(f"  → {len(cash):,} rows")

    print("Generating sales invoices...")
    sales = generate_sales(24)
    sales.to_csv(f"{OUT}/sales_invoices.csv", index=False)
    print(f"  → {len(sales):,} rows")

    print("Generating expense bills...")
    expenses = generate_expenses(24)
    expenses.to_csv(f"{OUT}/expense_bills.csv", index=False)
    print(f"  → {len(expenses):,} rows")

    print("\nDone. Files written to:", OUT)
    print("\nEntities:    Savanna Honey Ltd (SHL) | Aqua Lakes Ltd (AQL) | GreenCarbon Ltd (GCL)")
    print("Currency:    KES primary, USD secondary")
    print("Period:      Jan 2024 – Dec 2025 (24 months)")
    print("Anomalies:   duplicate entry, round-number spike, aged suspense,")
    print("             reversal pair, logistics cost spike")
