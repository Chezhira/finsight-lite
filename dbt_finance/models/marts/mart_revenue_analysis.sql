select
    period,
    entity,
    customer,
    revenue_category,
    currency,
    status,
    amount_kes,
    amount_usd
from {{ ref('stg_sales_invoices') }}
