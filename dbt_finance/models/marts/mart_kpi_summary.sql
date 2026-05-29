with open_invoices as (
    select period, entity, sum(case when is_open then amount_kes else 0 end) as open_invoice_amount
    from {{ ref('stg_sales_invoices') }}
    group by 1, 2
),
open_bills as (
    select period, entity, sum(case when is_open then amount_kes else 0 end) as open_bill_amount
    from {{ ref('stg_expense_bills') }}
    group by 1, 2
),
dq as (
    select count(*) as dq_exception_count from dq_exceptions
)
select
    pnl.period,
    pnl.entity,
    pnl.revenue,
    pnl.cogs,
    pnl.gross_profit,
    pnl.gross_margin_percent,
    pnl.opex,
    pnl.operating_profit_proxy,
    b.budget_revenue,
    b.budget_cogs,
    b.budget_opex,
    b.budget_operating_profit_proxy,
    pnl.revenue - b.budget_revenue as revenue_variance,
    pnl.opex - b.budget_opex as opex_variance,
    pnl.operating_profit_proxy - b.budget_operating_profit_proxy as operating_profit_variance,
    cash.closing_balance as closing_cash_balance,
    coalesce(inv.open_invoice_amount, 0) as open_invoice_amount,
    coalesce(bills.open_bill_amount, 0) as open_bill_amount,
    0 as anomaly_count,
    dq.dq_exception_count
from {{ ref('mart_monthly_pnl') }} pnl
left join {{ ref('stg_budget') }} b on pnl.period = b.period and pnl.entity = b.entity
left join {{ ref('mart_cash_movement') }} cash on pnl.period = cash.period and pnl.entity = cash.entity
left join open_invoices inv on pnl.period = inv.period and pnl.entity = inv.entity
left join open_bills bills on pnl.period = bills.period and pnl.entity = bills.entity
cross join dq
